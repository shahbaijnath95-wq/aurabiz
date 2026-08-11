"""Master Backend — Super Admin API (port 8010)"""
import sys
import os
import uuid
import secrets
import json
import hmac
import hashlib
import razorpay
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext

from database import get_master_db, init_master_db
from models import (
    Tenant, AdminUser, AIProvider, AIUsageLog, PlatformInvoice, PlatformStats,
    AdminAuditLog, FeatureFlag, APIKey, SupportTicket, SupportMessage,
    Notification, NotificationSetting, PlatformWebhook, WebhookDeliveryLog,
    Backup, Reseller, ResellerPayout, WhiteLabelConfig, Integration,
)
from config import (
    MASTER_JWT_SECRET, MASTER_JWT_ALGORITHM, MASTER_JWT_EXPIRY_HOURS,
    DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
)

# ─── Razorpay Client ───
razorpay_client = None
_rzp_key = os.getenv("RAZORPAY_KEY_ID", "")
_rzp_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
if _rzp_key and _rzp_secret:
    try:
        razorpay_client = razorpay.Client(auth=(_rzp_key, _rzp_secret))
        print("[Razorpay] Client initialized")
    except Exception as e:
        print(f"[Razorpay] Init failed: {e}")
else:
    print("[Razorpay] Keys not set — payment endpoints will return errors")

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Helper: Hash password (bcrypt with salt) ───
def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(admin_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=MASTER_JWT_EXPIRY_HOURS)
    return jwt.encode({"sub": admin_id, "exp": exp}, MASTER_JWT_SECRET, algorithm=MASTER_JWT_ALGORITHM)


# ─── Lifespan: init DB + create default admin ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast if critical secrets not configured
    if not MASTER_JWT_SECRET:
        print("\n" + "!" * 60)
        print("[WARNING] MASTER_JWT_SECRET not set — using JWT_SECRET_KEY fallback")
        print("Set MASTER_JWT_SECRET env var in production!")
        print("!" * 60 + "\n")
    if not DEFAULT_ADMIN_PASSWORD:
        print("\n" + "!" * 60)
        print("[WARNING] DEFAULT_ADMIN_PASSWORD not set — a random password will be generated")
        print("Set DEFAULT_ADMIN_PASSWORD env var in production!")
        print("!" * 60 + "\n")
    await init_master_db()
    # Create default super admin if not exists
    from database import async_session
    async with async_session() as db:
        result = await db.execute(select(AdminUser).where(AdminUser.email == DEFAULT_ADMIN_EMAIL))
        admin = result.scalar_one_or_none()
        if not admin:
            # Never use a hardcoded known password — generate a random one when env var is missing
            password = DEFAULT_ADMIN_PASSWORD or secrets.token_urlsafe(24)
            admin = AdminUser(
                email=DEFAULT_ADMIN_EMAIL,
                password_hash=hash_password(password),
                name="Super Admin",
                role="super_admin",
            )
            db.add(admin)
            await db.commit()
            if not DEFAULT_ADMIN_PASSWORD:
                print("\n" + "=" * 60)
                print(f"[SETUP] Default admin created: {DEFAULT_ADMIN_EMAIL}")
                print(f"[SETUP] Password (random, generated once): {password}")
                print("[SETUP] Set DEFAULT_ADMIN_PASSWORD env var and restart to use your own password.")
                print("=" * 60 + "\n")
        elif admin.password_hash and not admin.password_hash.startswith("$2") and DEFAULT_ADMIN_PASSWORD:
            # Migrate old SHA-256 hash to bcrypt
            admin.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
            await db.commit()
        # Security warnings (no credentials are printed to console)
        if os.getenv("MASTER_JWT_SECRET") is None or os.getenv("MASTER_JWT_SECRET") == "change-me-in-production":
            print("\n" + "!" * 60)
            print("[SECURITY WARNING] Default JWT secret is set!")
            print("   Set MASTER_JWT_SECRET env variable in production!")
            print("!" * 60 + "\n")
        if not DEFAULT_ADMIN_PASSWORD:
            print("\n" + "!" * 60)
            print("[SECURITY WARNING] DEFAULT_ADMIN_PASSWORD not set — admin password is randomly generated")
            print("   Set DEFAULT_ADMIN_PASSWORD env variable in production!")
            print("!" * 60 + "\n")
    yield


app = FastAPI(title="Master Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Desktop app (file://) + all localhost origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth dependency ───
async def get_current_admin(
    cred: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_master_db),
):
    if not cred:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(cred.credentials, MASTER_JWT_SECRET, algorithms=[MASTER_JWT_ALGORITHM])
        admin_id = payload.get("sub")
    except Exception:
        raise HTTPException(401, "Invalid token")
    result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(401, "Admin not found or inactive")
    return admin


# ─── Role-based dependencies ───
async def require_super_admin(admin=Depends(get_current_admin)):
    if admin.role != "super_admin":
        raise HTTPException(403, "Super admin access required")
    return admin


async def require_admin(admin=Depends(get_current_admin)):
    if admin.role not in ("super_admin", "admin"):
        raise HTTPException(403, "Admin access required")
    return admin


# ═══════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════

