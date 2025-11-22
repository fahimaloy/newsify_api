from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from cj36.core.security import create_access_token, get_password_hash, verify_password
from cj36.dependencies import (
    get_current_user,
    get_db,
    RoleChecker
)
from cj36.models import User, UserCreate, UserRead, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserRead)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"])),
):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
        post_review_before_publish=user.post_review_before_publish,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=List[UserRead])
def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "maintainer"])),
):
    users = db.query(User).all()
    return users


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin", "maintainer"])),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"])),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = user_in.dict(exclude_unset=True)
    if "password" in user_data:
        user_data["hashed_password"] = get_password_hash(user_data["password"])
        del user_data["password"]
    for key, value in user_data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=UserRead)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"])),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
