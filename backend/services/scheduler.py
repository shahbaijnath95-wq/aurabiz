"""
Background Scheduler — Dispatches pending follow-ups and scheduled messages.

Runs as a background asyncio task started in main.py lifespan.
Polls every 60 seconds for due items and dispatches them.
"""
import asyncio
from datetime import datetime, timezone
from loguru import logger
import httpx
import os

# WhatsApp bot HTTP bridge. Env-driven so Docker networking works.
BOT_URL = os.getenv("BOT_URL", "http://127.0.0.1:8001")
BOT_API_KEY = os.getenv("BOT_API_KEY", "") or None


async def _send_whatsapp(phone: str, message: str) -> bool:
    """Send a WhatsApp message through the bot bridge."""
    if not phone or not message:
        return False
    payload = {"phone": phone, "message": message}
    headers = {}
    if BOT_API_KEY:
        headers["Authorization"] = f"Bearer {BOT_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{BOT_URL}/send", json=payload, headers=headers)
            return r.status_code == 200
    except Exception as e:
        logger.error(f"Bot send failed for {phone}: {e}")
        return False


async def dispatch_pending_followups():
    """Find and send due follow-ups via WhatsApp."""
    try:
        from database import async_session
        from services.followup_service import FollowUpService
        from models import FollowUp, Customer
        from sqlalchemy import select

        async with async_session() as db:
            svc = FollowUpService(db)
            pending = await svc.get_pending_followups(business_id=None)
            sent = 0
            for fu in pending:
                try:
                    phone = None
                    if fu.customer_id:
                        cust_result = await db.execute(
                            select(Customer).where(Customer.id == fu.customer_id)
                        )
                        customer = cust_result.scalar_one_or_none()
                        phone = customer.phone_number if customer else None

                    ok = await _send_whatsapp(phone, fu.message_template)
                    if ok:
                        await svc.mark_sent(fu.id)
                        sent += 1
                        logger.info(f"Follow-up {fu.id} sent via WhatsApp")
                    else:
                        await svc.mark_failed(fu.id, "Bot send failed (unreachable or rejected)")
                        logger.warning(f"Follow-up {fu.id} send failed")
                except Exception as e:
                    logger.error(f"Follow-up {fu.id} dispatch failed: {e}")
                    await svc.mark_failed(fu.id, str(e))
            if sent:
                logger.info(f"Dispatched {sent} follow-ups")
    except Exception as e:
        logger.error(f"Follow-up dispatch error: {e}")


async def dispatch_pending_scheduled_messages():
    """Find and send due scheduled messages via WhatsApp."""
    try:
        from database import async_session
        from services.scheduled_message_service import ScheduledMessageService
        from models import ScheduledMessage, Customer
        from sqlalchemy import select

        async with async_session() as db:
            svc = ScheduledMessageService(db)
            pending = await svc.get_pending_messages(business_id=None)
            sent = 0
            for msg in pending:
                try:
                    phone = None
                    if msg.customer_id:
                        cust_result = await db.execute(
                            select(Customer).where(Customer.id == msg.customer_id)
                        )
                        customer = cust_result.scalar_one_or_none()
                        phone = customer.phone_number if customer else None

                    ok = await _send_whatsapp(phone, msg.content)
                    if ok:
                        await svc.mark_sent(msg.id)
                        sent += 1
                        logger.info(f"Scheduled message {msg.id} sent via WhatsApp")
                    else:
                        await svc.mark_failed(msg.id, "Bot send failed (unreachable or rejected)")
                        logger.warning(f"Scheduled message {msg.id} send failed")
                except Exception as e:
                    logger.error(f"Scheduled message {msg.id} dispatch failed: {e}")
                    await svc.mark_failed(msg.id, str(e))
            if sent:
                logger.info(f"Dispatched {sent} scheduled messages")
    except Exception as e:
        logger.error(f"Scheduled message dispatch error: {e}")


async def check_inventory_alerts():
    """Periodically check for low-stock and out-of-stock alerts."""
    try:
        from database import async_session
        from services.inventory_alert_service import InventoryAlertService
        from models import Business
        from sqlalchemy import select

        async with async_session() as db:
            svc = InventoryAlertService(db)
            result = await db.execute(select(Business.id))
            business_ids = [r[0] for r in result.all()]
            total_alerts = 0
            for biz_id in business_ids:
                try:
                    stats = await svc.check_stock_alerts(biz_id)
                    total_alerts += stats.get("alerts", 0)
                except Exception:
                    pass
            if total_alerts:
                logger.info(f"Created {total_alerts} inventory alerts")
    except Exception as e:
        logger.error(f"Inventory alert check error: {e}")


async def scheduler_loop():
    """Main scheduler loop — runs every 60 seconds."""
    logger.info("Background scheduler started")
    while True:
        try:
            await asyncio.gather(
                dispatch_pending_followups(),
                dispatch_pending_scheduled_messages(),
                check_inventory_alerts(),
                return_exceptions=True,
            )
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
        await asyncio.sleep(60)


_scheduler_task = None


def start_scheduler():
    """Start the background scheduler task."""
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(scheduler_loop())
        logger.info("Background scheduler task created")


def stop_scheduler():
    """Stop the background scheduler task."""
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        logger.info("Background scheduler stopped")
