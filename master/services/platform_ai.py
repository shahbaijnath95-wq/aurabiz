"""
Platform AI Keys Service
========================
Tenant backends call this to get platform-level AI keys.
Platform keys are the FALLBACK when tenant has no own keys.

Flow:
1. Tenant sends message → backend tries tenant's own AI keys first
2. If no own keys → fetch platform keys from master DB
3. Use platform keys to call AI providers
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from pathlib import Path

# Master DB path (same machine, relative path)
MASTER_DB_PATH = os.getenv(
    "MASTER_DB_PATH",
    str(Path(__file__).parent.parent / "data" / "master.db")
)


def get_platform_ai_providers() -> List[Dict]:
    """Fetch active AI providers from master database."""
    if not os.path.exists(MASTER_DB_PATH):
        return []
    try:
        conn = sqlite3.connect(MASTER_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT provider_key, api_key, account_id, model, priority, config "
            "FROM ai_providers WHERE is_active = 1 ORDER BY priority DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_platform_ai_config() -> Dict[str, Dict]:
    """Get platform AI providers as a dict keyed by provider_key.
    
    Returns:
        {
            "cloudflare": {"api_key": "...", "account_id": "...", "model": "...", ...},
            "gemini": {"api_key": "...", "model": "...", ...},
            "groq": {"api_key": "...", "model": "...", ...},
        }
    """
    providers = get_platform_ai_providers()
    config = {}
    for p in providers:
        config[p["provider_key"]] = {
            "api_key": p["api_key"],
            "account_id": p.get("account_id", ""),
            "model": p.get("model", ""),
            "config": json.loads(p.get("config", "{}")) if isinstance(p.get("config"), str) else p.get("config", {}),
        }
    return config


def log_ai_usage(tenant_id: str, provider_key: str, model: str,
                 tokens_in: int = 0, tokens_out: int = 0,
                 latency_ms: int = 0, success: bool = True, error: str = None):
    """Log AI usage to master database."""
    if not os.path.exists(MASTER_DB_PATH):
        return
    try:
        import uuid
        from datetime import datetime, timezone
        conn = sqlite3.connect(MASTER_DB_PATH)
        conn.execute(
            "INSERT INTO ai_usage_logs (id, tenant_id, provider_key, model, tokens_in, tokens_out, latency_ms, success, error_message, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), tenant_id, provider_key, model,
             tokens_in, tokens_out, latency_ms, success, error,
             datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Usage logging should never break the app


if __name__ == "__main__":
    # Test
    providers = get_platform_ai_providers()
    print(f"Found {len(providers)} platform AI providers:")
    for p in providers:
        print(f"  {p['provider_key']}: {p['model']} (priority={p['priority']})")
