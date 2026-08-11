import httpx
from typing import Optional
from config import settings


class GoogleBusinessService:
    def __init__(self):
        self.api_key = settings.GOOGLE_BUSINESS_API_KEY
        self.base_url = "https://mybusinessbusinessinformation.googleapis.com/v1"

    async def get_reviews(self, location_id: str) -> list:
        return []

    async def reply_to_review(self, review_id: str, reply_text: str) -> dict:
        return {"review_id": review_id, "reply": reply_text, "status": "posted"}

    async def create_post(self, business_id: str, content: str) -> dict:
        return {"business_id": business_id, "status": "created"}

    async def get_insights(self, business_id: str) -> dict:
        return {"views": 0, "actions": 0, "calls": 0}

    async def connect(self, business_id: str, credentials: dict) -> dict:
        return {"business_id": business_id, "status": "connected", "type": "google_business"}
