from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import os
import time
import uuid

from config import settings as app_config
from database import engine, redis_client, Base
from logging_config import setup_logging, logger
from middleware.rate_limit import RateLimitMiddleware
from middleware.request_logging import RequestLoggingMiddleware
from middleware.tenant import TenantMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + Shutdown lifecycle."""
    setup_logging()
    logger.info("Starting AI WhatsApp Assistant...")

    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured.")

    # Warm up Redis (optional)
    if redis_client:
        try:
            await redis_client.ping()
            logger.info("Redis connected.")
        except Exception as e:
            logger.warning("Redis not available: {} - running without cache", e)
    else:
        logger.warning("Redis not configured - running without cache")

    # Start background scheduler for follow-ups, scheduled messages, inventory alerts
    try:
        from services.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        logger.info("Background scheduler started.")
    except Exception as e:
        logger.warning("Scheduler failed to start: {}", e)

    yield

    # --- SHUTDOWN ---
    try:
        from services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    await engine.dispose()
    if redis_client:
        await redis_client.close()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="AI WhatsApp Business Assistant",
    description="Small business ke liye intelligent WhatsApp assistant - analytics, loyalty, inventory, billing sab kuch!",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware — order matters: logging outer, rate limit inner, tenant inner, CORS inner
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, rate=1.0, capacity=60)
app.add_middleware(TenantMiddleware)


# ── Security Headers Middleware ─────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not app_config.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# ── Request ID Middleware ───────────────────────────────────────
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach unique request ID for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration}ms"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"],
)

# CORS — lock down to config
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ---- Import and register routers ----
from routers import (
    auth,
    transactions,
    customers,
    analytics,
    loyalty,
    integrations,
    revenue,
    admin,
    inventory,
    feedback,
    audit,
    webhooks,
    templates,
    chat,
    trainer,
    orders_bookings,
    coupons,
    orders,
    broadcast,
    cart,
    uploads,
    bot_config,
    bot_stats,
    bot_proxy,
    settings,
    catalog,
    payments,
    teams,
    inventory_alerts,
    followups,
    segments,
    scheduled_messages,
    exports,
    monitoring,
    knowledge,
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(customers.router)
app.include_router(analytics.router)
app.include_router(trainer.router)
app.include_router(loyalty.router)
app.include_router(integrations.router)
app.include_router(revenue.router)
app.include_router(admin.router)
app.include_router(inventory.router)
app.include_router(feedback.router)
app.include_router(audit.router)
app.include_router(webhooks.router)
app.include_router(templates.router)
app.include_router(chat.router)
app.include_router(orders_bookings.router)
app.include_router(coupons.router)
app.include_router(orders.router)
app.include_router(broadcast.router)
app.include_router(cart.router)
app.include_router(uploads.router)
app.include_router(bot_config.router)
app.include_router(bot_stats.router)
app.include_router(bot_proxy.router)
app.include_router(settings.router)
app.include_router(catalog.router)
app.include_router(payments.router)
app.include_router(teams.router)
app.include_router(inventory_alerts.router)
app.include_router(followups.router)
app.include_router(segments.router)
app.include_router(scheduled_messages.router)
app.include_router(exports.router)
app.include_router(monitoring.router)
app.include_router(knowledge.router)

# Mount uploads directory for serving images
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ── WebSocket Manager ──────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, business_id: str):
        await ws.accept()
        self.active.setdefault(business_id, []).append(ws)

    def disconnect(self, ws: WebSocket, business_id: str):
        if business_id in self.active:
            self.active[business_id] = [c for c in self.active[business_id] if c != ws]
            if not self.active[business_id]:
                del self.active[business_id]

    async def broadcast(self, business_id: str, message: str):
        for ws in self.active.get(business_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


@app.get("/")
async def root():
    return {
        "message": "AI WhatsApp Assistant chal raha hai!",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    db_ok = False
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    redis_ok = redis_client is not None
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "down",
        "redis": "connected" if redis_ok else "not configured",
        "version": "1.0.0",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, business_id: str = None, token: str = None):
    """WebSocket endpoint for real-time updates.

    Auth: requires a valid `token` query param (business JWT).
    Set WS_REQUIRE_AUTH=false to allow unauthenticated (dev only).
    """
    require_auth = os.getenv("WS_REQUIRE_AUTH", "true").lower() != "false"
    if require_auth or token:
        from jose import jwt as _jwt
        secret = app_config.SECRET_KEY or app_config.JWT_SECRET_KEY
        if not token or not secret:
            await websocket.close(code=4401, reason="Unauthorized: token required")
            return
        try:
            payload = _jwt.decode(token, secret, algorithms=["HS256"])
            # Optionally verify user exists in DB
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=4401, reason="Unauthorized: invalid token")
                return
        except Exception:
            await websocket.close(code=4401, reason="Unauthorized: invalid token")
            return

    bid = business_id or "default"
    await ws_manager.connect(websocket, bid)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, bid)
    except Exception:
        ws_manager.disconnect(websocket, bid)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
