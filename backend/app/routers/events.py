import base64
import io
import os
import re
import secrets
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import qrcode
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ActivityPoint, Attendance, Club, Event, Registration, User, now
from ..schemas import CheckinIn, EventIn, EventOut
from ..security import current_user, ensure_club_manager, require_roles

router = APIRouter(tags=["events"])
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
MAX_POSTER = 2 * 1024 * 1024  # 2 MB
# Nhận diện ảnh bằng vài byte đầu file (không tin vào tên file hay content-type do client gửi)
IMAGE_SIGNS = {b"\xff\xd8\xff": ".jpg", b"\x89PNG\r\n\x1a\n": ".png"}
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


@router.post("/events/{event_id}/poster", response_model=EventOut)
def upload_poster(
    event_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_roles("manager", "admin")),
    db: Session = Depends(get_db),
):
    e = get_event(db, event_id)
    ensure_club_manager(db.get(Club, e.club_id), user)
    data = file.file.read(MAX_POSTER + 1)
    if len(data) > MAX_POSTER:
        raise HTTPException(413, "Ảnh poster tối đa 2 MB")
    ext = next((x for sign, x in IMAGE_SIGNS.items() if data.startswith(sign)), None)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        ext = ".webp"
    if not ext:
        raise HTTPException(415, "Chỉ nhận ảnh JPG, PNG hoặc WEBP")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = uuid4().hex + ext  # tên ngẫu nhiên: không ghi đè, không lộ tên file gốc
    (UPLOAD_DIR / name).write_bytes(data)
    remove_poster_file(e.poster_url)  # xóa ảnh cũ đã upload trước đó
    e.poster_url = os.getenv("ROOT_PATH", "") + "/uploads/" + name
    db.commit()
    return to_out(db, e)


def remove_poster_file(url: str | None) -> None:
    prefix = os.getenv("ROOT_PATH", "") + "/uploads/"
    if url and url.startswith(prefix):
        (UPLOAD_DIR / url.removeprefix(prefix)).unlink(missing_ok=True)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, user: User = Depends(require_roles("manager", "admin")), db: Session = Depends(get_db)):
    e = get_event(db, event_id)
    ensure_club_manager(db.get(Club, e.club_id), user)
    # đã có người điểm danh thì không xóa, để giữ nguyên điểm rèn luyện của sinh viên
    if db.scalar(select(func.count()).select_from(Attendance).where(Attendance.event_id == e.id)):
        raise HTTPException(409, "Sự kiện đã có sinh viên điểm danh, không thể xóa")
    db.execute(delete(Registration).where(Registration.event_id == e.id))
    remove_poster_file(e.poster_url)
    db.delete(e)
    db.commit()


@router.get("/uploads/{name}", include_in_schema=False)
def poster_file(name: str):
    # chỉ trả file đúng dạng tên do server sinh ra, chặn kiểu tấn công ../../etc/passwd
    if not re.fullmatch(r"[0-9a-f]{32}\.(png|jpg|webp)", name) or not (UPLOAD_DIR / name).is_file():
        raise HTTPException(404, "Không tìm thấy ảnh")
    return FileResponse(UPLOAD_DIR / name, headers={"Cache-Control": "public, max-age=86400"})


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
    club = ensure_club_manager(db.get(Club, e.club_id), user)
    # Lấy mọi sinh viên đã đăng ký, kèm thời điểm điểm danh (nếu có)
    rows = db.execute(
        select(User.full_name, User.email, Attendance.checked_at)
        .join(Registration, Registration.user_id == User.id)
        .outerjoin(Attendance, (Attendance.user_id == User.id) & (Attendance.event_id == e.id))
        .where(Registration.event_id == e.id)
        .order_by(User.full_name)
    ).all()
    present = sum(1 for r in rows if r.checked_at)

    wb = Workbook()
    ws = wb.active
    ws.title = "Điểm danh"
    blue, green, red = "1747A6", "0F8A4B", "C62A2A"
    thin = Side(style="thin", color="CDD5E2")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)

    ws.merge_cells("A1:F1")
    ws["A1"] = "DANH SÁCH ĐIỂM DANH SỰ KIỆN"
    ws["A1"].font = Font(size=15, bold=True, color=blue)
    ws["A1"].alignment = Alignment(horizontal="center")
    info = [
        ("Sự kiện", e.title), ("Câu lạc bộ", club.name), ("Địa điểm", e.location),
        ("Thời gian", f"{e.start_time:%H:%M} – {e.end_time:%H:%M}, ngày {e.start_time:%d/%m/%Y}"),
        ("Tổng kết", f"{present}/{len(rows)} sinh viên có mặt · {e.points} điểm rèn luyện/người"),
    ]
    for i, (k, v) in enumerate(info, start=3):
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=2)
        ws.cell(i, 1, k).font = Font(bold=True, color="5F6B80")
        ws.merge_cells(start_row=i, start_column=3, end_row=i, end_column=6)
        ws.cell(i, 3, v)

    head = 9
    for col, title in enumerate(["STT", "Họ và tên", "Email", "Trạng thái", "Thời gian điểm danh", "Điểm RL"], 1):
        c = ws.cell(head, col, title)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=blue)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = box
    for i, r in enumerate(rows, 1):
        ok = r.checked_at is not None
        values = [i, r.full_name, r.email, "Có mặt" if ok else "Vắng",
                  r.checked_at.strftime("%H:%M:%S %d/%m/%Y") if ok else "", e.points if ok else 0]
        for col, v in enumerate(values, 1):
            c = ws.cell(head + i, col, v)
            c.border = box
            if i % 2 == 0:
                c.fill = PatternFill("solid", fgColor="F3F5FA")
            if col in (1, 4, 5, 6):
                c.alignment = Alignment(horizontal="center")
        ws.cell(head + i, 4).font = Font(bold=True, color=green if ok else red)
    if not rows:
        ws.merge_cells(start_row=head + 1, start_column=1, end_row=head + 1, end_column=6)
        ws.cell(head + 1, 1, "Chưa có sinh viên đăng ký").alignment = Alignment(horizontal="center")
    for col, w in zip("ABCDEF", [6, 28, 32, 12, 22, 9]):
        ws.column_dimensions[col].width = w
    ws.row_dimensions[head].height = 22
    ws.freeze_panes = ws.cell(head + 1, 1)  # cố định dòng tiêu đề khi cuộn
    ws.page_setup.orientation = "landscape"  # in vừa 1 trang ngang
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="diem-danh-su-kien-{event_id}.xlsx"'},
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