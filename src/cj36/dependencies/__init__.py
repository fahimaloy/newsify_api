from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, create_engine
from cj36.core.config import settings
from cj36.core.security import ALGORITHM, SECRET_KEY
from cj36.models import User, UserType, AdminType

engine = create_engine(settings.db_url)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/token", auto_error=False)


def get_db() -> Generator:
    with Session(engine) as session:
        yield session


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_optional_current_user(
    db: Session = Depends(get_db), token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user


class AdminChecker:
    """Check if user is an administrator with specific admin types."""
    def __init__(self, allowed_admin_types: List[str]):
        self.allowed_admin_types = allowed_admin_types

    def __call__(self, current_user: User = Depends(get_current_user)):
        # Check if user is an administrator
        if current_user.user_type != UserType.ADMINISTRATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator access required",
            )
        
        # Check if admin_type is in allowed list
        if current_user.admin_type not in self.allowed_admin_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient administrator privileges",
            )
        return current_user


# Backward compatibility
class RoleChecker(AdminChecker):
    """Deprecated - use AdminChecker instead."""
    pass