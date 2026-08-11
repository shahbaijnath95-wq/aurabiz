from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from database import get_db
from models import User

SECRET_KEY = settings.SECRET_KEY or settings.JWT_SECRET_KEY
if not SECRET_KEY:
    raise ValueError("SECRET_KEY ya JWT_SECRET_KEY .env mein set karo — insecure fallback nahi chalega!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid ya expired hai",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account deactivated hai")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role — use as Depends(require_admin) on admin-only endpoints."""
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require super_admin role — use for critical operations."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


async def get_user_from_token(token: str, db: AsyncSession) -> User:
    """Validate a raw token string and return the user — used for WebSocket auth."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user


async def verify_business_access(
    user: User,
    business_id: str,
    db: AsyncSession,
) -> bool:
    """
    Verify that the authenticated user is allowed to access the requested business.
    Prevents IDOR (Insecure Direct Object Reference) attacks.

    Access rules:
      - super_admin: any business
      - Business owner: Business.user_id == user.id
      - Active team member: TeamMember.user_id == user.id, linked to the business
        through an active Team, with the member itself active
      - Everything else: denied
    """
    # Super admin bypass
    if user.role == "super_admin":
        return True

    # SECURITY FIX: ownership check — user must OWN the business.
    # Previously this only checked that the business existed and the user was
    # active, which let ANY logged-in user read ANY business's data (IDOR).
    from models import Business, Team, TeamMember

    result = await db.execute(
        select(Business).where(
            Business.id == business_id,
            Business.user_id == user.id,
        )
    )
    if result.scalar_one_or_none() is not None:
        return True

    # Team member access: active member of an active team in this business
    team_result = await db.execute(
        select(TeamMember.id)
        .join(Team, Team.id == TeamMember.team_id)
        .where(
            Team.business_id == business_id,
            Team.is_active.is_(True),
            TeamMember.user_id == user.id,
            TeamMember.is_active.is_(True),
        )
    )
    return team_result.scalar_one_or_none() is not None
