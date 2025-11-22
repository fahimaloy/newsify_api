import random
import string
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from cj36.core.security import create_access_token, get_password_hash, verify_password
from cj36.core.email import send_verification_email
from cj36.dependencies import (
    get_current_user,
    get_db,
    AdminChecker,
)
from cj36.models import (
    User,
    UserCreate,
    UserRead,
    UserUpdate,
    UserSignup,
    UserType,
)

router = APIRouter()

# ---------- Signup (subscriber) ----------
@router.post("/signup", response_model=UserRead)
def signup_user(
    user: UserSignup, db: Session = Depends(get_db)
):
    # Ensure username/email uniqueness
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    verification_code = ''.join(random.choices(string.digits, k=6))
    
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        phone=user.phone,
        newsletter_subscribed=user.newsletter_subscribed,
        user_type=UserType.SUBSCRIBER,
        is_verified=False,
        verification_code=verification_code
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    send_verification_email(db_user.email, verification_code)
    
    return db_user


@router.post("/verify")
def verify_email(
    email: str = Body(...),
    code: str = Body(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        return {"message": "User already verified"}
        
    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
        
    user.is_verified = True
    user.verification_code = None
    db.add(user)
    db.commit()
    
    # Auto-login: generate token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "message": "Verification successful"}


@router.post("/resend-verification")
def resend_verification(
    email: str = Body(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")
        
    verification_code = ''.join(random.choices(string.digits, k=6))
    user.verification_code = verification_code
    db.add(user)
    db.commit()
    
    send_verification_email(user.email, verification_code)
    return {"message": "Verification code sent"}

# ---------- Admin/User management (admin only) ----------
@router.post("/", response_model=UserRead)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AdminChecker(["admin"])),
):
    # Only admins can create other admins or maintainers; writers can be created by admins as well
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=getattr(user, "email", None),
        hashed_password=hashed_password,
        phone=getattr(user, "phone", None),
        user_type=getattr(user, "user_type", UserType.SUBSCRIBER),
        admin_type=getattr(user, "admin_type", None),
        post_review_before_publish=getattr(user, "post_review_before_publish", False),
        newsletter_subscribed=getattr(user, "newsletter_subscribed", False),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserRead])
def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(AdminChecker(["admin", "maintainer"])),
):
    users = db.query(User).all()
    return users

@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return current_user

@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AdminChecker(["admin", "maintainer"])),
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
    current_user: User = Depends(AdminChecker(["admin"])),
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
    current_user: User = Depends(AdminChecker(["admin"])),
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
        
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email verification required",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
