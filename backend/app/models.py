from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def now() -> datetime:
    return datetime.now()  # giờ địa phương của container (TZ=Asia/Ho_Chi_Minh)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="student")  # student|manager|admin


class Club(Base):
    __tablename__ = "clubs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class Membership(Base):  # N:N users <-> clubs
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "club_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")


class Event(Base):  # 1:N clubs -> events
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(150))
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    capacity: Mapped[int]
    points: Mapped[int] = mapped_column(default=5)
    poster_url: Mapped[str | None] = mapped_column(String(300))
    checkin_code: Mapped[str | None] = mapped_column(String(20))
    code_expires: Mapped[datetime | None]


class Registration(Base):  # N:N users <-> events
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("user_id", "event_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("user_id", "event_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    checked_at: Mapped[datetime] = mapped_column(default=now)


class ActivityPoint(Base):
    __tablename__ = "activity_points"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    points: Mapped[int]