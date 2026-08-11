from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, Business
from schemas import UserCreate, UserResponse, Token, BusinessCreate, BusinessResponse
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from pydantic import BaseModel
import secrets
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


async def _audit_log(db: AsyncSession, business_id: str, action: str, entity_type: str, entity_id: str, changes: dict = None, ip: str = None):
    """Helper to write audit log entry — safe if audit service not available."""
    try:
        from services.audit_service import AuditService
        svc = AuditService(db)
        await svc.log_action(
            business_id=business_id, action=action, entity_type=entity_type,
            entity_id=entity_id, changes=changes, ip_address=ip,
        )
    except Exception:
        pass  # Audit logging failure should not break the request


@router.post("/register", response_model=Token)
async def register(request: Request, data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email pehle se registered hai")

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
    )
    db.add(user)
    await db.flush()

    business = Business(user_id=user.id, name=data.full_name + "'s Business")
    db.add(business)
    await db.flush()

    tenant_id = getattr(request.state, "tenant_id", "default")
    token = create_access_token(data={"sub": user.id, "tenant_id": tenant_id})
    await _audit_log(db, getattr(business, "id", "default"), "register", "user", user.id, {"email": user.email}, ip=request.client.host if request.client else None)
    return Token(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            role=user.role, is_active=user.is_active,
        ),
    )


# ─── Email OTP Verification ───

# In-memory OTP store (production me Redis use karo)
_otp_store: dict[str, dict] = {}


@router.post("/send-otp")
async def send_otp(data: dict, db: AsyncSession = Depends(get_db)):
    """Email pe 6-digit OTP bhejo."""
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email do")

    # Check if email already registered
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email pehle se registered hai")

    # Generate 6-digit OTP
    otp = "".join(secrets.choice("0123456789") for _ in range(6))
    _otp_store[email] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "attempts": 0,
    }

    # TODO: Production me email bhejo (SendGrid/Resend)
    # Abhi development me OTP return kar dete hain
    return {"message": "OTP bhej diya gaya", "otp": otp, "expires_in": "5 minutes"}


@router.post("/verify-otp")
async def verify_otp(data: dict):
    """OTP verify karo."""
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    stored = _otp_store.get(email)
    if not stored:
        raise HTTPException(status_code=400, detail="OTP nahi mila — pehle se request karo")

    if datetime.now(timezone.utc) > stored["expires_at"]:
        del _otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expire ho gaya — dubara request karo")

    stored["attempts"] += 1
    if stored["attempts"] > 5:
        del _otp_store[email]
        raise HTTPException(status_code=400, detail="Zyada attempts — dubara request karo")

    if stored["otp"] != otp:
        raise HTTPException(status_code=400, detail="Galat OTP")

    # OTP verified — delete from store
    del _otp_store[email]
    return {"verified": True, "message": "Email verify ho gaya!"}


@router.post("/login", response_model=Token)
async def login(request: Request, data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ya password galat hai")

    tenant_id = getattr(request.state, "tenant_id", "default")
    token = create_access_token(data={"sub": user.id, "tenant_id": tenant_id})
    # Audit log
    await _audit_log(db, "default", "login", "user", user.id, {"email": user.email}, ip=request.client.host if request.client else None)
    return Token(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            role=user.role, is_active=user.is_active,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id, email=current_user.email,
        full_name=current_user.full_name, role=current_user.role,
        is_active=current_user.is_active, phone=current_user.phone,
    )


@router.get("/business")
async def get_business(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Business).where(Business.user_id == current_user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business setup nahi hua")
    return {
        "id": business.id, "name": business.name, "type": business.type,
        "phone_number": business.phone_number, "currency": business.currency,
        "timezone": business.timezone, "subscription_tier": business.subscription_tier,
        "onboarding_completed": business.onboarding_completed,
    }


@router.post("/business", response_model=BusinessResponse)
async def create_business(
    data: BusinessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Business).where(Business.user_id == current_user.id))
    existing = result.scalar_one_or_none()
    if existing:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        await db.flush()
        return BusinessResponse(
            id=existing.id, user_id=existing.user_id, name=existing.name,
            currency=existing.currency, timezone=existing.timezone,
            locale=existing.locale, subscription_tier=existing.subscription_tier,
            subscription_status=existing.subscription_status,
            onboarding_completed=existing.onboarding_completed,
        )

    business = Business(user_id=current_user.id, **data.model_dump())
    db.add(business)
    await db.flush()
    return BusinessResponse(
        id=business.id, user_id=business.user_id, name=business.name,
        currency=business.currency, timezone=business.timezone,
        locale=business.locale, subscription_tier=business.subscription_tier,
        subscription_status=business.subscription_status,
        onboarding_completed=business.onboarding_completed,
    )


# ─── FORGOT PASSWORD ───────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class LicenseLoginRequest(BaseModel):
    license_key: str


@router.post("/license-login", response_model=Token)
async def license_login(req: LicenseLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Desktop app se license key se auto-login — no email/password needed."""
    import httpx

    # Step 1: Validate license against master backend
    master_url = "http://localhost:8010"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            # Use machine_id="skip" to bypass machine check (web dashboard login)
            resp = await client.post(f"{master_url}/api/license/validate", json={
                "license_key": req.license_key,
                "machine_id": "skip",
            })
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="License invalid hai!")
            lic_data = resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Master backend unreachable: {str(e)}")

    # Step 2: Find or create user from license owner_email
    owner_email = lic_data.get("owner_email") or f"{lic_data['license_key'].lower().replace('-', '')}@aurabiz.local"
    owner_name = lic_data.get("owner_name") or "AuraBiz User"
    plan = lic_data.get("plan", "starter")

    result = await db.execute(select(User).where(User.email == owner_email))
    user = result.scalar_one_or_none()

    if not user:
        # Create new user from license
        user = User(
            email=owner_email,
            password_hash=get_password_hash(secrets.token_urlsafe(16)),
            full_name=owner_name,
            phone=None,
        )
        db.add(user)
        await db.flush()

        # Create business
        business = Business(user_id=user.id, name=f"{owner_name}'s Business", subscription_tier=plan)
        db.add(business)
        await db.flush()

    # Step 3: Generate JWT token
    tenant_id = getattr(request.state, "tenant_id", "default")
    token = create_access_token(data={"sub": user.id, "tenant_id": tenant_id})

    return Token(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, full_name=user.full_name,
            role=user.role, is_active=user.is_active,
        ),
    )


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send password reset token (in production, send via email)."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        # Don't reveal if email exists or not
        return {"message": "Agar email registered hai, toh reset link bheja jayega"}

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.flush()

    # In production, send email with reset link
    return {
        "message": "Reset token generate ho gaya. Email check karo.",
        "expires_in": "1 hour",
    }


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token."""
    result = await db.execute(select(User).where(User.reset_token == req.token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid ya expired token")

    # Check token expiry
    if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expire ho gaya")

    # Update password
    user.password_hash = get_password_hash(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.flush()

    return {"message": "Password successfully reset ho gaya. Ab login karein."}
