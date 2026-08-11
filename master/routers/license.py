"""
License & Desktop App API — Public endpoints for the Windows .exe app.

Flow:
  1. Customer buys plan on landing page → POST /api/license/purchase  → creates License (status=issued)
  2. Customer installs .exe → app calls POST /api/license/activate with license_key + machine_id
  3. Every app start → POST /api/license/validate (checks status + expiry + activations)
"""
import uuid
import hmac
import hashlib
import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter(prefix="/api/license", tags=["license"])

from main import require_super_admin

from database import get_master_db
from models import License, Tenant, PlatformInvoice
from sqlalchemy import select

router = APIRouter(prefix="/api/license", tags=["license"])

# Plan → price + limits
PLANS = {
    "starter":    {"price": 999,  "max_products": 100,  "messages": 500,   "users": 1, "ai_tiers": ["free", "paid"]},
    "growth":     {"price": 2499, "max_products": 500,  "messages": 2500,  "users": 5, "ai_tiers": ["free", "paid"]},
    "enterprise": {"price": 4999, "max_products": 0,    "messages": 0,     "users": 0, "ai_tiers": ["free", "paid"]},  # 0 = unlimited
}

# Annual (12 months for price of 10)
ANNUAL_MULTIPLIER = 10


def _gen_license_key() -> str:
    """Format: AURABIZ-XXXX-XXXX-XXXX-XXXX"""
    import secrets
    parts = ["".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4)) for _ in range(4)]
    return "AURABIZ-" + "-".join(parts)


def _verify_razorpay_signature(order_id: str, payment_id: str, signature: str, secret: str) -> bool:
    """Verify Razorpay payment signature to prevent fake payments."""
    if not signature or not secret:
        return False
    generated = hmac.new(
        secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated, signature)


def _validate_expiry(lic) -> bool:
    """Check if license is expired."""
    if lic.expires_at is None:
        return True  # Never expires (shouldn't happen with fix)
    now = datetime.now(timezone.utc)
    expires = lic.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > now


def _is_expired(expires_at) -> bool:
    """Compare safe — DB values can be naive (SQLite strips tz)."""
    if not expires_at:
        return False
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < now


# ─── Schemas ───
class CreateOrderRequest(BaseModel):
    plan: str
    billing: str = "monthly"
    ai_tier: str = "free"


class PurchaseRequest(BaseModel):
    plan: str                                   # starter | growth | enterprise
    billing: str = "monthly"                    # monthly | yearly
    owner_name: str
    owner_email: EmailStr
    owner_phone: Optional[str] = None
    payment_id: str                             # Razorpay payment id after successful payment
    payment_signature: Optional[str] = None     # Razorpay signature for verification
    razorpay_order_id: Optional[str] = None     # Razorpay order id for signature verification
    ai_tier: str = "free"                       # free | paid


class ActivateRequest(BaseModel):
    license_key: str
    machine_id: str                             # PC fingerprint from desktop app


class ValidateRequest(BaseModel):
    license_key: str
    machine_id: str


