"""Proxy to WhatsApp Bot HTTP server — CORS-free access for frontend."""

import httpx
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user

router = APIRouter(prefix="/api/v1/bot")

# Env-driven so Docker networking works (service name "whatsapp-bot").
BOT_URL = os.getenv("BOT_URL", "http://127.0.0.1:8001")
BOT_API_KEY = os.getenv("BOT_API_KEY", "") or None


def _bot_headers() -> dict:
    """Forward the bot API key if configured, else empty headers."""
    if BOT_API_KEY:
        return {"Authorization": f"Bearer {BOT_API_KEY}"}
    return {}


@router.get("/qr")
async def proxy_qr(current_user=Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{BOT_URL}/qr", headers=_bot_headers())
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bot unreachable: {e}")

@router.get("/status")
async def proxy_status(current_user=Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{BOT_URL}/status", headers=_bot_headers())
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bot unreachable: {e}")

@router.post("/logout")
async def proxy_logout(current_user=Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{BOT_URL}/logout", headers=_bot_headers())
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bot unreachable: {e}")

class SendMessage(BaseModel):
    phone: str
    message: str
    image_url: Optional[str] = None

@router.post("/send")
async def proxy_send(req: SendMessage, current_user=Depends(get_current_user)):
    try:
        payload = {"phone": req.phone, "message": req.message}
        if req.image_url:
            payload["image_url"] = req.image_url
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{BOT_URL}/send", json=payload, headers=_bot_headers())
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bot unreachable: {e}")
