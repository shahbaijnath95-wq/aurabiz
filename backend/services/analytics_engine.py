from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from models import Transaction, Customer, Product, Order, WhatsAppMessage


class AnalyticsEngine:
    def __init__(self, db: AsyncSession = None, redis=None):
        self.db = db
        self.redis = redis

    async def get_dashboard(self, business_id: str) -> dict:
        cache_key = f"dashboard:{business_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    import json
                    return json.loads(cached)
            except Exception:
                pass

        stat_cards = await self._get_stat_cards(business_id)
        revenue_chart = await self._get_revenue_chart(business_id)
        customer_metrics = await self._get_customer_metrics(business_id)
        top_products = await self._get_top_products(business_id)
        customer_segments = await self._get_customer_segments(business_id)
        recent_transactions = await self._get_recent_transactions(business_id)
        activity_feed = await self._get_activity_feed(business_id)
        ai_insights = await self.generate_insights(business_id)

        dashboard = {
            "stat_cards": stat_cards,
            "revenue_chart": revenue_chart,
            "customer_metrics": customer_metrics,
            "top_products": top_products,
            "revenue_forecast": [],
            "customer_segments": customer_segments,
            "recent_transactions": recent_transactions,
            "activity_feed": activity_feed,
            "ai_insights": ai_insights,
        }

        if self.redis:
            try:
                import json
                await self.redis.set(cache_key, json.dumps(dashboard, default=str), ex=300)
            except Exception:
                pass

        return dashboard

    async def _get_stat_cards(self, business_id: str) -> dict:
        if not self.db:
            return {
                "revenue": {"value": 0, "change": 0, "trend": "up"},
                "orders": {"value": 0, "change": 0, "trend": "up"},
                "customers": {"value": 0, "change": 0, "trend": "up"},
                "avg_order": {"value": 0, "change": 0, "trend": "up"},
                "messages": {"value": 0, "change": 0, "trend": "up"},
            }

        # Revenue & orders from ORDERS table (not transactions — orders are the real data)
        order_result = await self.db.execute(
            select(
                func.sum(Order.total_price).label("revenue"),
                func.count(Order.id).label("orders"),
                func.avg(Order.total_price).label("avg_order"),
            ).where(
                Order.business_id == business_id,
                Order.status.in_(["confirmed", "delivered", "shipped", "preparing"]),
            )
        )
        row = order_result.one_or_none()
        revenue = float(row[0]) if row and row[0] else 0
        orders = row[1] if row else 0
        avg_order = float(row[2]) if row and row[2] else 0

        # Message count from whatsapp_messages
        msg_result = await self.db.execute(
            select(func.count(WhatsAppMessage.id)).where(WhatsAppMessage.business_id == business_id)
        )
        messages = msg_result.scalar() or 0

        cust_result = await self.db.execute(
            select(func.count(Customer.id)).where(Customer.business_id == business_id)
        )
        customers = cust_result.scalar() or 0

        return {
            "revenue": {"value": round(revenue, 2), "change": 0, "trend": "up"},
            "orders": {"value": orders, "change": 0, "trend": "up"},
            "customers": {"value": customers, "change": 0, "trend": "up"},
            "avg_order": {"value": round(avg_order, 2), "change": 0, "trend": "up"},
            "messages": {"value": messages, "change": 0, "trend": "up"},
        }

    async def _get_revenue_chart(self, business_id: str) -> list:
        """Last 7 days revenue chart from orders table — single GROUP BY query."""
        if not self.db:
            return []
        try:
            start_day = datetime.utcnow().date() - timedelta(days=6)
            start_dt = datetime.combine(start_day, datetime.min.time())
            result = await self.db.execute(
                select(
                    func.date(Order.created_at).label("day"),
                    func.sum(Order.total_price).label("revenue"),
                    func.count(Order.id).label("orders"),
                ).where(
                    Order.business_id == business_id,
                    Order.created_at >= start_dt,
                ).group_by(func.date(Order.created_at)).order_by("day")
            )
            rows = result.all()
            # Build a dict for quick lookup, then fill all 7 days
            by_date = {str(r[0]): {"revenue": float(r[1]) if r[1] else 0, "orders": r[2]} for r in rows}
            chart = []
            for i in range(6, -1, -1):
                day = datetime.utcnow().date() - timedelta(days=i)
                day_str = day.isoformat()
                info = by_date.get(day_str, {"revenue": 0, "orders": 0})
                chart.append({
                    "date": day_str,
                    "revenue": info["revenue"],
                    "orders": info["orders"],
                })
            return chart
        except Exception:
            return [{"date": datetime.utcnow().date().isoformat(), "revenue": 0, "orders": 0}]

    async def _get_customer_metrics(self, business_id: str) -> dict:
        if not self.db:
            return {"total": 0, "new_this_month": 0, "active": 0, "churned": 0}
        result = await self.db.execute(
            select(func.count(Customer.id)).where(Customer.business_id == business_id)
        )
        total = result.scalar() or 0
        return {"total": total, "new_this_month": 0, "active": total, "churned": 0}

    async def _get_top_products(self, business_id: str) -> list:
        """Top products by total revenue from orders."""
        if not self.db:
            return []
        try:
            result = await self.db.execute(
                select(
                    Order.product_name,
                    func.sum(Order.quantity).label("total_qty"),
                    func.sum(Order.total_price).label("total_revenue"),
                    func.count(Order.id).label("order_count"),
                ).where(
                    Order.business_id == business_id,
                    Order.product_name.isnot(None),
                ).group_by(Order.product_name)
                .order_by(desc(func.sum(Order.total_price)))
                .limit(5)
            )
            return [
                {
                    "name": row.product_name,
                    "quantity": int(row.total_qty or 0),
                    "revenue": float(row.total_revenue or 0),
                    "sales": int(row.order_count or 0),
                }
                for row in result.all()
            ]
        except Exception:
            return []

    async def _get_customer_segments(self, business_id: str) -> dict:
        return {"high_value": 0, "medium_value": 0, "low_value": 0}

    async def _get_recent_transactions(self, business_id: str) -> list:
        if not self.db:
            return []
        result = await self.db.execute(
            select(Transaction).where(Transaction.business_id == business_id)
            .order_by(desc(Transaction.created_at)).limit(10)
        )
        txns = result.scalars().all()
        return [
            {"id": t.id, "amount": t.amount, "type": t.type, "status": t.status, "created_at": str(t.created_at)}
            for t in txns
        ]

    async def _get_activity_feed(self, business_id: str, limit: int = 50) -> list:
        return [{"type": "system", "message": "Dashboard loaded", "timestamp": datetime.utcnow().isoformat()}]

    async def get_revenue_analytics(self, business_id: str, period: str = "daily") -> dict:
        return {"business_id": business_id, "period": period, "data": []}

    async def get_customer_analytics(self, business_id: str) -> dict:
        return {"retention_rate": 0.0, "acquisition_rate": 0.0, "ltv": 0.0}

    async def get_transaction_analytics(self, business_id: str) -> dict:
        return {"total": 0, "completed": 0, "pending": 0, "failed": 0}

    async def calculate_mrr(self, business_id: str) -> float:
        return 0.0

    async def calculate_churn(self, business_id: str) -> float:
        return 0.0

    async def calculate_clv(self, business_id: str) -> float:
        return 0.0

    async def get_customer_segmentation(self, business_id: str) -> dict:
        return {"high_value": 0, "medium_value": 0, "low_value": 0}

    async def generate_insights(self, business_id: str) -> list[str]:
        return [
            "Dashboard setup ho gaya hai! Data aane ke baad insights milenge.",
            "Pehle products add karein aur transactions record karein.",
        ]

    async def get_activity_feed(self, business_id: str, limit: int = 50) -> list:
        return await self._get_activity_feed(business_id, limit)

    async def refresh_analytics(self, business_id: str) -> dict:
        if self.redis:
            await self.redis.delete(f"dashboard:{business_id}")
        return {"status": "refreshed", "business_id": business_id}
