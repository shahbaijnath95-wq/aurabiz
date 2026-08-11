import httpx
import hashlib
import json
import base64
from typing import Optional
from config import settings
import uuid


class PhonePeClient:
    def __init__(self):
        self.merchant_id = settings.PHONEPE_MERCHANT_ID
        self.api_key = settings.PHONEPE_API_KEY
        self.salt_key = settings.PHONEPE_SALT_KEY
        self.salt_index = settings.PHONEPE_SALT_INDEX
        self.base_url = settings.PHONEPE_BASE_URL

    def _generate_checksum(self, base64_payload: str, endpoint: str) -> str:
        """PhonePe checksum = sha256(base64_payload + endpoint + salt_key) + '##' + salt_index."""
        if not self.salt_key:
            return ""
        string_to_hash = base64_payload + endpoint + self.salt_key
        sha256 = hashlib.sha256(string_to_hash.encode()).hexdigest()
        return f"{sha256}##{self.salt_index}"

    def _encode_payload(self, payload: dict) -> str:
        return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()

    async def create_payment(self, amount: float, transaction_id: str = None, customer_id: str = None) -> dict:
        if not self.merchant_id:
            return {"error": "PhonePe configured nahi hai"}
        txn_id = transaction_id or f"TXN-{uuid.uuid4().hex[:12].upper()}"
        payload = {
            "merchantId": self.merchant_id,
            "transactionId": txn_id,
            "amount": int(amount * 100),
            "merchantOrderId": txn_id,
            "message": "Payment for order",
        }
        endpoint = "/pg/v1/pay"
        base64_payload = self._encode_payload(payload)
        checksum = self._generate_checksum(base64_payload, endpoint)
        # PhonePe expects the base64 payload as the request body (not JSON)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json={"request": base64_payload},
                headers={"X-VERIFY": checksum, "Content-Type": "application/json"},
            )
            return resp.json()

    async def check_status(self, transaction_id: str) -> dict:
        if not self.merchant_id:
            return {"error": "PhonePe configured nahi hai"}
        endpoint = f"/pg/v1/status/{self.merchant_id}/{transaction_id}"
        # For GET, checksum is sha256(endpoint + salt_key)
        string_to_hash = endpoint + self.salt_key
        sha256 = hashlib.sha256(string_to_hash.encode()).hexdigest()
        checksum = f"{sha256}##{self.salt_index}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}{endpoint}",
                headers={"X-VERIFY": checksum, "Content-Type": "application/json"},
            )
            return resp.json()

    async def create_refund(self, transaction_id: str, amount: float) -> dict:
        if not self.merchant_id:
            return {"error": "PhonePe configured nahi hai"}
        refund_payload = {
            "merchantId": self.merchant_id,
            "transactionId": transaction_id,
            "amount": int(amount * 100),
            "merchantOrderId": transaction_id,
        }
        endpoint = "/pg/v1/refund"
        base64_payload = self._encode_payload(refund_payload)
        checksum = self._generate_checksum(base64_payload, endpoint)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json={"request": base64_payload},
                headers={"X-VERIFY": checksum, "Content-Type": "application/json"},
            )
            return resp.json()

    async def connect(self, business_id: str, credentials: dict) -> dict:
        return {"business_id": business_id, "status": "connected", "type": "phonepe"}