@app.post("/admin/login")
async def admin_login(data: dict, db: AsyncSession = Depends(get_master_db)):
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if not email or not password:
        raise HTTPException(400, "Email and password required")
    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(password, admin.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if not admin.is_active:
        raise HTTPException(403, "Account disabled")
    admin.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    token = create_token(admin.id)
    return {"token": token, "admin": {"id": admin.id, "email": admin.email, "name": admin.name, "role": admin.role}}


@app.get("/admin/me")
async def admin_me(admin=Depends(get_current_admin)):
    return {"id": admin.id, "email": admin.email, "name": admin.name, "role": admin.role}


# ═══════════════════════════════════════════════════
# TENANT MANAGEMENT
# ═══════════════════════════════════════════════════

@app.get("/admin/tenants")
async def list_tenants(
    status: str = None,
    plan: str = None,
    search: str = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    q = select(Tenant)
    if status:
        q = q.where(Tenant.status == status)
    if plan:
        q = q.where(Tenant.plan == plan)
    if search:
        q = q.where(Tenant.name.ilike(f"%{search}%") | Tenant.owner_email.ilike(f"%{search}%"))
    q = q.order_by(Tenant.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    tenants = result.scalars().all()
    # Count total
    count_q = select(func.count(Tenant.id))
    if status:
        count_q = count_q.where(Tenant.status == status)
    total = (await db.execute(count_q)).scalar() or 0
    return {
        "tenants": [
            {
                "id": t.id, "slug": t.slug, "name": t.name,
                "owner_name": t.owner_name, "owner_email": t.owner_email,
                "status": t.status, "plan": t.plan,
                "messages_used": t.messages_used_this_month,
                "max_messages": t.max_messages_per_month,
                "created_at": str(t.created_at),
            }
            for t in tenants
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@app.post("/admin/tenants")
async def create_tenant(data: dict, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    name = data.get("name", "").strip()
    owner_email = data.get("owner_email", "").strip()
    owner_name = data.get("owner_name", "")
    plan = data.get("plan", "starter")
    if not name or not owner_email:
        raise HTTPException(400, "name and owner_email required")
    # Create slug
    import re
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    # Check unique
    existing = await db.execute(select(Tenant).where((Tenant.slug == slug) | (Tenant.owner_email == owner_email)))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Tenant with this name or email already exists")
    # Create tenant DB
    from config import TENANTS_DIR
    tenant_id = str(uuid.uuid4())
    db_path = str(TENANTS_DIR / f"{tenant_id}.db")
    tenant = Tenant(
        id=tenant_id, slug=slug, name=name,
        owner_name=owner_name, owner_email=owner_email,
        db_path=db_path, plan=plan,
        status="active",
    )
    db.add(tenant)
    await db.commit()
    return {"id": tenant.id, "slug": tenant.slug, "name": tenant.name, "status": tenant.status}


@app.get("/admin/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")
    return {
        "id": t.id, "slug": t.slug, "name": t.name,
        "owner_name": t.owner_name, "owner_email": t.owner_email, "owner_phone": t.owner_phone,
        "status": t.status, "plan": t.plan,
        "messages_used": t.messages_used_this_month, "max_messages": t.max_messages_per_month,
        "preferred_language": t.preferred_language,
        "created_at": str(t.created_at), "trial_ends_at": str(t.trial_ends_at) if t.trial_ends_at else None,
    }


@app.post("/admin/tenants/{tenant_id}/suspend")
async def suspend_tenant(tenant_id: str, data: dict, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")
    t.status = "suspended"
    t.suspended_at = datetime.now(timezone.utc)
    t.suspend_reason = data.get("reason", "")
    await db.commit()
    return {"status": "suspended", "tenant_id": tenant_id}


@app.post("/admin/tenants/{tenant_id}/reactivate")
async def reactivate_tenant(tenant_id: str, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")
    t.status = "active"
    t.suspended_at = None
    t.suspend_reason = None
    await db.commit()
    return {"status": "active", "tenant_id": tenant_id}


# ═══════════════════════════════════════════════════
# AI PROVIDER MANAGEMENT
# ═══════════════════════════════════════════════════

@app.get("/admin/ai-providers")
async def list_ai_providers(db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(AIProvider).order_by(AIProvider.priority.desc()))
    providers = result.scalars().all()
    return {
        "providers": [
            {
                "id": p.id, "name": p.name, "provider_key": p.provider_key,
                "model": p.model, "is_active": p.is_active, "priority": p.priority,
                "rate_limit_rpm": p.rate_limit_rpm, "rate_limit_rpd": p.rate_limit_rpd,
                "cost_per_1k_tokens": p.cost_per_1k_tokens,
                "has_api_key": bool(p.api_key),
                "created_at": str(p.created_at),
            }
            for p in providers
        ]
    }


@app.post("/admin/ai-providers")
async def create_ai_provider(data: dict, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    name = data.get("name", "").strip()
    provider_key = data.get("provider_key", "").strip().lower()
    api_key = data.get("api_key", "").strip()
    if not name or not provider_key or not api_key:
        raise HTTPException(400, "name, provider_key, and api_key required")
    existing = await db.execute(select(AIProvider).where(AIProvider.provider_key == provider_key))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Provider '{provider_key}' already exists. Use PUT to update.")
    provider = AIProvider(
        name=name, provider_key=provider_key, api_key=api_key,
        account_id=data.get("account_id", ""),
        model=data.get("model", ""),
        priority=data.get("priority", 0),
        rate_limit_rpm=data.get("rate_limit_rpm", 50),
        rate_limit_rpd=data.get("rate_limit_rpd", 1500),
        cost_per_1k_tokens=data.get("cost_per_1k_tokens", 0.0),
        is_active=data.get("is_active", True),
        config=data.get("config", {}),
    )
    db.add(provider)
    await db.commit()
    return {"id": provider.id, "name": provider.name, "provider_key": provider.provider_key}


@app.put("/admin/ai-providers/{provider_id}")
async def update_ai_provider(provider_id: str, data: dict, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Provider not found")
    for field in ["name", "api_key", "account_id", "model", "is_active", "priority", "rate_limit_rpm", "rate_limit_rpd", "cost_per_1k_tokens", "config"]:
        if field in data:
            setattr(p, field, data[field])
    await db.commit()
    return {"status": "updated", "provider_id": provider_id}


@app.delete("/admin/ai-providers/{provider_id}")
async def delete_ai_provider(provider_id: str, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Provider not found")
    await db.delete(p)
    await db.commit()
    return {"status": "deleted"}


@app.get("/admin/ai-providers/{provider_id}")
async def get_ai_provider(provider_id: str, db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(AIProvider).where(AIProvider.id == provider_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Provider not found")
    return {
        "id": p.id, "name": p.name, "provider_key": p.provider_key,
        "api_key": p.api_key, "account_id": p.account_id,
        "model": p.model, "is_active": p.is_active, "priority": p.priority,
        "rate_limit_rpm": p.rate_limit_rpm, "rate_limit_rpd": p.rate_limit_rpd,
        "cost_per_1k_tokens": p.cost_per_1k_tokens,
        "config": p.config,
        "created_at": str(p.created_at),
    }


@app.get("/admin/ai-usage")
async def get_ai_usage(
    tenant_id: str = None,
    provider_key: str = None,
    days: int = 7,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    q = select(AIUsageLog).where(AIUsageLog.created_at >= cutoff)
    if tenant_id:
        q = q.where(AIUsageLog.tenant_id == tenant_id)
    if provider_key:
        q = q.where(AIUsageLog.provider_key == provider_key)
    q = q.order_by(AIUsageLog.created_at.desc()).limit(500)
    result = await db.execute(q)
    logs = result.scalars().all()
    # Aggregate
    total_tokens_in = sum(l.tokens_in for l in logs)
    total_tokens_out = sum(l.tokens_out for l in logs)
    success_count = sum(1 for l in logs if l.success)
    return {
        "total_requests": len(logs),
        "success_rate": round(success_count / len(logs) * 100, 1) if logs else 0,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "recent_logs": [
            {
                "tenant_id": l.tenant_id, "provider": l.provider_key,
                "model": l.model, "tokens_in": l.tokens_in, "tokens_out": l.tokens_out,
                "latency_ms": l.latency_ms, "success": l.success,
                "created_at": str(l.created_at),
            }
            for l in logs[:50]
        ],
    }


# ═══════════════════════════════════════════════════
# PLATFORM ANALYTICS
# ═══════════════════════════════════════════════════

# ─── Centralized Plan Config (single source of truth) ───
PLANS = {
    "starter":    {"price": 999,  "max_products": 100,  "messages": 500,   "users": 1, "ai_tiers": ["free", "paid"]},
    "growth":     {"price": 2499, "max_products": 500,  "messages": 2500,  "users": 5, "ai_tiers": ["free", "paid"]},
    "enterprise": {"price": 4999, "max_products": 0,    "messages": 0,     "users": 0, "ai_tiers": ["free", "paid"]},  # 0 = unlimited
}
PLAN_PRICES = {pid: p["price"] for pid, p in PLANS.items()}
PLAN_LIMITS = {pid: {"messages": p["messages"], "products": p["max_products"], "users": p["users"]} for pid, p in PLANS.items()}


@app.get("/admin/analytics/overview")
async def analytics_overview(db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    total_tenants = (await db.execute(select(func.count(Tenant.id)))).scalar() or 0
    active_tenants = (await db.execute(select(func.count(Tenant.id)).where(Tenant.status == "active"))).scalar() or 0
    total_messages = (await db.execute(select(func.sum(Tenant.messages_used_this_month)))).scalar() or 0

    # Revenue from paid invoices
    total_revenue = (await db.execute(
        select(func.sum(PlatformInvoice.amount)).where(PlatformInvoice.status == "paid")
    )).scalar() or 0
    pending_revenue = (await db.execute(
        select(func.sum(PlatformInvoice.amount)).where(PlatformInvoice.status == "pending")
    )).scalar() or 0

    # Plan distribution
    from sqlalchemy import case
    plan_counts = {}
    for plan_name in ["starter", "growth", "enterprise"]:
        count = (await db.execute(
            select(func.count(Tenant.id)).where(Tenant.status != "deleted", Tenant.plan == plan_name)
        )).scalar() or 0
        plan_counts[plan_name] = count

    # MRR
    mrr = sum(PLAN_PRICES.get(p, 0) * c for p, c in plan_counts.items())

    # New signups this month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = (await db.execute(
        select(func.count(Tenant.id)).where(Tenant.created_at >= month_start)
    )).scalar() or 0

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "suspended_tenants": total_tenants - active_tenants,
        "total_messages_this_month": total_messages,
        "total_revenue": round(total_revenue, 2),
        "pending_revenue": round(pending_revenue, 2),
        "mrr": mrr,
        "plan_distribution": plan_counts,
        "new_signups_this_month": new_this_month,
    }


@app.get("/admin/analytics/daily")
async def analytics_daily(
    days: int = 30,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    """Daily aggregated stats for chart display."""
    from services.analytics_aggregator import get_daily_stats
    stats = get_daily_stats(days)
    return {"stats": stats, "days": days}


@app.get("/admin/analytics/growth")
async def analytics_growth(db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    """Growth metrics: signups, plan distribution, MRR, churn."""
    from services.analytics_aggregator import get_growth_stats
    return get_growth_stats()


@app.get("/admin/analytics/top-tenants")
async def analytics_top_tenants(
    limit: int = 10,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    """Top tenants by usage."""
    from services.analytics_aggregator import get_top_tenants
    return {"tenants": get_top_tenants(limit)}


@app.post("/admin/analytics/aggregate")
async def analytics_aggregate(db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    """Manually trigger daily stats aggregation."""
    from services.analytics_aggregator import aggregate_daily_stats
    result = aggregate_daily_stats()
    return {"status": "ok", "result": result}


# ═══════════════════════════════════════════════════
# BILLING & INVOICES
# ═══════════════════════════════════════════════════

@app.get("/admin/billing/invoices")
async def list_invoices(
    status: str = None,
    tenant_id: str = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    q = select(PlatformInvoice)
    if status:
        q = q.where(PlatformInvoice.status == status)
    if tenant_id:
        q = q.where(PlatformInvoice.tenant_id == tenant_id)
    q = q.order_by(PlatformInvoice.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    invoices = result.scalars().all()

    # Count total
    count_q = select(func.count(PlatformInvoice.id))
    if status:
        count_q = count_q.where(PlatformInvoice.status == status)
    if tenant_id:
        count_q = count_q.where(PlatformInvoice.tenant_id == tenant_id)
    total = (await db.execute(count_q)).scalar() or 0

    # Get tenant names for display
    invoice_list = []
    for inv in invoices:
        t_result = await db.execute(select(Tenant.name).where(Tenant.id == inv.tenant_id))
        tenant_name = t_result.scalar() or "Unknown"
        invoice_list.append({
            "id": inv.id, "tenant_id": inv.tenant_id, "tenant_name": tenant_name,
            "amount": inv.amount, "currency": inv.currency, "status": inv.status,
            "plan": inv.plan, "billing_period": inv.billing_period,
            "payment_id": inv.payment_id,
            "created_at": str(inv.created_at),
            "paid_at": str(inv.paid_at) if inv.paid_at else None,
        })

    return {
        "invoices": invoice_list,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    }


@app.post("/admin/billing/invoices")
async def create_invoice(
    data: dict,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    tenant_id = data.get("tenant_id", "")
    amount = data.get("amount", 0)
    plan = data.get("plan", "growth")
    billing_period = data.get("billing_period", "")

    if not tenant_id or not amount:
        raise HTTPException(400, "tenant_id and amount required")

    # Verify tenant exists
    t_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    if not t_result.scalar_one_or_none():
        raise HTTPException(404, "Tenant not found")

    invoice = PlatformInvoice(
        tenant_id=tenant_id,
        amount=float(amount),
        plan=plan,
        billing_period=billing_period or datetime.now(timezone.utc).strftime("%Y-%m"),
        status="pending",
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return {"id": invoice.id, "status": "created", "amount": invoice.amount}


@app.put("/admin/billing/invoices/{invoice_id}")
async def update_invoice(
    invoice_id: str,
    data: dict,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    result = await db.execute(select(PlatformInvoice).where(PlatformInvoice.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    new_status = data.get("status")
    if new_status:
        inv.status = new_status
        if new_status == "paid":
            inv.paid_at = datetime.now(timezone.utc)
            inv.payment_id = data.get("payment_id", "")

    await db.commit()
    return {"status": "updated", "invoice_id": invoice_id, "new_status": inv.status}


@app.get("/admin/billing/revenue")
async def billing_revenue(db: AsyncSession = Depends(get_master_db), admin=Depends(get_current_admin)):
    """Revenue summary for billing dashboard."""
    total_collected = (await db.execute(
        select(func.sum(PlatformInvoice.amount)).where(PlatformInvoice.status == "paid")
    )).scalar() or 0

    total_pending = (await db.execute(
        select(func.sum(PlatformInvoice.amount)).where(PlatformInvoice.status == "pending")
    )).scalar() or 0

    total_overdue = (await db.execute(
        select(func.sum(PlatformInvoice.amount)).where(PlatformInvoice.status == "overdue")
    )).scalar() or 0

    overdue_count = (await db.execute(
        select(func.count(PlatformInvoice.id)).where(PlatformInvoice.status == "overdue")
    )).scalar() or 0

    total_invoices = (await db.execute(select(func.count(PlatformInvoice.id)))).scalar() or 0
    paid_count = (await db.execute(
        select(func.count(PlatformInvoice.id)).where(PlatformInvoice.status == "paid")
    )).scalar() or 0

    # Plan distribution with revenue
    plan_revenue = {}
    for plan_name in ["starter", "growth", "enterprise"]:
        rev = (await db.execute(
            select(func.sum(PlatformInvoice.amount)).where(
                PlatformInvoice.status == "paid", PlatformInvoice.plan == plan_name
            )
        )).scalar() or 0
        plan_revenue[plan_name] = round(rev, 2)

    # MRR from active subscriptions
    mrr = 0
    for plan_name in ["starter", "growth", "enterprise"]:
        count = (await db.execute(
            select(func.count(Tenant.id)).where(Tenant.status == "active", Tenant.plan == plan_name)
        )).scalar() or 0
        mrr += PLAN_PRICES.get(plan_name, 0) * count

    return {
        "total_collected": round(total_collected, 2),
        "total_pending": round(total_pending, 2),
        "total_overdue": round(total_overdue, 2),
        "overdue_count": overdue_count,
        "total_invoices": total_invoices,
        "paid_count": paid_count,
        "collection_rate": round((paid_count / max(total_invoices, 1)) * 100, 1),
        "mrr": mrr,
        "plan_revenue": plan_revenue,
    }


@app.put("/admin/tenants/{tenant_id}/plan")
async def update_tenant_plan(
    tenant_id: str,
    data: dict,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    """Change a tenant's subscription plan."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")

    new_plan = data.get("plan", "").lower()
    if new_plan not in PLAN_PRICES:
        raise HTTPException(400, f"Invalid plan. Valid: {list(PLAN_PRICES.keys())}")

    # Plan limits
    plan_limits = {
        "starter": {"max_products": 50, "max_messages_per_month": 500},
        "growth": {"max_products": 9999, "max_messages_per_month": 5000},
        "enterprise": {"max_products": 99999, "max_messages_per_month": 99999},
    }

    old_plan = t.plan
    t.plan = new_plan
    t.max_products = plan_limits[new_plan]["max_products"]
    t.max_messages_per_month = plan_limits[new_plan]["max_messages_per_month"]
    t.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "updated",
        "tenant_id": tenant_id,
        "old_plan": old_plan,
        "new_plan": new_plan,
        "max_products": t.max_products,
        "max_messages_per_month": t.max_messages_per_month,
    }


# ═══════════════════════════════════════════════════
# TENANT DATA PROXY (view any tenant's data)
# ═══════════════════════════════════════════════════

@app.get("/admin/tenants/{tenant_id}/data/{table_name}")
async def get_tenant_data(
    tenant_id: str,
    table_name: str,
    limit: int = 50,
    page: int = 1,
    db: AsyncSession = Depends(get_master_db),
    admin=Depends(get_current_admin),
):
    """Proxy to read data from a tenant's database."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Tenant not found")

    import sqlite3
    valid_tables = [
        "customers", "orders", "products", "bookings", "whatsapp_messages",
        "conversations", "payments", "transactions", "coupons", "invoices",
    ]
    if table_name not in valid_tables:
        raise HTTPException(400, f"Invalid table. Valid: {valid_tables}")

    try:
        conn = sqlite3.connect(t.db_path)
        conn.row_factory = sqlite3.Row
        offset = (page - 1) * limit
        rows = conn.execute(f"SELECT * FROM [{table_name}] ORDER BY rowid DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
        conn.close()
        return {
            "data": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit,
        }
    except Exception as e:
        raise HTTPException(500, f"Error reading tenant DB: {str(e)}")


# ─── OmniRoute Config ───
import json

OMNIRoute_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "config", "omniroute_models.json")

def load_omniroute_config():
    try:
        with open(OMNIRoute_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"omniroute": {}, "opencode_models": [], "settings": {}}

def save_omniroute_config(data):
    try:
        with open(OMNIRoute_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

@app.get("/omniroute/config")
async def get_omniroute_config(auth=Depends(get_current_admin)):
    return load_omniroute_config()

@app.get("/omniroute/models")
async def get_omniroute_models(auth=Depends(get_current_admin)):
    config = load_omniroute_config()
    return {"models": config.get("opencode_models", []), "default_model": config.get("default_model", "")}

@app.put("/omniroute/config")
async def update_omniroute_config(body: dict, auth=Depends(get_current_admin)):
    current = load_omniroute_config()
    current.update(body)
    if save_omniroute_config(current):
        return {"status": "ok", "message": "Config updated"}
    raise HTTPException(500, "Failed to save config")

@app.put("/omniroute/settings")
async def update_omniroute_settings(body: dict, auth=Depends(get_current_admin)):
    current = load_omniroute_config()
    current["settings"] = {**current.get("settings", {}), **body}
    if save_omniroute_config(current):
        return {"status": "ok", "message": "Settings updated"}
    raise HTTPException(500, "Failed to save settings")

@app.put("/omniroute/default-model")
async def set_default_model(body: dict, auth=Depends(get_current_admin)):
    model_id = body.get("model_id", "")
    current = load_omniroute_config()
    current["default_model"] = model_id
    if save_omniroute_config(current):
        return {"status": "ok", "message": f"Default model set to {model_id}"}
    raise HTTPException(500, "Failed to save")

@app.put("/omniroute/fallback-chain")
async def set_fallback_chain(body: dict, auth=Depends(get_current_admin)):
    chain = body.get("chain", [])
    current = load_omniroute_config()
    current["fallback_chain"] = chain
    if save_omniroute_config(current):
        return {"status": "ok", "message": "Fallback chain updated"}
    raise HTTPException(500, "Failed to save")


# ─── Audit Log Endpoints ───
@app.get("/admin/audit-logs")
async def list_audit_logs(
    admin_user_id: str = None,
    action: str = None,
    page: int = 1,
    limit: int = 50,
    start_date: str = None,
    end_date: str = None,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    q = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())
    if admin_user_id:
        q = q.where(AdminAuditLog.admin_user_id == admin_user_id)
    if action:
        q = q.where(AdminAuditLog.action.contains(action))
    if start_date:
        q = q.where(AdminAuditLog.created_at >= start_date)
    if end_date:
        q = q.where(AdminAuditLog.created_at <= end_date)
    q = q.offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    logs = result.scalars().all()
    return {
        "logs": [
            {
                "id": l.id,
                "admin_user_id": l.admin_user_id,
                "action": l.action,
                "target_tenant_id": l.target_tenant_id,
                "details": l.details,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": len(logs),
        "page": page,
    }


@app.get("/admin/audit-logs/export")
async def export_audit_logs(
    start_date: str = None,
    end_date: str = None,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    q = select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())
    if start_date:
        q = q.where(AdminAuditLog.created_at >= start_date)
    if end_date:
        q = q.where(AdminAuditLog.created_at <= end_date)
    result = await db.execute(q)
    logs = result.scalars().all()
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total": len(logs),
        "logs": [
            {
                "id": l.id,
                "admin_user_id": l.admin_user_id,
                "action": l.action,
                "target_tenant_id": l.target_tenant_id,
                "details": l.details,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
    }


# ─── Feature Flag Endpoints ───
@app.get("/admin/feature-flags")
async def list_feature_flags(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.flag_name))
    flags = result.scalars().all()
    return {
        "flags": [
            {
                "id": f.id,
                "flag_name": f.flag_name,
                "description": f.description,
                "enabled": f.enabled,
                "target_tenant_ids": f.target_tenant_ids,
            }
            for f in flags
        ]
    }


@app.post("/admin/feature-flags")
async def create_feature_flag(
    data: dict,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    flag = FeatureFlag(
        flag_name=data["flag_name"],
        description=data.get("description"),
        enabled=data.get("enabled", False),
    )
    db.add(flag)
    audit = AdminAuditLog(
        admin_user_id=admin.id,
        action="feature_flag.create",
        details={"flag_name": data["flag_name"]},
    )
    db.add(audit)
    await db.commit()
    return {"id": flag.id, "status": "created"}


@app.put("/admin/feature-flags/{flag_id}")
async def update_feature_flag(
    flag_id: str,
    data: dict,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(404, "Flag not found")
    if "enabled" in data:
        flag.enabled = data["enabled"]
    if "description" in data:
        flag.description = data["description"]
    if "target_tenant_ids" in data:
        flag.target_tenant_ids = data["target_tenant_ids"]
    await db.commit()
    return {"status": "updated"}


@app.delete("/admin/feature-flags/{flag_id}")
async def delete_feature_flag(
    flag_id: str,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == flag_id))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(404, "Flag not found")
    await db.delete(flag)
    await db.commit()
    return {"status": "deleted"}


# ─── Team Management Endpoints ───
@app.get("/admin/team")
async def list_team_members(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(AdminUser).order_by(AdminUser.created_at.desc()))
    members = result.scalars().all()
    return {
        "members": [
            {
                "id": m.id,
                "email": m.email,
                "name": m.name,
                "role": m.role,
                "is_active": m.is_active,
                "last_login_at": m.last_login_at.isoformat() if m.last_login_at else None,
            }
            for m in members
        ]
    }


@app.post("/admin/team")
async def create_team_member(
    data: dict,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    existing = await db.execute(select(AdminUser).where(AdminUser.email == data["email"]))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")
    member = AdminUser(
        email=data["email"],
        name=data["name"],
        role=data.get("role", "admin"),
        password_hash=hash_password(data["password"]),
    )
    db.add(member)
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="team.create",
        details={"email": data["email"], "role": data.get("role", "admin")},
    ))
    await db.commit()
    return {"id": member.id, "status": "created"}


@app.put("/admin/team/{member_id}")
async def update_team_member(
    member_id: str,
    data: dict,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(AdminUser).where(AdminUser.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")
    if "name" in data:
        member.name = data["name"]
    if "role" in data:
        member.role = data["role"]
    if "is_active" in data:
        member.is_active = data["is_active"]
    await db.commit()
    return {"status": "updated"}


@app.delete("/admin/team/{member_id}")
async def delete_team_member(
    member_id: str,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(AdminUser).where(AdminUser.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")
    if member.role == "super_admin":
        raise HTTPException(400, "Cannot delete super admin")
    await db.delete(member)
    await db.commit()
    return {"status": "deleted"}


# ─── API Keys Endpoints ───
@app.get("/admin/api-keys")
async def list_api_keys(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    keys = result.scalars().all()
    return {
        "keys": [
            {
                "id": k.id,
                "name": k.name,
                "key_preview": k.key_preview,
                "permissions": k.permissions,
                "rate_limit": k.rate_limit,
                "is_active": k.is_active,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "created_at": k.created_at.isoformat() if k.created_at else None,
            }
            for k in keys
        ]
    }


@app.post("/admin/api-keys")
async def create_api_key(
    data: dict,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    import secrets
    raw_key = f"pa_{secrets.token_urlsafe(32)}"
    key_obj = APIKey(
        name=data["name"],
        key_hash=hash_password(raw_key),
        key_preview=raw_key[:12] + "...",
        permissions=data.get("permissions", ["read"]),
        rate_limit=data.get("rate_limit", 100),
    )
    db.add(key_obj)
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="api_key.create",
        details={"name": data["name"]},
    ))
    await db.commit()
    return {"id": key_obj.id, "key": raw_key}


@app.delete("/admin/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(404, "Key not found")
    await db.delete(key)
    await db.commit()
    return {"status": "revoked"}


# ─── WhatsApp Monitor Endpoints ───
@app.get("/admin/whatsapp/status")
async def get_whatsapp_status(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    # Placeholder: in real impl, query each tenant's bot status
    result = await db.execute(select(Tenant).where(Tenant.status == "active"))
    tenants = result.scalars().all()
    bots = [
        {
            "tenant_id": t.id,
            "business_name": t.name,
            "phone_number": t.owner_phone,
            "status": "connected",  # placeholder
            "last_message_at": None,
            "queue_depth": 0,
            "messages_today": 0,
        }
        for t in tenants
    ]
    return {"bots": bots}


@app.post("/admin/whatsapp/{tenant_id}/reconnect")
async def force_reconnect_bot(
    tenant_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    # Placeholder: send reconnect signal to whatsapp-bot service
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="whatsapp.reconnect",
        target_tenant_id=tenant_id,
    ))
    await db.commit()
    return {"status": "reconnect_triggered"}


@app.post("/admin/whatsapp/{tenant_id}/disconnect")
async def disconnect_bot(
    tenant_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="whatsapp.disconnect",
        target_tenant_id=tenant_id,
    ))
    await db.commit()
    return {"status": "disconnected"}


# ─── Support Ticket Endpoints ───
@app.get("/admin/support/tickets")
async def list_support_tickets(
    status: str = None,
    priority: str = None,
    page: int = 1,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    q = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status:
        q = q.where(SupportTicket.status == status)
    if priority:
        q = q.where(SupportTicket.priority == priority)
    q = q.offset((page - 1) * 20).limit(20)
    result = await db.execute(q)
    tickets = result.scalars().all()
    return {
        "tickets": [
            {
                "id": t.id,
                "tenant_id": t.tenant_id,
                "subject": t.subject,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "assigned_to": t.assigned_to,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ],
        "total": len(tickets),
        "page": page,
    }


@app.get("/admin/support/tickets/{ticket_id}")
async def get_support_ticket(
    ticket_id: str,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    msgs_result = await db.execute(
        select(SupportMessage).where(SupportMessage.ticket_id == ticket_id).order_by(SupportMessage.created_at)
    )
    messages = msgs_result.scalars().all()
    return {
        "id": ticket.id,
        "tenant_id": ticket.tenant_id,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "assigned_to": ticket.assigned_to,
        "internal_notes": ticket.internal_notes,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "messages": [
            {
                "id": m.id,
                "message": m.message,
                "from_admin": m.from_admin,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@app.put("/admin/support/tickets/{ticket_id}")
async def update_support_ticket(
    ticket_id: str,
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    if "status" in data:
        ticket.status = data["status"]
    if "priority" in data:
        ticket.priority = data["priority"]
    if "assigned_to" in data:
        ticket.assigned_to = data["assigned_to"]
    if "internal_notes" in data:
        ticket.internal_notes = data["internal_notes"]
    await db.commit()
    return {"status": "updated"}


@app.post("/admin/support/tickets/{ticket_id}/reply")
async def reply_support_ticket(
    ticket_id: str,
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    msg = SupportMessage(
        ticket_id=ticket_id,
        message=data["message"],
        from_admin=True,
    )
    db.add(msg)
    # Update ticket status to in_progress
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if ticket and ticket.status == "open":
        ticket.status = "in_progress"
    await db.commit()
    return {"id": msg.id, "status": "sent"}


# ─── Notification Endpoints ───
@app.get("/admin/notifications")
async def list_notifications(
    page: int = 1,
    unread_only: bool = False,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    q = select(Notification).order_by(Notification.created_at.desc())
    if unread_only:
        q = q.where(Notification.read == False)
    q = q.offset((page - 1) * 50).limit(50)
    result = await db.execute(q)
    notifs = result.scalars().all()
    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "severity": n.severity,
                "tenant_id": n.tenant_id,
                "read": n.read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifs
        ],
        "total": len(notifs),
    }


@app.post("/admin/notifications/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Notification).where(Notification.id == notif_id))
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.read = True
    await db.commit()
    return {"status": "read"}


@app.get("/admin/notifications/settings")
async def get_notification_settings(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(NotificationSetting).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        return {
            "email_enabled": True,
            "slack_webhook": "",
            "sms_enabled": False,
            "alert_thresholds": {"high_messages": 5000, "failed_payments": 3, "ban_alerts": True},
        }
    return {
        "id": settings.id,
        "email_enabled": settings.email_enabled,
        "slack_webhook": settings.slack_webhook,
        "sms_enabled": settings.sms_enabled,
        "alert_thresholds": settings.alert_thresholds,
    }


@app.put("/admin/notifications/settings")
async def update_notification_settings(
    data: dict,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(NotificationSetting).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = NotificationSetting()
        db.add(settings)
    settings.email_enabled = data.get("email_enabled", True)
    settings.slack_webhook = data.get("slack_webhook")
    settings.sms_enabled = data.get("sms_enabled", False)
    settings.alert_thresholds = data.get("alert_thresholds", {})
    await db.commit()
    return {"status": "updated"}


# ─── Platform Webhook Endpoints ───
@app.get("/admin/webhooks")
async def list_platform_webhooks(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(PlatformWebhook).order_by(PlatformWebhook.created_at.desc()))
    webhooks = result.scalars().all()
    return {
        "webhooks": [
            {
                "id": w.id,
                "url": w.url,
                "events": w.events,
                "active": w.active,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in webhooks
        ]
    }


@app.post("/admin/webhooks")
async def create_platform_webhook(
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    webhook = PlatformWebhook(
        url=data["url"],
        events=data.get("events", []),
        secret=data.get("secret"),
    )
    db.add(webhook)
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="webhook.create",
        details={"url": data["url"]},
    ))
    await db.commit()
    return {"id": webhook.id, "status": "created"}


@app.put("/admin/webhooks/{webhook_id}")
async def update_platform_webhook(
    webhook_id: str,
    data: dict,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(PlatformWebhook).where(PlatformWebhook.id == webhook_id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(404, "Webhook not found")
    if "url" in data:
        webhook.url = data["url"]
    if "events" in data:
        webhook.events = data["events"]
    if "active" in data:
        webhook.active = data["active"]
    await db.commit()
    return {"status": "updated"}


@app.delete("/admin/webhooks/{webhook_id}")
async def delete_platform_webhook(
    webhook_id: str,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(PlatformWebhook).where(PlatformWebhook.id == webhook_id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(404, "Webhook not found")
    await db.delete(webhook)
    await db.commit()
    return {"status": "deleted"}


@app.get("/admin/webhooks/{webhook_id}/logs")
async def get_webhook_delivery_logs(
    webhook_id: str,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(
        select(WebhookDeliveryLog)
        .where(WebhookDeliveryLog.webhook_id == webhook_id)
        .order_by(WebhookDeliveryLog.created_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()
    return {
        "logs": [
            {
                "id": l.id,
                "event": l.event,
                "status_code": l.status_code,
                "error": l.error,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    }


# ─── Backup Endpoints ───
@app.get("/admin/backups")
async def list_backups(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Backup).order_by(Backup.created_at.desc()))
    backups = result.scalars().all()
    return {
        "backups": [
            {
                "id": b.id,
                "tenant_id": b.tenant_id,
                "tenant_name": b.tenant_name,
                "size_bytes": b.size_bytes,
                "type": b.type,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in backups
        ]
    }


@app.post("/admin/backups")
async def create_backup(
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    tenant_id = data.get("tenant_id")
    tenant_name = None
    size = 0
    if tenant_id:
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if tenant:
            tenant_name = tenant.name
            import os
            db_path = tenant.db_path
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
    else:
        # All tenants backup size
        import os
        from config import DATA_DIR
        tenants_dir = DATA_DIR / "tenants"
        if tenants_dir.exists():
            for f in tenants_dir.glob("*.db"):
                size += f.stat().st_size

    backup = Backup(
        tenant_id=tenant_id,
        tenant_name=tenant_name or "All Tenants",
        size_bytes=size,
        type="manual",
    )
    db.add(backup)
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="backup.create",
        target_tenant_id=tenant_id,
    ))
    await db.commit()
    return {"id": backup.id, "status": "created", "size_bytes": size}


@app.post("/admin/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(404, "Backup not found")
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="backup.restore",
        target_tenant_id=backup.tenant_id,
    ))
    await db.commit()
    return {"status": "restore_initiated"}


@app.get("/admin/backups/{backup_id}/download")
async def download_backup(
    backup_id: str,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(404, "Backup not found")
    return {
        "id": backup.id,
        "tenant_id": backup.tenant_id,
        "tenant_name": backup.tenant_name,
        "size_bytes": backup.size_bytes,
        "created_at": backup.created_at.isoformat() if backup.created_at else None,
    }


@app.delete("/admin/backups/{backup_id}")
async def delete_backup(
    backup_id: str,
    _: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Backup).where(Backup.id == backup_id))
    backup = result.scalar_one_or_none()
    if not backup:
        raise HTTPException(404, "Backup not found")
    await db.delete(backup)
    await db.commit()
    return {"status": "deleted"}


# ─── System Health Endpoints ───
@app.get("/admin/system/health")
async def get_system_health(_: AdminUser = Depends(get_current_admin)):
    import psutil
    import os

    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/" if os.name != "nt" else "C:\\")

    services = [
        {"name": "Master Backend", "port": 8010, "status": "healthy", "latency_ms": 0},
        {"name": "Backend (FastAPI)", "port": 8000, "status": "healthy" if _check_port(8000) else "down"},
        {"name": "WhatsApp Bot", "port": 8001, "status": "healthy" if _check_port(8001) else "down"},
        {"name": "PostgreSQL", "port": 5432, "status": "healthy" if _check_port(5432) else "down"},
        {"name": "Redis", "port": 6379, "status": "healthy" if _check_port(6379) else "down"},
        {"name": "Qdrant", "port": 6333, "status": "healthy" if _check_port(6333) else "down"},
    ]

    return {
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "services": services,
        "stats": {
            "uptime_24h": "99.9",
            "requests_today": 0,
            "error_rate": 0.0,
            "avg_response_ms": 0,
        },
    }


def _check_port(port: int) -> bool:
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


# ─── Reseller Endpoints ───
@app.get("/admin/resellers")
async def list_resellers(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Reseller).order_by(Reseller.created_at.desc()))
    resellers = result.scalars().all()
    return {
        "resellers": [
            {
                "id": r.id,
                "name": r.name,
                "email": r.email,
                "commission_rate": r.commission_rate,
                "is_active": r.is_active,
                "tenants_count": r.tenants_count,
                "total_commission": r.total_commission,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in resellers
        ]
    }


@app.post("/admin/resellers")
async def create_reseller(
    data: dict,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    reseller = Reseller(
        name=data["name"],
        email=data["email"],
        commission_rate=data.get("commission_rate", 30),
    )
    db.add(reseller)
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="reseller.create",
        details={"email": data["email"]},
    ))
    await db.commit()
    return {"id": reseller.id, "status": "created"}


@app.put("/admin/resellers/{reseller_id}")
async def update_reseller(
    reseller_id: str,
    data: dict,
    _: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Reseller).where(Reseller.id == reseller_id))
    reseller = result.scalar_one_or_none()
    if not reseller:
        raise HTTPException(404, "Reseller not found")
    if "name" in data:
        reseller.name = data["name"]
    if "email" in data:
        reseller.email = data["email"]
    if "commission_rate" in data:
        reseller.commission_rate = data["commission_rate"]
    if "is_active" in data:
        reseller.is_active = data["is_active"]
    await db.commit()
    return {"status": "updated"}


@app.get("/admin/resellers/{reseller_id}/payouts")
async def get_reseller_payouts(
    reseller_id: str,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(
        select(ResellerPayout)
        .where(ResellerPayout.reseller_id == reseller_id)
        .order_by(ResellerPayout.created_at.desc())
    )
    payouts = result.scalars().all()
    return {
        "payouts": [
            {
                "id": p.id,
                "amount": p.amount,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in payouts
        ]
    }


# ─── White-Label Endpoints ───
@app.get("/admin/white-label")
async def get_white_label_configs(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(WhiteLabelConfig))
    configs = result.scalars().all()
    # Enrich with tenant name
    enriched = []
    for c in configs:
        tenant_result = await db.execute(select(Tenant).where(Tenant.id == c.tenant_id))
        tenant = tenant_result.scalar_one_or_none()
        enriched.append({
            "id": c.id,
            "tenant_id": c.tenant_id,
            "tenant_name": tenant.name if tenant else "Unknown",
            "logo_url": c.logo_url,
            "primary_color": c.primary_color,
            "domain": c.domain,
            "remove_branding": c.remove_branding,
        })
    return {"configs": enriched}


@app.put("/admin/white-label/{tenant_id}")
async def update_white_label_config(
    tenant_id: str,
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(WhiteLabelConfig).where(WhiteLabelConfig.tenant_id == tenant_id))
    config = result.scalar_one_or_none()
    if not config:
        config = WhiteLabelConfig(tenant_id=tenant_id)
        db.add(config)
    if "logo_url" in data:
        config.logo_url = data["logo_url"]
    if "primary_color" in data:
        config.primary_color = data["primary_color"]
    if "domain" in data:
        config.domain = data["domain"]
    if "remove_branding" in data:
        config.remove_branding = data["remove_branding"]
    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="white_label.update",
        target_tenant_id=tenant_id,
    ))
    await db.commit()
    return {"status": "updated"}


# ─── Integration Endpoints ───
@app.get("/admin/integrations")
async def list_integrations(
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Integration).order_by(Integration.name))
    integrations = result.scalars().all()
    if not integrations:
        # Seed default integrations
        defaults = [
            {"name": "Razorpay", "category": "payments", "description": "Payment gateway", "price": 0},
            {"name": "PhonePe", "category": "payments", "description": "UPI payments", "price": 0},
            {"name": "Tally ERP", "category": "accounting", "description": "Accounting software", "price": 499},
            {"name": "Google Business", "category": "marketing", "description": "Google Business Profile", "price": 0},
            {"name": "Instagram", "category": "marketing", "description": "Instagram business", "price": 0},
            {"name": "Zoho CRM", "category": "crm", "description": "Customer relationship management", "price": 0},
            {"name": "Shopify", "category": "ecommerce", "description": "E-commerce platform", "price": 0},
            {"name": "WooCommerce", "category": "ecommerce", "description": "WordPress e-commerce", "price": 0},
            {"name": "Salesforce", "category": "crm", "description": "Enterprise CRM", "price": 999},
            {"name": "HubSpot", "category": "crm", "description": "Inbound marketing CRM", "price": 499},
            {"name": "Slack", "category": "communication", "description": "Team messaging", "price": 0},
            {"name": "Zapier", "category": "automation", "description": "5000+ app connections", "price": 0},
        ]
        for d in defaults:
            db.add(Integration(**d))
        await db.commit()
        result = await db.execute(select(Integration).order_by(Integration.name))
        integrations = result.scalars().all()

    return {
        "integrations": [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "description": i.description,
                "enabled": i.enabled,
                "price": i.price,
            }
            for i in integrations
        ]
    }


@app.put("/admin/integrations/{integration_id}")
async def toggle_integration(
    integration_id: str,
    data: dict,
    _: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_master_db),
):
    result = await db.execute(select(Integration).where(Integration.id == integration_id))
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(404, "Integration not found")
    if "enabled" in data:
        integration.enabled = data["enabled"]
    await db.commit()
    return {"status": "updated"}


# ─── Billing Enhancement: Auto-generate monthly invoices ───
@app.post("/admin/billing/generate-monthly")
async def generate_monthly_invoices(
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_master_db),
):
    now = datetime.now(timezone.utc)
    billing_period = now.strftime("%Y-%m")
    plan_prices = {"starter": 0, "growth": 999, "enterprise": 2999}

    result = await db.execute(select(Tenant).where(Tenant.status == "active"))
    tenants = result.scalars().all()
    created = 0
    for t in tenants:
        # Skip if invoice already exists for this period
        existing = await db.execute(
            select(PlatformInvoice).where(
                PlatformInvoice.tenant_id == t.id,
                PlatformInvoice.billing_period == billing_period,
            )
        )
        if existing.scalar_one_or_none():
            continue
        amount = plan_prices.get(t.plan, 0)
        if amount == 0:
            continue
        invoice = PlatformInvoice(
            tenant_id=t.id,
            amount=amount,
            plan=t.plan,
            billing_period=billing_period,
        )
        db.add(invoice)
        created += 1

    db.add(AdminAuditLog(
        admin_user_id=admin.id,
        action="billing.generate_monthly",
        details={"created": created, "period": billing_period},
    ))
    await db.commit()
    return {"status": "ok", "created": created, "period": billing_period}


# ─── Health ───
@app.get("/health")
async def health():
    return {"status": "ok", "service": "master-backend", "version": "1.0.0"}


# ─── Razorpay Webhook ───
@app.post("/api/license/razorpay-webhook")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook for async payment confirmation."""
    payload = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    if secret:
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    data = json.loads(payload)
    event = data.get("event")

    if event == "payment.captured":
        payment = data["payload"]["payment"]["entity"]
        order_id = payment.get("order_id")
        # Log successful payment — license already created by /purchase endpoint
        print(f"[WEBHOOK] Payment captured: {payment.get('id')} for order {order_id}")

    return {"status": "ok"}


# ─── License & Desktop App API ───
from routers.license import router as license_router
app.include_router(license_router)


if __name__ == "__main__":
    import uvicorn
    from config import MASTER_PORT
    uvicorn.run(app, host="0.0.0.0", port=MASTER_PORT)
