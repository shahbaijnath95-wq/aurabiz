"""Business settings management - invoice, AI, payments, profile."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from database import get_db
from models import BusinessSettings, User
from auth import get_current_user, verify_business_access

router = APIRouter(prefix="/api/v1", tags=["settings"])


# ── Pydantic schemas ──

class InvoiceSettings(BaseModel):
    business_name: Optional[str] = ""
    gst_number: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    bank_name: Optional[str] = ""
    account_number: Optional[str] = ""
    ifsc_code: Optional[str] = ""
    upi_id: Optional[str] = ""
    terms: Optional[str] = ""


class AISettings(BaseModel):
    provider: Optional[str] = "openrouter"
    api_key: Optional[str] = ""
    model: Optional[str] = ""
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    system_prompt: Optional[str] = ""
    voice_orders_enabled: Optional[bool] = False


class PaymentSettings(BaseModel):
    razorpay_key: Optional[str] = ""
    razorpay_secret: Optional[str] = ""
    phonepe_merchant_id: Optional[str] = ""
    phonepe_secret_key: Optional[str] = ""
    default_upi_id: Optional[str] = ""
    auto_collect: Optional[bool] = False


class BusinessProfile(BaseModel):
    name: Optional[str] = ""
    type: Optional[str] = ""
    phone_number: Optional[str] = ""
    address: Optional[str] = ""
    email: Optional[str] = ""
    website: Optional[str] = ""
    logo_url: Optional[str] = ""


class BusinessHoursSettings(BaseModel):
    enabled: Optional[bool] = True
    open_hour: Optional[int] = 10
    close_hour: Optional[int] = 20
    days: Optional[list] = [1, 2, 3, 4, 5, 6]
    timezone: Optional[str] = "Asia/Kolkata"
    closed_message: Optional[str] = ""


# ── DB helpers ──

async def get_setting(db: AsyncSession, business_id: str, section: str) -> dict:
    result = await db.execute(
        select(BusinessSettings).where(
            BusinessSettings.business_id == business_id,
            BusinessSettings.section == section,
        )
    )
    row = result.scalar_one_or_none()
    return row.data if row else {}


async def save_setting(db: AsyncSession, business_id: str, section: str, data: dict):
    result = await db.execute(
        select(BusinessSettings).where(
            BusinessSettings.business_id == business_id,
            BusinessSettings.section == section,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.data = data
    else:
        row = BusinessSettings(business_id=business_id, section=section, data=data)
        db.add(row)
    await db.commit()


async def get_business_id_from_user(user: User, db: AsyncSession) -> str:
    """Extract business_id from user — query DB directly (async-safe)."""
    from models import Business
    result = await db.execute(select(Business).where(Business.user_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Koi business nahi mila. Pehle business banao.")
    return business.id


# ── GET endpoints (read-only, no auth required for public display) ──

@router.get("/settings")
async def get_all_settings(business_id: str = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not business_id:
        return {}
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        result = await db.execute(
            select(BusinessSettings).where(BusinessSettings.business_id == business_id)
        )
        rows = result.scalars().all()
        return {row.section: row.data for row in rows}
    except Exception:
        return {}


@router.get("/settings/{section}")
async def get_settings(section: str, business_id: str = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not business_id:
        return {}
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        return await get_setting(db, business_id, section)
    except Exception:
        return {}


# ── PUT endpoints (auth required) ──

@router.put("/settings/invoice")
async def update_invoice_settings(
    req: InvoiceSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business_id = await get_business_id_from_user(current_user, db)
    await save_setting(db, business_id, "invoice", req.model_dump())
    return {"status": "updated"}


@router.put("/settings/ai")
async def update_ai_settings(
    req: AISettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business_id = await get_business_id_from_user(current_user, db)
    await save_setting(db, business_id, "ai", req.model_dump())
    return {"status": "updated"}


@router.put("/settings/payments")
async def update_payment_settings(
    req: PaymentSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business_id = await get_business_id_from_user(current_user, db)
    await save_setting(db, business_id, "payments", req.model_dump())
    return {"status": "updated"}


@router.put("/settings/profile")
async def update_profile_settings(
    req: BusinessProfile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business_id = await get_business_id_from_user(current_user, db)
    await save_setting(db, business_id, "profile", req.model_dump())
    return {"status": "updated"}


@router.put("/settings/business-hours")
async def update_business_hours(
    req: BusinessHoursSettings,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business_id = await get_business_id_from_user(current_user, db)
    hours_data = req.model_dump()
    await save_setting(db, business_id, "business_hours", hours_data)

    # Also update bot_config.json so bot picks up changes immediately
    try:
        import json
        import os
        bot_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "whatsapp-bot", "bot_config.json")
        bot_cfg = {}
        if os.path.exists(bot_config_path):
            with open(bot_config_path, "r", encoding="utf-8") as f:
                bot_cfg = json.load(f)

        bot_cfg["business_hours"] = {
            "enabled": hours_data["enabled"],
            "start_hour": hours_data["open_hour"],
            "end_hour": hours_data["close_hour"],
            "days": hours_data["days"],
            "timezone": hours_data["timezone"],
        }
        if hours_data.get("closed_message"):
            bot_cfg["business_hours"]["closed_message"] = hours_data["closed_message"]

        with open(bot_config_path, "w", encoding="utf-8") as f:
            json.dump(bot_cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Bot config update error: {}", e)

    return {"status": "updated"}


@router.put("/settings/{section}")
async def update_settings(
    section: str,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    business_id = await get_business_id_from_user(current_user, db)
    await save_setting(db, business_id, section, data)
    return {"status": "updated", "section": section}
