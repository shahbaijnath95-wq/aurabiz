from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator
from fastapi import Request
import json
import os

from config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Redis - disabled (not running locally, causes 2s delay per request)
redis_client = None


class Base(DeclarativeBase):
    pass


tenant_engines = {}
tenant_sessions = {}

async def ensure_tenant_db(tenant_id: str):
    if tenant_id == "default":
        return engine, async_session
        
    if tenant_id not in tenant_engines:
        # Tenant DBs AppData mein rakho — install dir (C:\Program Files) read-only hai!
        _appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        tenants_dir = os.path.join(_appdata, "AuraBiz", "tenants")
        db_path = os.path.join(tenants_dir, f"{tenant_id}.db")
        os.makedirs(tenants_dir, exist_ok=True)
        
        is_new = not os.path.exists(db_path)
        
        db_url = f"sqlite+aiosqlite:///{db_path}"
        t_engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
        )
        t_session = async_sessionmaker(t_engine, class_=AsyncSession, expire_on_commit=False)
        tenant_engines[tenant_id] = t_engine
        tenant_sessions[tenant_id] = t_session
        
        if is_new:
            async with t_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
    return tenant_engines[tenant_id], tenant_sessions[tenant_id]


async def get_db(request: Request = None) -> AsyncGenerator[AsyncSession, None]:
    tenant_id = "default"
    if request and hasattr(request.state, "tenant_id"):
        tenant_id = request.state.tenant_id
        
    _, t_session = await ensure_tenant_db(tenant_id)
    
    async with t_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis():
    return redis_client


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Lightweight schema migration: existing SQLite DBs may lack newly added columns.
    # create_all does NOT add columns to existing tables, so ALTER TABLE runs here.
    if "sqlite" in settings.DATABASE_URL:
        await _migrate_sqlite_columns()


async def _migrate_sqlite_columns():
    """Add missing columns to existing SQLite tables (idempotent)."""
    migrations = {
        "orders": [
            ("payment_status", "VARCHAR(30) DEFAULT 'pending'"),
            ("payment_id", "VARCHAR"),
        ],
    }
    async with engine.begin() as conn:
        for table, columns in migrations.items():
            existing = {
                row[1]
                for row in (
                    await conn.execute(text(f"PRAGMA table_info({table})"))
                ).fetchall()
            }
            for col_name, col_def in columns:
                if col_name not in existing:
                    await conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                    )


async def close_db():
    await engine.dispose()
    for t_engine in tenant_engines.values():
        await t_engine.dispose()
    if redis_client:
        await redis_client.close()


class RedisSession:
    def __init__(self, redis):
        self.redis = redis

    async def get(self, key: str) -> dict | None:
        if not self.redis:
            return None
        data = await self.redis.get(f"session:{key}")
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, value: dict, expiry: int = 3600) -> None:
        if not self.redis:
            return
        await self.redis.set(f"session:{key}", json.dumps(value, default=str), ex=expiry)

    async def delete(self, key: str) -> None:
        if not self.redis:
            return
        await self.redis.delete(f"session:{key}")

    async def exists(self, key: str) -> bool:
        if not self.redis:
            return False
        return await self.redis.exists(f"session:{key}") > 0
