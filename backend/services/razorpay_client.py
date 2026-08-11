import httpx
import hashlib
import hmac
import base64
from typing import Optional
from config import settings
import uuid


class RazorpayClient:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.base_url = "https://api.razorpay.com/v1"
        self.auth = (self.key_id, self.key_secret) if self.key_id else None

    async def create_order(self, amount: float, currency: str = "INR", receipt: str = None) -> dict:
        if not self.auth:
            return {"error": "Razorpay configured nahi hai"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/orders",
                auth=self.auth,
                json={
                    "amount": int(amount * 100),
                    "currency": currency,
                    "receipt": receipt or str(uuid.uuid4()),
                },
            )
            return resp.json()

    async def create_payment_link(self, amount: float, description: str = None) -> dict:
        if not self.auth:
            return {"error": "Razorpay configured nahi hai"}
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/payment_links",
                auth=self.auth,
                json={
                    "amount": int(amount * 100),
                    "currency": "INR",
                    "description": description or "Payment",
                },
            )
            return resp.json()

    async def get_payment(self, payment_id: str) -> dict:
        if not self.auth:
            return {"error": "Razorpay configured nahi hai"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/payments/{payment_id}", auth=self.auth)
            return resp.json()

    async def create_refund(self, payment_id: str, amount: float = None) -> dict:
        if not self.auth:
            return {"error": "Razorpay configured nahi hai"}
        async with httpx.AsyncClient() as client:
            payload = {}
            if amount:
                payload["amount"] = int(amount * 100)
            resp = await client.post(f"{self.base_url}/payments/{payment_id}/refund", auth=self.auth, json=payload)
            return resp.json()

    async def verify_payment(self, order_id: str, payment_id: str, signature: str) -> bool:
        if not self.key_secret:
            return False
        payload = f"{order_id}|{payment_id}"
        expected = hmac.new(self.key_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def connect(self, business_id: str, credentials: dict) -> dict:
        return {"business_id": business_id, "status": "connected", "type": "razorpay"}
