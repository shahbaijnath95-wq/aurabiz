"""
Analytics Aggregator Service
=============================
Aggregates platform stats. Works with BOTH SQLite (local desktop) and
PostgreSQL (Render cloud). Uses the SQLAlchemy async engine from database.py
instead of raw sqlite3 with hardcoded paths.
"""
import uuid
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select, func, text

from database import engine, async_session
from models import PlatformStats, Tenant


def _get_tenant_db_stats(db_path: str) -> Dict:
    """Read aggregate counts from a single tenant's SQLite database (if real file)."""
    stats = {
        "total_orders": 0,
        "total_messages": 0,
        "total_revenue": 0.0,
        "total_customers": 0,
        "total_products": 0,
    }
    # Desktop-app tenants have db_path="local-desktop-app" (no real file)
    if not db_path or not os.path.exists(db_path):
        return stats

    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
            stats["total_orders"] = row[0] if row else 0
        except Exception:
            pass
        try:
            row = conn.execute("SELECT COUNT(*) FROM whatsapp_messages").fetchone()
            stats["total_messages"] = row[0] if row else 0
        except Exception:
            pass
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status IN ('confirmed', 'paid', 'completed')"
            ).fetchone()
            stats["total_revenue"] = float(row[0]) if row else 0.0
        except Exception:
            pass
        try:
            row = conn.execute("SELECT COUNT(*) FROM customers").fetchone()
            stats["total_customers"] = row[0] if row else 0
        except Exception:
            pass
        try:
            row = conn.execute("SELECT COUNT(*) FROM products").fetchone()
            stats["total_products"] = row[0] if row else 0
        except Exception:
            pass
        conn.close()
    except Exception:
        pass

    return stats


async def aggregate_daily_stats() -> Dict:
    """Aggregate stats from all tenants and write to platform_stats table."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    async with async_session() as db:
        # Get all tenants
        tenants_result = await db.execute(
            select(Tenant.id, Tenant.db_path, Tenant.status, Tenant.plan)
        )
        tenants = tenants_result.all()

        total_tenants = len(tenants)
        active_tenants = sum(1 for t in tenants if t.status == "active")
        total_messages = 0
        total_orders = 0
        total_revenue = 0.0

        for tenant in tenants:
            stats = _get_tenant_db_stats(tenant.db_path)
            total_messages += stats["total_messages"]
            total_orders += stats["total_orders"]
            total_revenue += stats["total_revenue"]

        # New signups today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        new_signups = (await db.execute(
            select(func.count(Tenant.id)).where(Tenant.created_at >= today_start)
        )).scalar() or 0

        # Upsert into platform_stats (delete existing for today, then insert)
        existing = (await db.execute(
            select(PlatformStats).where(PlatformStats.date == today)
        )).scalar_one_or_none()
        if existing:
            existing.total_tenants = total_tenants
            existing.active_tenants = active_tenants
            existing.total_messages = total_messages
            existing.total_orders = total_orders
            existing.total_revenue = total_revenue
            existing.new_signups = new_signups
        else:
            db.add(PlatformStats(
                id=str(uuid.uuid4()),
                date=today,
                total_tenants=total_tenants,
                active_tenants=active_tenants,
                total_messages=total_messages,
                total_orders=total_orders,
                total_revenue=total_revenue,
                new_signups=new_signups,
                created_at=datetime.now(timezone.utc),
            ))
        await db.commit()

    return {
        "date": today,
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_messages": total_messages,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "new_signups": new_signups,
    }


async def get_daily_stats(days: int = 30) -> List[Dict]:
    """Fetch daily stats for the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    async with async_session() as db:
        result = await db.execute(
            select(PlatformStats).where(PlatformStats.date >= cutoff).order_by(PlatformStats.date.asc())
        )
        rows = result.scalars().all()
    return [
        {
            "date": r.date,
            "total_tenants": r.total_tenants,
            "active_tenants": r.active_tenants,
            "total_messages": r.total_messages,
            "total_orders": r.total_orders,
            "total_revenue": r.total_revenue,
            "new_signups": r.new_signups,
        }
        for r in rows
    ]


async def get_growth_stats() -> Dict:
    """Calculate growth metrics: signups, plan distribution, MRR, churn."""
    now = datetime.now(timezone.utc)
    this_month = now.strftime("%Y-%m")
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as db:
        # Plan distribution
        plan_rows = await db.execute(
            select(Tenant.plan, func.count(Tenant.id)).where(Tenant.status != "deleted").group_by(Tenant.plan)
        )
        plan_distribution = {p: c for p, c in plan_rows.all()}

        # MRR
        plan_prices = {"starter": 999, "growth": 2499, "enterprise": 4999}
        mrr = sum(plan_prices.get(p, 0) * c for p, c in plan_distribution.items())

        # New signups this month / last month
        new_this_month = (await db.execute(
            select(func.count(Tenant.id)).where(Tenant.created_at >= month_start)
        )).scalar() or 0
        new_last_month = (await db.execute(
            select(func.count(Tenant.id)).where(
                Tenant.created_at >= last_month_start, Tenant.created_at < month_start
            )
        )).scalar() or 0

        # Churned (suspended)
        churned = (await db.execute(
            select(func.count(Tenant.id)).where(Tenant.status == "suspended", Tenant.suspended_at >= month_start)
        )).scalar() or 0

        # Active / total
        total_active = (await db.execute(
            select(func.count(Tenant.id)).where(Tenant.status == "active")
        )).scalar() or 0
        total_all = (await db.execute(
            select(func.count(Tenant.id)).where(Tenant.status != "deleted")
        )).scalar() or 0

    return {
        "plan_distribution": plan_distribution,
        "mrr": mrr,
        "new_signups_this_month": new_this_month,
        "new_signups_last_month": new_last_month,
        "signup_growth_pct": round(
            ((new_this_month - new_last_month) / max(new_last_month, 1)) * 100, 1
        ),
        "churned_this_month": churned,
        "churn_rate": round((churned / max(total_active, 1)) * 100, 1),
        "total_active": total_active,
        "total_tenants": total_all,
    }


async def get_top_tenants(limit: int = 10) -> List[Dict]:
    """Get top tenants by message usage."""
    async with async_session() as db:
        result = await db.execute(
            select(Tenant).where(Tenant.status != "deleted")
            .order_by(Tenant.messages_used_this_month.desc())
            .limit(limit)
        )
        tenants = result.scalars().all()

    top = []
    for t in tenants:
        tenant_stats = _get_tenant_db_stats(t.db_path)
        top.append({
            "id": t.id,
            "name": t.name,
            "owner_email": t.owner_email,
            "plan": t.plan,
            "messages_used_this_month": t.messages_used_this_month,
            "total_orders": tenant_stats["total_orders"],
            "total_revenue": tenant_stats["total_revenue"],
            "total_customers": tenant_stats["total_customers"],
        })
    return top


if __name__ == "__main__":
    import asyncio
    async def _run():
        print("Aggregating daily stats...")
        result = await aggregate_daily_stats()
        print(f"Result: {result}")
        print("\nGrowth stats:")
        growth = await get_growth_stats()
        for k, v in growth.items():
            print(f"  {k}: {v}")
    asyncio.run(_run())