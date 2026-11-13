import base64
import io
import secrets
from datetime import timedelta

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ActivityPoint, Attendance, Club, Event, Registration, User, now
from ..schemas import CheckinIn, EventIn, EventOut
from ..security import current_user, ensure_club_manager, require_roles

router = APIRouter(tags=["events"])
FIELDS = ["id", "club_id", "title", "description", "location", "start_time", "end_time",
          "capacity", "points", "poster_url"]


def to_out(db: Session, e: Event) -> dict:
    n = db.scalar(select(func.count()).select_from(Registration).where(Registration.event_id == e.id))
    return {**{f: getattr(e, f) for f in FIELDS}, "registered_count": n}


def get_event(db: Session, event_id: int, lock: bool = False) -> Event:
    stmt = select(Event).where(Event.id == event_id)
    e = db.scalar(stmt.with_for_update() if lock else stmt)
    if not e:
        raise HTTPException(404, "Không tìm thấy sự kiện")
    return e


def find(db: Session, model, user_id: int, event_id: int):
    return db.scalar(select(model).where(model.user_id == user_id, model.event_id == event_id))


@router.get("/events", response_model=list[EventOut])
def list_events(
    q: str = "",
    club_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    stmt = select(Event).where(Event.title.ilike(f"%{q}%"))
    if club_id:
        stmt = stmt.where(Event.club_id == club_id)
    rows = db.scalars(stmt.order_by(Event.start_time).offset((page - 1) * size).limit(size)).all()
    return [to_out(db, e) for e in rows]


@router.post("/events", status_code=201, response_model=EventOut)
def create_event(
    data: EventIn, user: User = Depends(require_roles("manager", "admin")), db: Session = Depends(get_db)
):
    ensure_club_manager(db.get(Club, data.club_id), user)
    e = Event(**data.model_dump())
    db.add(e)
    db.commit()
    return to_out(db, e)


@router.post("/events/{event_id}/register", status_code=201)
def register(event_id: int, user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    e = get_event(db, event_id, lock=True)  # khoá hàng: tránh đăng ký vượt số lượng
    if e.end_time < now():
        raise HTTPException(400, "Sự kiện đã kết thúc")
    if find(db, Registration, user.id, e.id):
        raise HTTPException(409, "Bạn đã đăng ký sự kiện này")
    if to_out(db, e)["registered_count"] >= e.capacity:
        raise HTTPException(409, "Sự kiện đã đủ số lượng")
    db.add(Registration(user_id=user.id, event_id=e.id))
    db.commit()
    return {"message": "Đăng ký thành công"}


@router.delete("/events/{event_id}/register", status_code=204)
def cancel(event_id: int, user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    e = get_event(db, event_id)
    r = find(db, Registration, user.id, e.id)
    if not r:
        raise HTTPException(404, "Bạn chưa đăng ký sự kiện này")
    if e.start_time <= now():
        raise HTTPException(400, "Sự kiện đã bắt đầu, không thể hủy")
    db.delete(r)
    db.commit()


@router.get("/me/registrations")
def my_registrations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Registration.event_id).where(Registration.user_id == user.id)).all()


@router.post("/events/{event_id}/qr")
def make_qr(event_id: int, user: User = Depends(require_roles("manager", "admin")), db: Session = Depends(get_db)):
    e = get_event(db, event_id)
    ensure_club_manager(db.get(Club, e.club_id), user)
    e.checkin_code = secrets.token_urlsafe(6)
    e.code_expires = now() + timedelta(minutes=10)  # hết hạn sau 10 phút
    db.commit()
    buf = io.BytesIO()
    qrcode.make(e.checkin_code).save(buf, format="PNG")
    return {"code": e.checkin_code, "expires_at": e.code_expires,
            "qr_png_base64": base64.b64encode(buf.getvalue()).decode()}


@router.post("/events/{event_id}/checkin")
def checkin(event_id: int, data: CheckinIn, user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    e = get_event(db, event_id)
    if not find(db, Registration, user.id, e.id):
        raise HTTPException(403, "Bạn chưa đăng ký sự kiện này")
    t = now()
    if not (e.start_time <= t <= e.end_time):
        raise HTTPException(400, "Ngoài thời gian diễn ra sự kiện")
    if not e.checkin_code or e.code_expires < t or not secrets.compare_digest(data.code, e.checkin_code):
        raise HTTPException(400, "Mã điểm danh không đúng hoặc đã hết hạn")
    if find(db, Attendance, user.id, e.id):
        raise HTTPException(409, "Bạn đã điểm danh rồi")
    db.add(Attendance(user_id=user.id, event_id=e.id))
    db.add(ActivityPoint(user_id=user.id, event_id=e.id, points=e.points))
    db.commit()
    return {"message": "Điểm danh thành công", "points": e.points}


@router.get("/events/{event_id}/attendances/export")
def export(event_id: int, user: User = Depends(require_roles("manager", "admin")), db: Session = Depends(get_db)):
    e = get_event(db, event_id)
    ensure_club_manager(db.get(Club, e.club_id), user)
    rows = db.execute(
        select(User.full_name, User.email, Attendance.checked_at)
        .join(Attendance, Attendance.user_id == User.id)
        .where(Attendance.event_id == event_id)
    ).all()
    wb = Workbook()
    ws = wb.active
    ws.append(["Họ tên", "Email", "Thời gian điểm danh"])
    for r in rows:
        ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="diem-danh-{event_id}.xlsx"'},
    )


@router.get("/me/history")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Event.id, Event.title, Event.start_time, ActivityPoint.points)
        .join(ActivityPoint, ActivityPoint.event_id == Event.id)
        .where(ActivityPoint.user_id == user.id)
        .order_by(Event.start_time.desc())
    ).all()
    return {
        "total_points": sum(r.points for r in rows),
        "events": [{"event_id": r.id, "title": r.title, "start_time": r.start_time, "points": r.points} for r in rows],
    }