# ─── Endpoints ───
@router.post("/create-order")
async def create_order(req: CreateOrderRequest):
    """Create Razorpay order — call this BEFORE opening checkout."""
    from main import razorpay_client
    if not razorpay_client:
        raise HTTPException(status_code=503, detail="Razorpay not configured")

    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    plan = PLANS[req.plan]
    amount = plan["price"] if req.billing == "monthly" else plan["price"] * ANNUAL_MULTIPLIER

    try:
        order = razorpay_client.order.create({
            "amount": amount * 100,  # paise
            "currency": "INR",
            "receipt": f"aurabiz_{req.plan}_{uuid.uuid4().hex[:8]}",
            "notes": {"plan": req.plan, "billing": req.billing, "ai_tier": req.ai_tier},
        })
        return {
            "razorpay_order_id": order["id"],
            "amount": amount * 100,
            "currency": "INR",
            "key": os.getenv("RAZORPAY_KEY_ID", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order create failed: {str(e)}")


@router.get("/plans")
async def get_plans():
    """Landing page ke liye plan list + prices."""
    return {
        "plans": [
            {
                "id": pid,
                "price": p["price"],
                "annual_price": p["price"] * ANNUAL_MULTIPLIER,
                "max_products": p["max_products"],
                "messages": p["messages"],
                "ai_tiers": p["ai_tiers"],
            }
            for pid, p in PLANS.items()
        ]
    }


@router.post("/purchase")
async def purchase(req: PurchaseRequest):
    """Plan purchase ke baad license key generate karo (Razorpay payment verified)."""
    try:
        if req.plan not in PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan")

        plan = PLANS[req.plan]
        amount = plan["price"] if req.billing == "monthly" else plan["price"] * ANNUAL_MULTIPLIER
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[PURCHASE ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Purchase error: {str(e)}")

    # ── PAYMENT VERIFICATION ──
    razorpay_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if razorpay_secret and req.payment_signature and req.razorpay_order_id:
        if not _verify_razorpay_signature(req.razorpay_order_id, req.payment_id, req.payment_signature, razorpay_secret):
            raise HTTPException(status_code=400, detail="Payment signature verification failed")
    elif razorpay_secret and not req.payment_signature:
        raise HTTPException(status_code=400, detail="Payment signature required")

    # ── Calculate expiry (monthly also gets expiry now) ──
    if req.billing == "monthly":
        expiry = datetime.now(timezone.utc) + timedelta(days=30)
    else:
        expiry = datetime.now(timezone.utc) + timedelta(days=365)

    # Tenant (business) banao — same email se dedupe
    from database import async_session
    async with async_session() as db:
        tenant_result = await db.execute(select(Tenant).where(Tenant.owner_email == req.owner_email))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(
                slug=f"t{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
                name=f"{req.owner_name}'s Business",
                owner_name=req.owner_name,
                owner_email=req.owner_email,
                owner_phone=req.owner_phone,
                db_path="local-desktop-app",
                status="active",
                plan=req.plan,
                max_products=plan["max_products"] if plan["max_products"] else 1000,
                max_messages_per_month=plan["messages"] if plan["messages"] else 100000,
            )
            db.add(tenant)
            await db.flush()

        license_key = _gen_license_key()

        lic = License(
            license_key=license_key,
            tenant_id=tenant.id,
            plan=req.plan,
            status="issued",
            max_activations=1,
            activations_used=0,
            owner_name=req.owner_name,
            owner_email=req.owner_email,
            owner_phone=req.owner_phone,
            amount_paid=amount,
            ai_tier=req.ai_tier,
            paid_at=datetime.now(timezone.utc),
            expires_at=expiry,
        )
        db.add(lic)

        inv = PlatformInvoice(
            tenant_id=tenant.id,
            amount=amount,
            status="paid",
            plan=req.plan,
            billing_period=req.billing,
            payment_id=req.payment_id,
            paid_at=datetime.now(timezone.utc),
        )
        db.add(inv)
        await db.commit()

        return {
            "license_key": license_key,
            "plan": req.plan,
            "billing": req.billing,
            "amount_paid": amount,
            "ai_tier": req.ai_tier,
            "expires_at": str(expiry),
            "download_url": "/api/license/download-exe",
        }


@router.post("/activate")
async def activate(req: ActivateRequest):
    """Desktop app install ke baad pehli baar run — license activate karo."""
    print(f"[ACTIVATE] key={req.license_key}, machine={req.machine_id}")
    from database import async_session
    async with async_session() as db:
        result = await db.execute(select(License).where(License.license_key == req.license_key.upper()))
        lic = result.scalar_one_or_none()
        if not lic:
            print(f"[ACTIVATE] License not found!")
            raise HTTPException(status_code=404, detail="Invalid license key")
        print(f"[ACTIVATE] Found: status={lic.status}, machine={lic.machine_id}, used={lic.activations_used}")
        if not lic:
            raise HTTPException(status_code=404, detail="Invalid license key")

        if lic.status == "revoked":
            raise HTTPException(status_code=403, detail="License revoked")

        if _is_expired(lic.expires_at):
            lic.status = "expired"
            await db.commit()
            raise HTTPException(status_code=403, detail="License expired")

        # Already activated on this machine → OK (re-activation)
        if lic.machine_id == req.machine_id:
            lic.status = "activated"
            lic.last_activated_at = datetime.now(timezone.utc)
            await db.commit()
            return {"activated": True, "license_key": lic.license_key, "plan": lic.plan, "ai_tier": lic.ai_tier}

        # Activation limit check
        if (lic.activations_used or 0) >= lic.max_activations:
            raise HTTPException(status_code=403, detail="Activation limit reached")

        lic.machine_id = req.machine_id
        lic.activations_used = (lic.activations_used or 0) + 1
        lic.status = "activated"
        lic.last_activated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()
        print(f"[ACTIVATE] Committed! New status={lic.status}, machine={lic.machine_id}")

        return {"activated": True, "license_key": lic.license_key, "plan": lic.plan, "ai_tier": lic.ai_tier}


@router.post("/validate")
async def validate(req: ValidateRequest):
    """Har app start pe — license valid hai ya nahi check karo."""
    from database import async_session
    async with async_session() as db:
        result = await db.execute(select(License).where(License.license_key == req.license_key.upper()))
        lic = result.scalar_one_or_none()
        if not lic:
            raise HTTPException(status_code=404, detail="Invalid license key")

        if lic.status == "revoked":
            raise HTTPException(status_code=403, detail="License revoked")

        if lic.status == "issued":
            raise HTTPException(status_code=403, detail="License not activated yet — please activate first")

        if _is_expired(lic.expires_at):
            lic.status = "expired"
            await db.commit()
            raise HTTPException(status_code=403, detail="License expired")

        # Machine ID check — skip if machine_id is "skip" (for web dashboard login)
        if req.machine_id != "skip" and lic.machine_id is not None and lic.machine_id != req.machine_id:
            raise HTTPException(status_code=403, detail="License not activated on this machine")

        return {
            "valid": True,
            "license_key": lic.license_key,
            "plan": lic.plan,
            "ai_tier": lic.ai_tier,
            "owner_name": lic.owner_name,
            "owner_email": lic.owner_email,
            "expires_at": str(lic.expires_at) if lic.expires_at else None,
            "max_products": (PLANS[lic.plan]["max_products"] if lic.plan in PLANS and PLANS[lic.plan]["max_products"] else 1000),
        }


@router.get("/download-exe")
async def download_exe():
    """Windows .exe installer download — real built file serve karo."""
    import os
    from fastapi.responses import FileResponse

    # Repo-root relative: <root>/master/releases/AuraBiz-Setup.exe
    installer_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "releases",
        "AuraBiz-Setup.exe",
    )
    if os.path.exists(installer_path):
        return FileResponse(
            installer_path,
            filename="AuraBiz-Setup.exe",
            media_type="application/octet-stream",
        )
    return {
        "message": "Installer abhi build nahi hua — 'npm run dist' chalao desktop-app me.",
        "expected_path": installer_path,
    }


# ─── Super Admin endpoints (authenticated) ───
@router.get("/admin/licenses")
async def admin_list_licenses(admin=Depends(require_super_admin)):
    """Super admin: saare licenses ki list + details."""
    from database import async_session
    async with async_session() as db:
        result = await db.execute(
            select(License).order_by(License.created_at.desc()).limit(200)
        )
        licenses = result.scalars().all()
        return {
            "total": len(licenses),
            "licenses": [
                {
                    "id": l.id,
                    "license_key": l.license_key,
                    "plan": l.plan,
                    "status": l.status,
                    "ai_tier": l.ai_tier,
                    "owner_name": l.owner_name,
                    "owner_email": l.owner_email,
                    "owner_phone": l.owner_phone,
                    "amount_paid": l.amount_paid,
                    "machine_id": l.machine_id,
                    "activations_used": l.activations_used,
                    "max_activations": l.max_activations,
                    "expires_at": str(l.expires_at) if l.expires_at else None,
                    "created_at": str(l.created_at) if l.created_at else None,
                    "tenant_id": l.tenant_id,
                }
                for l in licenses
            ],
        }


@router.get("/admin/licenses/stats")
async def admin_license_stats(admin=Depends(require_super_admin)):
    """Super admin: license summary stats."""
    from database import async_session
    from sqlalchemy import func as sa_func
    async with async_session() as db:
        total = (await db.execute(select(sa_func.count(License.id)))).scalar() or 0
        activated = (await db.execute(select(sa_func.count(License.id)).where(License.status == "activated"))).scalar() or 0
        issued = (await db.execute(select(sa_func.count(License.id)).where(License.status == "issued"))).scalar() or 0
        revoked = (await db.execute(select(sa_func.count(License.id)).where(License.status == "revoked"))).scalar() or 0
        revenue = (await db.execute(select(sa_func.coalesce(sa_func.sum(License.amount_paid), 0)))).scalar() or 0
        paid_ai = (await db.execute(select(sa_func.count(License.id)).where(License.ai_tier == "paid"))).scalar() or 0
        free_ai = (await db.execute(select(sa_func.count(License.id)).where(License.ai_tier == "free"))).scalar() or 0
        by_plan = {}
        for plan in ["starter", "growth", "enterprise"]:
            by_plan[plan] = (await db.execute(select(sa_func.count(License.id)).where(License.plan == plan))).scalar() or 0
        return {
            "total": total,
            "activated": activated,
            "issued": issued,
            "revoked": revoked,
            "revenue": revenue,
            "paid_ai": paid_ai,
            "free_ai": free_ai,
            "by_plan": by_plan,
        }


@router.post("/admin/licenses/{license_key}/revoke")
async def admin_revoke_license(license_key: str, admin=Depends(require_super_admin)):
    """Super admin: license revoke karo (customer ka app band hoga)."""
    from database import async_session
    async with async_session() as db:
        result = await db.execute(select(License).where(License.license_key == license_key.upper()))
        lic = result.scalar_one_or_none()
        if not lic:
            raise HTTPException(status_code=404, detail="License nahi mila")
        lic.status = "revoked"
        await db.commit()
        return {"message": "License revoked", "license_key": lic.license_key}
