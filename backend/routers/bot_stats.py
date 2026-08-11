"""Bot stats - message counts, recent messages."""

import os
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from database import get_db
from auth import get_current_user, verify_business_access
from models import User
from models import WhatsAppMessage

router = APIRouter(prefix="/api/v1", tags=["bot_stats"])


@router.get("/bot/stats/{business_id}")
async def get_bot_stats(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's messages
    today_result = await db.execute(
        select(func.count()).where(
            WhatsAppMessage.business_id == business_id,
            WhatsAppMessage.created_at >= today,
        )
    )
    today_total = today_result.scalar() or 0

    # Today inbound
    today_inbound = await db.execute(
        select(func.count()).where(
            WhatsAppMessage.business_id == business_id,
            WhatsAppMessage.created_at >= today,
            WhatsAppMessage.direction == "inbound",
        )
    )
    today_in = today_inbound.scalar() or 0

    # Today outbound
    today_outbound = await db.execute(
        select(func.count()).where(
            WhatsAppMessage.business_id == business_id,
            WhatsAppMessage.created_at >= today,
            WhatsAppMessage.direction == "outbound",
        )
    )
    today_out = today_outbound.scalar() or 0

    # Total messages
    total_result = await db.execute(
        select(func.count()).where(WhatsAppMessage.business_id == business_id)
    )
    total_all = total_result.scalar() or 0

    # Recent messages (last 20)
    recent = await db.execute(
        select(WhatsAppMessage)
        .where(WhatsAppMessage.business_id == business_id)
        .order_by(desc(WhatsAppMessage.created_at))
        .limit(20)
    )
    messages = [
        {
            "id": m.id,
            "content": m.content,
            "direction": m.direction,
            "sender": m.customer_id or "",
            "created_at": str(m.created_at) if m.created_at else "",
        }
        for m in recent.scalars().all()
    ]

    return {
        "today_total": today_total,
        "today_inbound": today_in,
        "today_outbound": today_out,
        "total_messages": total_all,
        "recent_messages": messages,
    }

