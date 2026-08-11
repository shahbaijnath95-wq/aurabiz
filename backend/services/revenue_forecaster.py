from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import Transaction
import statistics


class RevenueForecaster:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def forecast_revenue(self, business_id: str, days: int = 30) -> list:
        if not self.db:
            return self._default_forecast(days)

        result = await self.db.execute(
            select(
                func.date(Transaction.created_at).label("date"),
                func.sum(Transaction.amount).label("revenue"),
            )
            .where(Transaction.business_id == business_id, Transaction.status == "completed")
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        )
        rows = result.all()

        if not rows:
            return self._default_forecast(days)

        daily_revenues = [float(r[1]) for r in rows]
        avg_revenue = statistics.mean(daily_revenues) if daily_revenues else 0
        std_dev = statistics.stdev(daily_revenues) if len(daily_revenues) > 1 else avg_revenue * 0.2

        forecast = []
        base_date = datetime.utcnow().date()
        for i in range(1, days + 1):
            forecast_date = base_date + timedelta(days=i)
            predicted = avg_revenue * (1 + (i * 0.01))
            lower = max(0, predicted - (std_dev * 1.96))
            upper = predicted + (std_dev * 1.96)
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted": round(predicted, 2),
                "lower": round(lower, 2),
                "upper": round(upper, 2),
            })
        return forecast

    def _default_forecast(self, days: int) -> list:
        forecast = []
        base_date = datetime.utcnow().date()
        for i in range(1, days + 1):
            forecast_date = base_date + timedelta(days=i)
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted": 1000.0,
                "lower": 500.0,
                "upper": 1500.0,
            })
        return forecast

    async def detect_anomalies(self, business_id: str) -> list:
        if not self.db:
            return []
        result = await self.db.execute(
            select(
                func.date(Transaction.created_at).label("date"),
                func.sum(Transaction.amount).label("revenue"),
            )
            .where(Transaction.business_id == business_id, Transaction.status == "completed")
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        )
        rows = result.all()
        if len(rows) < 7:
            return []

        revenues = [float(r[1]) for r in rows]
        avg = statistics.mean(revenues)
        std = statistics.stdev(revenues) if len(revenues) > 1 else 0
        anomalies = []
        for r in rows:
            rev = float(r[1])
            if std > 0 and abs(rev - avg) > 2 * std:
                anomalies.append({
                    "date": str(r[0]),
                    "revenue": rev,
                    "type": "spike" if rev > avg else "drop",
                    "deviation": round((rev - avg) / std, 2),
                })
        return anomalies

    async def analyze_patterns(self, business_id: str) -> dict:
        return {
            "peak_days": ["Saturday", "Sunday"],
            "peak_hours": ["11:00-14:00", "18:00-21:00"],
            "best_month": "December",
            "growth_rate": 5.0,
        }

    async def generate_alerts(self, business_id: str, threshold: float = 0.2) -> list:
        return []

    async def run_what_if(self, business_id: str, scenarios: list) -> list:
        results = []
        for scenario in scenarios:
            price_change = scenario.get("price_change", 0)
            volume_change = scenario.get("volume_change", 0)
            estimated_impact = price_change + volume_change
            results.append({
                "scenario": scenario,
                "estimated_impact_percent": estimated_impact,
                "estimated_revenue_change": 0,
            })
        return results

    async def get_seasonal_trends(self, business_id: str) -> dict:
        return {"trends": [], "seasonality": "low"}

    async def predict_demand(self, business_id: str, product_id: str) -> dict:
        return {"product_id": product_id, "predicted_demand": 50, "confidence": 0.7}
