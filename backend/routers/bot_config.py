"""Bot configuration management - business hours, auto-reply, welcome message."""

import os
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user

router = APIRouter(prefix="/api/v1")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "whatsapp-bot", "bot_config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"business_id": "", "welcome_message": "", "business_hours": {}, "auto_reply": {}}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    # Atomic write: write to temp file then rename
    import tempfile
    dir_path = os.path.dirname(CONFIG_PATH) or "."
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=dir_path, delete=False, suffix=".tmp") as tmp:
        json.dump(config, tmp, indent=2, ensure_ascii=False)
        tmp_path = tmp.name
    os.replace(tmp_path, CONFIG_PATH)


class BotConfigUpdate(BaseModel):
    welcome_message: Optional[str] = None
    business_hours: Optional[dict] = None
    auto_reply: Optional[dict] = None


@router.get("/bot/config")
async def get_bot_config(current_user=Depends(get_current_user)):
    return load_config()


@router.put("/bot/config")
async def update_bot_config(req: BotConfigUpdate, current_user=Depends(get_current_user)):
    config = load_config()
    if req.welcome_message is not None:
        config["welcome_message"] = req.welcome_message
    if req.business_hours is not None:
        config["business_hours"] = req.business_hours
    if req.auto_reply is not None:
        config["auto_reply"] = req.auto_reply
    save_config(config)
    return {"status": "updated", "config": config}
