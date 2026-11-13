from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import RegisterIn
from ..security import create_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(409, "Email đã được đăng ký")
    # Luôn tạo vai trò student: người dùng không thể tự nâng quyền
    u = User(email=data.email, full_name=data.full_name, password_hash=hash_password(data.password))
    db.add(u)
    db.commit()
    return {"id": u.id, "email": u.email}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == form.username))
    if not u or not verify_password(form.password, u.password_hash):
        raise HTTPException(401, "Sai email hoặc mật khẩu")
    return {"access_token": create_token(u), "token_type": "bearer"}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}