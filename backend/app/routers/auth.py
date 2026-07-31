from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.schemas import Credentials, TokenOut
from app.security import create_token, current_user, hash_password, verify_password
from app.services import unique_handle

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: Credentials, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status_code=409, detail="That email already has an account.")
    user = User(
        email=body.email,
        handle=unique_handle(db, body.email),
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user.id), email=user.email, handle=user.handle)


@router.post("/login", response_model=TokenOut)
def login(body: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    return TokenOut(access_token=create_token(user.id), email=user.email, handle=user.handle)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "handle": user.handle}
