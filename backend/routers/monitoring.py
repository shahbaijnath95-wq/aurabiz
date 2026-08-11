"""
Metrics Router — Prometheus-style metrics + system health dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import psutil
import os

from database import get_db, engine, redis_client
from config import settings as app_config

router = APIRouter(tags=["Monitoring"])

_start_time = time.time()


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)):
    """Prometheus-style metrics endpoint."""
    uptime = round(time.time() - _start_time, 2)

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # DB metrics
    db_ok = False
    db_latency_ms = 0
    try:
        start = time.time()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - start) * 1000, 2)
        db_ok = True
    except Exception:
        pass

    # Redis metrics
    redis_ok = False
    redis_latency_ms = 0
    if redis_client:
        try:
            start = time.time()
            await redis_client.ping()
            redis_latency_ms = round((time.time() - start) * 1000, 2)
            redis_ok = True
        except Exception:
            pass

    return {
        "uptime_seconds": uptime,
        "app": {
            "name": app_config.APP_NAME,
            "version": app_config.APP_VERSION,
            "debug": app_config.DEBUG,
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_used_mb": round(mem.used / 1024 / 1024, 1),
            "memory_total_mb": round(mem.total / 1024 / 1024, 1),
            "memory_percent": mem.percent,
            "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "disk_percent": round(disk.percent, 1),
        },
        "services": {
            "database": {
                "status": "up" if db_ok else "down",
                "latency_ms": db_latency_ms,
            },
            "redis": {
                "status": "up" if redis_ok else "down",
                "latency_ms": redis_latency_ms,
            },
        },
    }


@router.get("/health/detailed")
async def health_detailed(db: AsyncSession = Depends(get_db)):
    """Detailed health check with component status."""
    checks = {}
    overall = "healthy"

    # DB check
    try:
        start = time.time()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "latency_ms": round((time.time() - start) * 1000, 2)}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}
        overall = "degraded"

    # Redis check
    if redis_client:
        try:
            start = time.time()
            await redis_client.ping()
            checks["redis"] = {"status": "ok", "latency_ms": round((time.time() - start) * 1000, 2)}
        except Exception as e:
            checks["redis"] = {"status": "error", "error": str(e)}
            overall = "degraded"
    else:
        checks["redis"] = {"status": "not_configured"}

    # Disk space check
    disk = psutil.disk_usage("/")
    if disk.percent > 90:
        checks["disk"] = {"status": "warning", "usage_percent": disk.percent}
        overall = "degraded"
    else:
        checks["disk"] = {"status": "ok", "usage_percent": disk.percent}

    # Memory check
    mem = psutil.virtual_memory()
    if mem.percent > 90:
        checks["memory"] = {"status": "warning", "usage_percent": mem.percent}
    else:
        checks["memory"] = {"status": "ok", "usage_percent": mem.percent}

    return {
        "status": overall,
        "checks": checks,
        "uptime_seconds": round(time.time() - _start_time, 2),
    }
