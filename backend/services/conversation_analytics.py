"""
Conversation Analytics Service — Message stats, customer engagement, conversation insights.
Tracks message volumes, response times, sentiment distribution, and active conversations.
"""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case, and_
from loguru import logger

from models import (
    WhatsAppMessage, Conversation, Customer, Order,
    Transaction, MessageDirection, ConversationStatus
)


class ConversationAnalytics:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversation_stats(self, business_id: str, days: int = 30) -> dict:
        """Get comprehensive conversation analytics."""
        since = datetime.utcnow() - timedelta(days=days)

        try:
            # Message counts by direction
            msg_result = await self.db.execute(
                select(
                    func.count(WhatsAppMessage.id).label("total"),
                    func.count(case(
                        (WhatsAppMessage.direction == MessageDirection.INBOUND, 1)
                    )).label("inbound"),
                    func.count(case(
                        (WhatsAppMessage.direction == MessageDirection.OUTBOUND, 1)
                    )).label("outbound"),
                ).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.created_at >= since,
                )
            )
            msg_row = msg_result.one_or_none()

            # Unique customers who messaged
            unique_result = await self.db.execute(
                select(func.count(func.distinct(WhatsAppMessage.customer_id))).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.direction == MessageDirection.INBOUND,
                    WhatsAppMessage.created_at >= since,
                )
            )
            unique_customers = unique_result.scalar() or 0

            # Active conversations
            conv_result = await self.db.execute(
                select(func.count(Conversation.id)).where(
                    Conversation.business_id == business_id,
                    Conversation.status == ConversationStatus.OPEN,
                )
            )
            active_conversations = conv_result.scalar() or 0

            # Message type breakdown
            type_result = await self.db.execute(
                select(
                    WhatsAppMessage.message_type,
                    func.count(WhatsAppMessage.id).label("count"),
                ).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.created_at >= since,
                ).group_by(WhatsAppMessage.message_type)
            )
            message_types = {row[0]: row[1] for row in type_result.all()}

            # Messages per day trend
            daily_trend = await self._get_daily_message_trend(business_id, since)

            # Response time (approximate — time between inbound and next outbound)
            avg_response_time = await self._estimate_avg_response_time(business_id, since)

            return {
                "period_days": days,
                "total_messages": msg_row.total if msg_row else 0,
                "inbound_messages": msg_row.inbound if msg_row else 0,
                "outbound_messages": msg_row.outbound if msg_row else 0,
                "unique_customers": unique_customers,
                "active_conversations": active_conversations,
                "message_types": message_types,
                "daily_trend": daily_trend,
                "avg_response_time_seconds": avg_response_time,
                "response_rate": self._calc_response_rate(
                    msg_row.inbound if msg_row else 0,
                    msg_row.outbound if msg_row else 0,
                ),
            }
        except Exception as e:
            logger.error("Conversation stats error: {}", e)
            return self._empty_stats(days)

    async def get_customer_engagement(self, business_id: str, days: int = 30) -> dict:
        """Get customer engagement metrics."""
        since = datetime.utcnow() - timedelta(days=days)

        try:
            # Top active customers
            top_result = await self.db.execute(
                select(
                    WhatsAppMessage.customer_id,
                    func.count(WhatsAppMessage.id).label("msg_count"),
                ).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.direction == MessageDirection.INBOUND,
                    WhatsAppMessage.created_at >= since,
                ).group_by(WhatsAppMessage.customer_id)
                .order_by(desc(func.count(WhatsAppMessage.id)))
                .limit(10)
            )
            top_customers = [
                {"customer_id": row[0], "message_count": row[1]}
                for row in top_result.all()
            ]

            # New vs returning customers
            new_result = await self.db.execute(
                select(func.count(Customer.id)).where(
                    Customer.business_id == business_id,
                    Customer.created_at >= since,
                )
            )
            new_customers = new_result.scalar() or 0

            total_result = await self.db.execute(
                select(func.count(Customer.id)).where(
                    Customer.business_id == business_id,
                )
            )
            total_customers = total_result.scalar() or 0

            # Hourly distribution (when customers message most)
            hourly = await self._get_hourly_distribution(business_id, since)

            return {
                "period_days": days,
                "total_customers": total_customers,
                "new_customers": new_customers,
                "returning_customers": total_customers - new_customers,
                "top_customers": top_customers,
                "hourly_distribution": hourly,
            }
        except Exception as e:
            logger.error("Customer engagement error: {}", e)
            return {"period_days": days, "total_customers": 0, "new_customers": 0,
                    "returning_customers": 0, "top_customers": [], "hourly_distribution": []}

    async def get_sentiment_summary(self, business_id: str, days: int = 30) -> dict:
        """
        Analyze sentiment distribution from message content.
        Simple keyword-based — no external AI dependency.
        """
        since = datetime.utcnow() - timedelta(days=days)

        try:
            result = await self.db.execute(
                select(WhatsAppMessage.content).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.direction == MessageDirection.INBOUND,
                    WhatsAppMessage.created_at >= since,
                ).limit(500)
            )
            messages = [row[0] for row in result.all() if row[0]]

            positive_words = [
                "accha", "badhiya", "shukriya", "dhanyavaad", "great", "good", "nice",
                "happy", "best", "love", "amazing", "awesome", "perfect", "thanks",
                "bilkul", "zaroor", "sure", "theek", "sahi", "wah", "mast", "jhakas"
            ]
            negative_words = [
                "kharab", "bura", "pareshan", "angry", "bad", "problem", "gussa",
                "worst", "hate", "terrible", "horrible", "slow", "late", "broken",
                "defect", "refund", "complaint", "disappointed", "frustrated"
            ]

            pos = neg = neutral = 0
            for msg in messages:
                lower = msg.lower()
                has_pos = any(w in lower for w in positive_words)
                has_neg = any(w in lower for w in negative_words)
                if has_pos and not has_neg:
                    pos += 1
                elif has_neg and not has_pos:
                    neg += 1
                else:
                    neutral += 1

            total = pos + neg + neutral
            return {
                "total_analyzed": total,
                "positive": pos,
                "negative": neg,
                "neutral": neutral,
                "positive_pct": round(pos / total * 100, 1) if total else 0,
                "negative_pct": round(neg / total * 100, 1) if total else 0,
                "neutral_pct": round(neutral / total * 100, 1) if total else 0,
            }
        except Exception as e:
            logger.error("Sentiment summary error: {}", e)
            return {"total_analyzed": 0, "positive": 0, "negative": 0, "neutral": 0,
                    "positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}

    async def get_intent_distribution(self, business_id: str, days: int = 30) -> dict:
        """Classify inbound messages by intent keywords."""
        since = datetime.utcnow() - timedelta(days=days)

        intent_keywords = {
            "pricing": ["price", "kitna", "rate", "dam", "cost", "paisa", "charge", "fee"],
            "order": ["order", "buy", "kharid", "lena", "purchase", "booking"],
            "inquiry": ["hai", "available", "stock", "kya", "kaise", "batao", "info"],
            "complaint": ["problem", "issue", "gussa", "kharab", "broken", "refund"],
            "support": ["help", "madad", "support", "repair", "fix"],
            "payment": ["pay", "payment", "bill", "upi", "paise", "transfer"],
            "feedback": ["feedback", "review", "rating", "accha", "bura", "suggestion"],
        }

        try:
            result = await self.db.execute(
                select(WhatsAppMessage.content).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.direction == MessageDirection.INBOUND,
                    WhatsAppMessage.created_at >= since,
                ).limit(1000)
            )
            messages = [row[0] for row in result.all() if row[0]]

            counts = {k: 0 for k in intent_keywords}
            counts["general"] = 0

            for msg in messages:
                lower = msg.lower()
                matched = False
                for intent, keywords in intent_keywords.items():
                    if any(kw in lower for kw in keywords):
                        counts[intent] += 1
                        matched = True
                        break
                if not matched:
                    counts["general"] += 1

            total = len(messages)
            return {
                "total_messages": total,
                "intents": {
                    k: {"count": v, "pct": round(v / total * 100, 1) if total else 0}
                    for k, v in counts.items()
                },
            }
        except Exception as e:
            logger.error("Intent distribution error: {}", e)
            return {"total_messages": 0, "intents": {}}

    async def get_full_analytics(self, business_id: str, days: int = 30) -> dict:
        """Get all conversation analytics combined."""
        stats = await self.get_conversation_stats(business_id, days)
        engagement = await self.get_customer_engagement(business_id, days)
        sentiment = await self.get_sentiment_summary(business_id, days)
        intents = await self.get_intent_distribution(business_id, days)

        return {
            "conversation_stats": stats,
            "customer_engagement": engagement,
            "sentiment": sentiment,
            "intent_distribution": intents,
        }

    async def _get_daily_message_trend(self, business_id: str, since: datetime) -> list:
        """Get daily message counts for chart."""
        try:
            result = await self.db.execute(
                select(
                    func.date(WhatsAppMessage.created_at).label("day"),
                    func.count(WhatsAppMessage.id).label("count"),
                ).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.created_at >= since,
                ).group_by(func.date(WhatsAppMessage.created_at))
                .order_by(func.date(WhatsAppMessage.created_at))
            )
            return [
                {"date": str(row[0]), "messages": row[1]}
                for row in result.all()
            ]
        except Exception:
            return []

    async def _estimate_avg_response_time(self, business_id: str, since: datetime) -> float:
        """Estimate average response time in seconds (inbound → next outbound)."""
        try:
            # Get inbound messages with their timestamps
            inbound = await self.db.execute(
                select(WhatsAppMessage.created_at).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.direction == MessageDirection.INBOUND,
                    WhatsAppMessage.created_at >= since,
                ).order_by(WhatsAppMessage.created_at).limit(200)
            )
            inbound_times = [row[0] for row in inbound.all()]

            if not inbound_times:
                return 0.0

            # Get outbound messages
            outbound = await self.db.execute(
                select(WhatsAppMessage.created_at).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.direction == MessageDirection.OUTBOUND,
                    WhatsAppMessage.created_at >= since,
                ).order_by(WhatsAppMessage.created_at).limit(200)
            )
            outbound_times = [row[0] for row in outbound.all()]

            if not outbound_times:
                return 0.0

            # Simple matching: for each inbound, find next outbound
            total_seconds = 0
            count = 0
            for in_time in inbound_times[:50]:
                for out_time in outbound_times:
                    if out_time > in_time:
                        diff = (out_time - in_time).total_seconds()
                        if diff < 3600:  # Ignore if > 1 hour
                            total_seconds += diff
                            count += 1
                        break

            return round(total_seconds / count, 1) if count > 0 else 0.0
        except Exception:
            return 0.0

    async def _get_hourly_distribution(self, business_id: str, since: datetime) -> list:
        """Get hourly message distribution (0-23 hours)."""
        try:
            result = await self.db.execute(
                select(
                    func.strftime("%H", WhatsAppMessage.created_at).label("hour"),
                    func.count(WhatsAppMessage.id).label("count"),
                ).where(
                    WhatsAppMessage.business_id == business_id,
                    WhatsAppMessage.direction == MessageDirection.INBOUND,
                    WhatsAppMessage.created_at >= since,
                ).group_by(func.strftime("%H", WhatsAppMessage.created_at))
                .order_by(func.strftime("%H", WhatsAppMessage.created_at))
            )
            return [
                {"hour": int(row[0]), "messages": row[1]}
                for row in result.all()
            ]
        except Exception:
            return []

    def _calc_response_rate(self, inbound: int, outbound: int) -> float:
        if inbound == 0:
            return 0.0
        return round(min(outbound / inbound, 1.0) * 100, 1)

    def _empty_stats(self, days: int) -> dict:
        return {
            "period_days": days,
            "total_messages": 0,
            "inbound_messages": 0,
            "outbound_messages": 0,
            "unique_customers": 0,
            "active_conversations": 0,
            "message_types": {},
            "daily_trend": [],
            "avg_response_time_seconds": 0.0,
            "response_rate": 0.0,
        }
