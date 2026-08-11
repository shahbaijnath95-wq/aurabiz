import httpx
from typing import Optional
from config import settings


class InstagramService:
    def __init__(self):
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.base_url = "https://graph.facebook.com/v19.0"

    async def get_messages(self, business_id: str) -> list:
        return []

    async def get_media(self, business_id: str) -> list:
        return []

    async def reply_to_comment(self, comment_id: str, message: str) -> dict:
        return {"comment_id": comment_id, "status": "replied"}

    async def get_insights(self, media_id: str) -> dict:
        return {"likes": 0, "comments": 0, "shares": 0}

    async def connect(self, business_id: str, credentials: dict) -> dict:
        return {"business_id": business_id, "status": "connected", "type": "instagram"}
