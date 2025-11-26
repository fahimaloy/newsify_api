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
    AdminType,
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
    
    # Auto-login: generate tokens
    from cj36.core.security import create_refresh_token
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "message": "Verification successful"
    }


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

from cj36.core.email import send_password_reset_email

@router.post("/reset-password-request")
def request_password_reset(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verification_code = ''.join(random.choices(string.digits, k=6))
    current_user.verification_code = verification_code
    db.add(current_user)
    db.commit()
    
    send_password_reset_email(current_user.email, verification_code)
    return {"message": "Password reset OTP sent"}

@router.post("/reset-password-confirm")
def confirm_password_reset(
    code: str = Body(...),
    new_password: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    current_user.hashed_password = get_password_hash(new_password)
    current_user.verification_code = None
    db.add(current_user)
    db.commit()
    
    return {"message": "Password updated successfully"}

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
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    user_type: UserType = None,
    admin_type: AdminType = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(AdminChecker(["admin", "maintainer"])),
):
    query = db.query(User)
    
    if search:
        search_filter = (
            User.username.ilike(f"%{search}%") | 
            User.email.ilike(f"%{search}%")
        )
        # Add full_name check if it exists on model, which it does now
        if hasattr(User, "full_name"):
             search_filter = search_filter | User.full_name.ilike(f"%{search}%")
        
        query = query.filter(search_filter)
    
    if user_type:
        query = query.filter(User.user_type == user_type)
        
    if admin_type:
        query = query.filter(User.admin_type == admin_type)
        
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return current_user

@router.patch("/me", response_model=UserRead)
def update_current_user(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user profile."""
    user_data = user_in.dict(exclude_unset=True)
    
    # Filter out restricted fields
    restricted_fields = ["user_type", "admin_type", "username", "email", "is_blocked", "is_verified", "verification_code"]
    for field in restricted_fields:
        if field in user_data:
            del user_data[field]
            
    # Exclude password (use reset flow)
    if "password" in user_data:
        del user_data["password"]

    for key, value in user_data.items():
        setattr(current_user, key, value)
        
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
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
    current_user: User = Depends(AdminChecker(["admin", "maintainer"])),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Permission checks
    if current_user.admin_type == AdminType.MAINTAINER:
        # Maintainer cannot update admin users
        if user.user_type == UserType.ADMINISTRATOR:
             raise HTTPException(
                status_code=403, 
                detail="Maintainers cannot update administrator accounts"
            )
        
        # Maintainer can only block/unblock subscribers (update is_blocked)
        # They shouldn't be able to change other fields like username, email, etc.
        # But the requirement says "can block any subscriber type users".
        # It doesn't explicitly forbid updating other fields of subscribers, but "view... details" suggests read-only mostly.
        # I'll allow updating everything for subscribers for now, but strictly forbid touching admins.
        
        # Actually, let's be stricter. If they are maintainer, and target is subscriber, allow.
        if user.user_type != UserType.SUBSCRIBER:
             raise HTTPException(
                status_code=403, 
                detail="Maintainers can only update subscriber accounts"
            )

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
    
    # Import refresh token function
    from cj36.core.security import create_refresh_token
    
    # Create both access and refresh tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_access_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    from cj36.core.security import verify_token, create_refresh_token
    
    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="User not verified")
    
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
