from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Club, Membership, User
from ..schemas import ClubIn, ClubOut, MembershipPatch
from ..security import current_user, ensure_club_manager, require_roles

router = APIRouter(tags=["clubs"])


@router.get("/clubs", response_model=list[ClubOut])
def list_clubs(
    q: str = "",
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    stmt = select(Club).where(Club.name.ilike(f"%{q}%")).order_by(Club.id)
    return db.scalars(stmt.offset((page - 1) * size).limit(size)).all()


@router.post("/clubs", status_code=201, response_model=ClubOut)
def create_club(
    data: ClubIn, user: User = Depends(require_roles("manager", "admin")), db: Session = Depends(get_db)
):
    if db.scalar(select(Club).where(Club.name == data.name)):
        raise HTTPException(409, "Tên CLB đã tồn tại")
    c = Club(**data.model_dump(), manager_id=user.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.post("/clubs/{club_id}/join", status_code=201)
def join(club_id: int, user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    if not db.get(Club, club_id):
        raise HTTPException(404, "Không tìm thấy câu lạc bộ")
    if db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.club_id == club_id)):
        raise HTTPException(409, "Bạn đã gửi yêu cầu hoặc đã là thành viên")
    m = Membership(user_id=user.id, club_id=club_id)
    db.add(m)
    db.commit()
    return {"id": m.id, "status": m.status}


@router.get("/clubs/{club_id}/members")
def members(club_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ensure_club_manager(db.get(Club, club_id), user)
    rows = db.execute(
        select(Membership.id, Membership.status, User.full_name, User.email)
        .join(User, User.id == Membership.user_id)
        .where(Membership.club_id == club_id)
    ).all()
    return [{"id": r.id, "status": r.status, "full_name": r.full_name, "email": r.email} for r in rows]


@router.patch("/memberships/{membership_id}")
def review(
    membership_id: int, data: MembershipPatch, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    m = db.get(Membership, membership_id)
    if not m:
        raise HTTPException(404, "Không tìm thấy yêu cầu")
    ensure_club_manager(db.get(Club, m.club_id), user)
    m.status = data.status
    db.commit()
    return {"id": m.id, "status": m.status}


@router.get("/me/memberships")
def my_memberships(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Membership).where(Membership.user_id == user.id)).all()
    return [{"club_id": m.club_id, "status": m.status} for m in rows]