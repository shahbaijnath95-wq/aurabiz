"""
Webhook Manager — Enhanced with delivery logs, retry logic, signature verification.
Dispatches events to registered webhook endpoints with exponential backoff.
"""

import json
import time
import hashlib
import hmac
import uuid
from typing import Optional
from datetime import datetime
import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models import WebhookSubscription, WebhookDeliveryLog


class WebhookManager:
    def __init__(self, db: AsyncSession = None, http_client: httpx.AsyncClient = None):
        self.db = db
        self.client = http_client or httpx.AsyncClient(timeout=15.0)

    async def register_webhook(self, business_id: str, url: str, events: list,
                                secret: str = None) -> WebhookSubscription:
        """Register a new webhook subscription."""
        if not secret:
            secret = hashlib.sha256(uuid.uuid4().bytes).hexdigest()

        webhook = WebhookSubscription(
            business_id=business_id,
            url=url,
            events=events,
            secret=secret,
            is_active=True,
        )
        self.db.add(webhook)
        await self.db.flush()
        logger.info("Webhook registered: {} -> {} (events: {})", webhook.id, url, events)
        return webhook

    async def trigger_webhooks(self, business_id: str, event_type: str, payload: dict) -> list:
        """Trigger all matching webhooks for an event."""
        result = await self.db.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.business_id == business_id,
                WebhookSubscription.is_active == True,
            )
        )
        webhooks = result.scalars().all()
        results = []

        for webhook in webhooks:
            if event_type in webhook.events or "*" in webhook.events:
                delivery_result = await self._deliver(webhook, event_type, payload)
                results.append(delivery_result)

        return results

    async def _deliver(self, webhook: WebhookSubscription, event_type: str,
                        payload: dict, attempt: int = 1) -> dict:
        """Deliver a webhook with retry logic and logging."""
        delivery_id = str(uuid.uuid4())
        start_time = time.time()

        # Create delivery log
        log = WebhookDeliveryLog(
            id=delivery_id,
            webhook_id=webhook.id,
            business_id=webhook.business_id,
            event_type=event_type,
            url=webhook.url,
            payload=payload,
            status="pending",
            attempts=attempt,
            max_retries=3,
        )
        self.db.add(log)

        try:
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Event": event_type,
                "X-Webhook-Delivery": delivery_id,
                "X-Webhook-Timestamp": str(int(time.time())),
            }

            # HMAC signature verification
            if webhook.secret:
                body_str = json.dumps(payload, default=str, sort_keys=True)
                signature = hmac.new(
                    webhook.secret.encode(),
                    body_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            # Send request
            resp = await self.client.post(
                webhook.url,
                json=payload,
                headers=headers,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            log.status_code = resp.status_code
            log.duration_ms = duration_ms
            log.response_body = resp.text[:1000] if resp.text else ""

            if 200 <= resp.status_code < 300:
                log.status = "delivered"
                log.delivered_at = datetime.utcnow()
                webhook.last_triggered_at = datetime.utcnow()
                webhook.failure_count = 0
                logger.info("Webhook delivered: {} -> {} ({}ms)", event_type, webhook.url, duration_ms)
            else:
                log.status = "failed"
                log.error_message = f"HTTP {resp.status_code}"
                webhook.failure_count = (webhook.failure_count or 0) + 1
                logger.warning("Webhook failed: {} -> {} (HTTP {})", event_type, webhook.url, resp.status_code)

                # Retry with exponential backoff
                if attempt < 3:
                    return await self._retry_delivery(webhook, event_type, payload, log, attempt)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log.status = "failed"
            log.duration_ms = duration_ms
            log.error_message = str(e)[:500]
            webhook.failure_count = (webhook.failure_count or 0) + 1
            logger.error("Webhook delivery error: {} -> {}: {}", event_type, webhook.url, e)

            # Retry on connection errors
            if attempt < 3:
                return await self._retry_delivery(webhook, event_type, payload, log, attempt)

        await self.db.flush()
        return {
            "webhook_id": webhook.id,
            "delivery_id": delivery_id,
            "status": log.status,
            "status_code": log.status_code,
            "attempts": log.attempts,
        }

    async def _retry_delivery(self, webhook: WebhookSubscription, event_type: str,
                               payload: dict, log: WebhookDeliveryLog, attempt: int) -> dict:
        """Retry webhook delivery with exponential backoff."""
        import asyncio
        delay = 2 ** attempt  # 2s, 4s
        log.status = "retrying"
        log.attempts = attempt + 1
        await self.db.flush()

        logger.info("Retrying webhook in {}s (attempt {}/{})", delay, attempt + 1, 3)
        await asyncio.sleep(delay)

        return await self._deliver(webhook, event_type, payload, attempt + 1)

    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook HMAC signature."""
        if not secret or not signature:
            return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    async def get_delivery_logs(self, webhook_id: str, limit: int = 50) -> list:
        """Get delivery logs for a webhook."""
        result = await self.db.execute(
            select(WebhookDeliveryLog).where(
                WebhookDeliveryLog.webhook_id == webhook_id
            ).order_by(desc(WebhookDeliveryLog.created_at)).limit(limit)
        )
        logs = result.scalars().all()
        return [
            {
                "id": log.id,
                "event_type": log.event_type,
                "url": log.url,
                "status": log.status,
                "status_code": log.status_code,
                "attempts": log.attempts,
                "duration_ms": log.duration_ms,
                "error_message": log.error_message,
                "created_at": str(log.created_at),
                "delivered_at": str(log.delivered_at) if log.delivered_at else None,
            }
            for log in logs
        ]

    async def retry_delivery(self, webhook_id: str, delivery_id: str = None) -> bool:
        """Manually retry a failed delivery."""
        query = select(WebhookDeliveryLog).where(
            WebhookDeliveryLog.webhook_id == webhook_id,
            WebhookDeliveryLog.status == "failed",
        )
        if delivery_id:
            query = query.where(WebhookDeliveryLog.id == delivery_id)

        result = await self.db.execute(query.order_by(desc(WebhookDeliveryLog.created_at)).limit(1))
        log = result.scalar_one_or_none()
        if not log:
            return False

        # Get the webhook
        wb_result = await self.db.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
        )
        webhook = wb_result.scalar_one_or_none()
        if not webhook:
            return False

        await self._deliver(webhook, log.event_type, log.payload)
        return True

    async def replay_events(self, webhook_id: str, start_time: str, end_time: str) -> int:
        """Replay events within a time range."""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)

            result = await self.db.execute(
                select(WebhookDeliveryLog).where(
                    WebhookDeliveryLog.webhook_id == webhook_id,
                    WebhookDeliveryLog.created_at >= start,
                    WebhookDeliveryLog.created_at <= end,
                )
            )
            logs = result.scalars().all()

            # Get webhook
            wb_result = await self.db.execute(
                select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
            )
            webhook = wb_result.scalar_one_or_none()
            if not webhook:
                return 0

            count = 0
            for log in logs:
                await self._deliver(webhook, log.event_type, log.payload)
                count += 1

            return count
        except Exception as e:
            logger.error("Replay error: {}", e)
            return 0

    async def get_webhook_stats(self, business_id: str) -> dict:
        """Get webhook delivery statistics."""
        try:
            # Total webhooks
            total_result = await self.db.execute(
                select(func.count(WebhookSubscription.id)).where(
                    WebhookSubscription.business_id == business_id
                )
            )
            total = total_result.scalar() or 0

            # Active webhooks
            active_result = await self.db.execute(
                select(func.count(WebhookSubscription.id)).where(
                    WebhookSubscription.business_id == business_id,
                    WebhookSubscription.is_active == True,
                )
            )
            active = active_result.scalar() or 0

            # Delivery stats (last 7 days)
            from sqlalchemy import func
            week_ago = datetime.utcnow() - timedelta(days=7)
            delivery_result = await self.db.execute(
                select(
                    func.count(WebhookDeliveryLog.id).label("total"),
                    func.count(case(
                        (WebhookDeliveryLog.status == "delivered", 1)
                    )).label("delivered"),
                    func.count(case(
                        (WebhookDeliveryLog.status == "failed", 1)
                    )).label("failed"),
                ).where(
                    WebhookDeliveryLog.business_id == business_id,
                    WebhookDeliveryLog.created_at >= week_ago,
                )
            )
            d_row = delivery_result.one_or_none()

            return {
                "total_webhooks": total,
                "active_webhooks": active,
                "delivery_7d": {
                    "total": d_row.total if d_row else 0,
                    "delivered": d_row.delivered if d_row else 0,
                    "failed": d_row.failed if d_row else 0,
                    "success_rate": round(
                        (d_row.delivered / d_row.total * 100) if d_row and d_row.total else 0, 1
                    ),
                },
            }
        except Exception as e:
            logger.error("Webhook stats error: {}", e)
            return {"total_webhooks": 0, "active_webhooks": 0, "delivery_7d": {}}
