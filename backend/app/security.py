import os
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Club, User

SECRET = os.environ["SECRET_KEY"]  # bắt buộc đặt trong .env
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_token(user: User) -> str:
    exp = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, SECRET, "HS256")


def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        uid = int(jwt.decode(token, SECRET, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "Người dùng không tồn tại")
    return user


def require_roles(*roles: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Không đủ quyền thực hiện thao tác này")
        return user

    return dep


def ensure_club_manager(club: Club | None, user: User) -> Club:
    if not club:
        raise HTTPException(404, "Không tìm thấy câu lạc bộ")
    if user.role != "admin" and club.manager_id != user.id:
        raise HTTPException(403, "Bạn không phải ban chủ nhiệm CLB này")
    return club