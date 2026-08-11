"""
Analytics Aggregator Service
=============================
Iterates all active tenants, reads their SQLite DBs,
and populates the platform_stats table with daily aggregated data.
"""
import sqlite3
import uuid
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pathlib import Path

MASTER_DB_PATH = os.getenv(
    "MASTER_DB_PATH",
    str(Path(__file__).parent.parent / "data" / "master.db")
)


def _get_tenant_db_stats(db_path: str) -> Dict:
    """Read aggregate counts from a single tenant's database."""
    stats = {
        "total_orders": 0,
        "total_messages": 0,
        "total_revenue": 0.0,
        "total_customers": 0,
        "total_products": 0,
    }
    if not os.path.exists(db_path):
        return stats

    try:
        conn = sqlite3.connect(db_path)
        # Orders count
        try:
            row = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
            stats["total_orders"] = row[0] if row else 0
        except Exception:
            pass

        # Messages count
        try:
            row = conn.execute("SELECT COUNT(*) FROM whatsapp_messages").fetchone()
            stats["total_messages"] = row[0] if row else 0
        except Exception:
            pass

        # Revenue from payments (only confirmed/paid)
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status IN ('confirmed', 'paid', 'completed')"
            ).fetchone()
            stats["total_revenue"] = float(row[0]) if row else 0.0
        except Exception:
            pass

        # Customers
        try:
            row = conn.execute("SELECT COUNT(*) FROM customers").fetchone()
            stats["total_customers"] = row[0] if row else 0
        except Exception:
            pass

        # Products
        try:
            row = conn.execute("SELECT COUNT(*) FROM products").fetchone()
            stats["total_products"] = row[0] if row else 0
        except Exception:
            pass

        conn.close()
    except Exception:
        pass

    return stats


def aggregate_daily_stats() -> Dict:
    """
    Aggregate stats from all tenants and write to platform_stats table.
    Returns summary of aggregation.
    """
    if not os.path.exists(MASTER_DB_PATH):
        return {"error": "Master DB not found"}

    master = sqlite3.connect(MASTER_DB_PATH)
    master.row_factory = sqlite3.Row

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get all tenants
    tenants = master.execute(
        "SELECT id, db_path, status, plan FROM tenants"
    ).fetchall()

    total_tenants = len(tenants)
    active_tenants = sum(1 for t in tenants if t["status"] == "active")
    total_messages = 0
    total_orders = 0
    total_revenue = 0.0

    for tenant in tenants:
        db_path = tenant["db_path"]
        stats = _get_tenant_db_stats(db_path)
        total_messages += stats["total_messages"]
        total_orders += stats["total_orders"]
        total_revenue += stats["total_revenue"]

    # Count new signups today
    new_signups = master.execute(
        "SELECT COUNT(*) FROM tenants WHERE DATE(created_at) = ?", (today,)
    ).fetchone()[0]

    # Upsert into platform_stats (delete existing for today, then insert)
    master.execute("DELETE FROM platform_stats WHERE date = ?", (today,))
    master.execute(
        """INSERT INTO platform_stats (id, date, total_tenants, active_tenants, total_messages, total_orders, total_revenue, new_signups, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(uuid.uuid4()), today, total_tenants, active_tenants,
         total_messages, total_orders, total_revenue, new_signups,
         datetime.now(timezone.utc).isoformat())
    )
    master.commit()
    master.close()

    return {
        "date": today,
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_messages": total_messages,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "new_signups": new_signups,
    }


def get_daily_stats(days: int = 30) -> List[Dict]:
    """Fetch daily stats for the last N days."""
    if not os.path.exists(MASTER_DB_PATH):
        return []

    master = sqlite3.connect(MASTER_DB_PATH)
    master.row_factory = sqlite3.Row

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = master.execute(
        "SELECT * FROM platform_stats WHERE date >= ? ORDER BY date ASC",
        (cutoff,)
    ).fetchall()
    master.close()

    return [dict(r) for r in rows]


def get_growth_stats() -> Dict:
    """Calculate growth metrics: signups, plan distribution, MRR, churn."""
    if not os.path.exists(MASTER_DB_PATH):
        return {}

    master = sqlite3.connect(MASTER_DB_PATH)
    master.row_factory = sqlite3.Row

    now = datetime.now(timezone.utc)
    this_month = now.strftime("%Y-%m")
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    # Plan distribution
    plans = master.execute(
        "SELECT plan, COUNT(*) as count FROM tenants WHERE status != 'deleted' GROUP BY plan"
    ).fetchall()
    plan_distribution = {r["plan"]: r["count"] for r in plans}

    # MRR calculation
    plan_prices = {"starter": 0, "growth": 999, "enterprise": 2999}
    mrr = sum(plan_prices.get(p, 0) * c for p, c in plan_distribution.items())

    # New signups this month
    new_this_month = master.execute(
        "SELECT COUNT(*) FROM tenants WHERE strftime('%Y-%m', created_at) = ?",
        (this_month,)
    ).fetchone()[0]

    # New signups last month (for comparison)
    new_last_month = master.execute(
        "SELECT COUNT(*) FROM tenants WHERE strftime('%Y-%m', created_at) = ?",
        (last_month,)
    ).fetchone()[0]

    # Churn (suspended this month)
    churned = master.execute(
        "SELECT COUNT(*) FROM tenants WHERE status = 'suspended' AND strftime('%Y-%m', suspended_at) = ?",
        (this_month,)
    ).fetchone()[0]

    # Total active
    total_active = master.execute(
        "SELECT COUNT(*) FROM tenants WHERE status = 'active'"
    ).fetchone()[0]

    # Total all time
    total_all = master.execute(
        "SELECT COUNT(*) FROM tenants WHERE status != 'deleted'"
    ).fetchone()[0]

    master.close()

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


def get_top_tenants(limit: int = 10) -> List[Dict]:
    """Get top tenants by message usage."""
    if not os.path.exists(MASTER_DB_PATH):
        return []

    master = sqlite3.connect(MASTER_DB_PATH)
    master.row_factory = sqlite3.Row

    rows = master.execute(
        """SELECT id, name, owner_email, plan, status, messages_used_this_month, max_messages_per_month
           FROM tenants WHERE status != 'deleted'
           ORDER BY messages_used_this_month DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    master.close()

    result = []
    for r in rows:
        row_dict = dict(r)
        # Try to get order/revenue from tenant DB
        db_path_query = sqlite3.connect(MASTER_DB_PATH)
        db_path_row = db_path_query.execute(
            "SELECT db_path FROM tenants WHERE id = ?", (r["id"],)
        ).fetchone()
        db_path_query.close()

        if db_path_row:
            tenant_stats = _get_tenant_db_stats(db_path_row[0])
            row_dict["total_orders"] = tenant_stats["total_orders"]
            row_dict["total_revenue"] = tenant_stats["total_revenue"]
            row_dict["total_customers"] = tenant_stats["total_customers"]
        else:
            row_dict["total_orders"] = 0
            row_dict["total_revenue"] = 0
            row_dict["total_customers"] = 0

        result.append(row_dict)

    return result


if __name__ == "__main__":
    print("Aggregating daily stats...")
    result = aggregate_daily_stats()
    print(f"Result: {result}")

    print("\nGrowth stats:")
    growth = get_growth_stats()
    for k, v in growth.items():
        print(f"  {k}: {v}")

    print("\nTop tenants:")
    top = get_top_tenants(5)
    for t in top:
        print(f"  {t['name']}: {t['messages_used_this_month']} msgs")
