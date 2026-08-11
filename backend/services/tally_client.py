import httpx
from typing import Optional
from config import settings


class TallyClient:
    def __init__(self):
        self.base_url = settings.TALLY_API_URL
        self.api_key = settings.TALLY_API_KEY
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def get_ledgers(self, business_id: str) -> list:
        return []

    async def get_vouchers(self, business_id: str) -> list:
        return []

    async def get_stock(self, business_id: str) -> list:
        return []

    async def get_reports(self, business_id: str, report_type: str = "profit_loss") -> dict:
        return {"type": report_type, "data": {}}

    async def create_voucher(self, business_id: str, voucher_data: dict) -> dict:
        return {"status": "created", "data": voucher_data}

    async def sync_transactions(self, business_id: str) -> dict:
        return {"synced": 0, "status": "completed"}

    async def connect(self, business_id: str, credentials: dict) -> dict:
        return {"business_id": business_id, "status": "connected", "type": "tally"}
