"""
Webhooks Router — CRUD, delivery logs, retry, replay, stats.
Enhanced with delivery tracking and exponential backoff retry.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database import get_db
from auth import get_current_user, verify_business_access
from models import User, WebhookSubscription
from schemas import WebhookCreate, SuccessResponse
from services.webhook_manager import WebhookManager

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.post("/register")
async def register_webhook(
    data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    wm = WebhookManager(db)
    webhook = await wm.register_webhook(data.business_id, data.url, data.events)
    return {"status": "registered", "webhook_id": webhook.id, "secret": webhook.secret}


@router.get("/")
async def list_webhooks(
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.business_id == business_id)
    )
    webhooks = result.scalars().all()
    return {
        "webhooks": [
            {
                "id": w.id,
                "url": w.url,
                "events": w.events,
                "is_active": w.is_active,
                "failure_count": w.failure_count,
                "last_triggered_at": str(w.last_triggered_at) if w.last_triggered_at else None,
                "created_at": str(w.created_at) if w.created_at else None,
            }
            for w in webhooks
        ]
    }


@router.put("/{id}")
async def update_webhook(
    id: str,
    url: str = Query(None),
    events: list[str] = Query(None),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook nahi mila")
    if not await verify_business_access(current_user, webhook.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    if url:
        webhook.url = url
    if events:
        webhook.events = events
    if is_active is not None:
        webhook.is_active = is_active
    await db.flush()
    return {"status": "updated"}


@router.delete("/{id}")
async def delete_webhook(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook nahi mila")
    if not await verify_business_access(current_user, webhook.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(webhook)
    await db.flush()
    return {"status": "deleted"}


@router.post("/{id}/test")
async def test_webhook(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a test event to the webhook."""
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook nahi mila")
    if not await verify_business_access(current_user, webhook.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    wm = WebhookManager(db)
    result = await wm.trigger_webhooks(
        business_id=webhook.business_id,
        event_type="webhook.test",
        payload={
            "event": "webhook.test",
            "message": "Test webhook from WhatsApp Business Assistant",
            "timestamp": str(__import__('datetime').datetime.utcnow()),
        },
    )
    return {"status": "tested", "webhook_id": id, "results": result}


@router.get("/{id}/logs")
async def get_delivery_logs(
    id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get delivery logs for a webhook."""
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook nahi mila")
    if not await verify_business_access(current_user, webhook.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    wm = WebhookManager(db)
    logs = await wm.get_delivery_logs(id, limit)
    return {"logs": logs}


@router.post("/{id}/retry")
async def retry_webhook(
    id: str,
    delivery_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually retry a failed webhook delivery."""
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook nahi mila")
    if not await verify_business_access(current_user, webhook.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    wm = WebhookManager(db)
    success = await wm.retry_delivery(id, delivery_id)
    if not success:
        raise HTTPException(status_code=404, detail="No failed delivery found")
    return {"status": "retrying", "webhook_id": id}


@router.post("/replay/{id}")
async def replay_events(
    id: str,
    start_time: str = Query(...),
    end_time: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Replay events within a time range."""
    result = await db.execute(select(WebhookSubscription).where(WebhookSubscription.id == id))
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook nahi mila")
    if not await verify_business_access(current_user, webhook.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    wm = WebhookManager(db)
    count = await wm.replay_events(id, start_time, end_time)
    return {"replayed": count}


@router.get("/stats/{business_id}")
async def get_webhook_stats(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get webhook delivery statistics."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    wm = WebhookManager(db)
    stats = await wm.get_webhook_stats(business_id)
    return stats
