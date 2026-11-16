from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ActivityPoint, Attendance, Club, Event, Registration, User
from ..security import require_roles

router = APIRouter(tags=["stats"])


def semester(d: datetime) -> str:
    """HK1: tháng 8 đến tháng 1 năm sau; HK2: tháng 2 đến tháng 6; Hè: tháng 7."""
    if d.month >= 8:
        return f"HK1 {d.year}-{d.year + 1}"
    if d.month == 1:
        return f"HK1 {d.year - 1}-{d.year}"
    if d.month <= 6:
        return f"HK2 {d.year - 1}-{d.year}"
    return f"Hè {d.year - 1}-{d.year}"


def count_by_event(db: Session, model):
    return select(model.event_id, func.count().label("n")).group_by(model.event_id).subquery()


@router.get("/stats/semesters")
def stats_by_semester(
    club_id: int | None = None,
    user: User = Depends(require_roles("manager", "admin")),
    db: Session = Depends(get_db),
):
    reg, att = count_by_event(db, Registration), count_by_event(db, Attendance)
    pts = select(ActivityPoint.event_id, func.sum(ActivityPoint.points).label("n")).group_by(ActivityPoint.event_id).subquery()
    stmt = (
        select(Event.start_time, func.coalesce(reg.c.n, 0), func.coalesce(att.c.n, 0), func.coalesce(pts.c.n, 0))
        .join(Club, Club.id == Event.club_id)
        .outerjoin(reg, reg.c.event_id == Event.id)
        .outerjoin(att, att.c.event_id == Event.id)
        .outerjoin(pts, pts.c.event_id == Event.id)
    )
    if user.role != "admin":  # ban chủ nhiệm chỉ xem CLB mình phụ trách
        stmt = stmt.where(Club.manager_id == user.id)
    if club_id:
        stmt = stmt.where(Event.club_id == club_id)

    out = defaultdict(lambda: {"events": 0, "registrations": 0, "attendances": 0, "points": 0, "start": None})
    for start, n_reg, n_att, n_pts in db.execute(stmt):
        s = out[semester(start)]
        s["events"] += 1
        s["registrations"] += n_reg
        s["attendances"] += n_att
        s["points"] += n_pts
        s["start"] = min(s["start"] or start, start)
    rows = sorted(out.items(), key=lambda kv: kv[1]["start"], reverse=True)
    return [
        {"semester": k, "events": v["events"], "registrations": v["registrations"], "attendances": v["attendances"],
         "attendance_rate": round(v["attendances"] / v["registrations"] * 100, 1) if v["registrations"] else 0,
         "points": v["points"]}
        for k, v in rows
    ]
