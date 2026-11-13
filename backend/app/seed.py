from datetime import timedelta

from sqlalchemy import select

from .database import SessionLocal
from .models import Club, Event, User, now
from .security import hash_password


def seed():
    with SessionLocal() as db:
        if db.scalar(select(User).limit(1)):
            return
        admin = User(email="admin@demo.vn", full_name="Đoàn - Hội", role="admin", password_hash=hash_password("Admin@123"))
        mgr = User(email="manager@demo.vn", full_name="Chủ nhiệm CLB", role="manager", password_hash=hash_password("Manager@123"))
        sv = User(email="sv@demo.vn", full_name="Sinh viên Demo", password_hash=hash_password("Student@123"))
        db.add_all([admin, mgr, sv])
        db.flush()
        c1 = Club(name="CLB Lập trình", description="Cùng học và làm dự án mã nguồn mở", manager_id=mgr.id)
        c2 = Club(name="CLB Tiếng Anh", description="Giao lưu, luyện nói mỗi tuần", manager_id=mgr.id)
        db.add_all([c1, c2])
        db.flush()
        n = now()
        db.add_all([
            Event(club_id=c1.id, title="Workshop Git & GitHub", location="Phòng Lab 2", capacity=40,
                  start_time=n + timedelta(days=3), end_time=n + timedelta(days=3, hours=2)),
            Event(club_id=c2.id, title="English Speaking Night", location="Hội trường A", capacity=60, points=3,
                  start_time=n + timedelta(days=7), end_time=n + timedelta(days=7, hours=2)),
        ])
        db.commit()