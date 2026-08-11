"""
Message Queue - 1000+ customers ek saath handle karta hai.
Redis use karta hai agar available ho, nahi toh in-memory queue.
WhatsApp rate limits ke saath safely send karta hai.

Flow:
1. Message queue mein add hota hai
2. Worker systematically send karta hai (rate limited)
3. Failed messages retry hote hain
4. Status track hota hai
"""

import asyncio
import json
import time
from typing import Optional
from datetime import datetime
from collections import deque
import threading


class MessageQueue:
    """
    In-memory message queue - Redis nahi chahiye.
    Production mein Redis add kar sakte ho.
    """

    def __init__(self):
        self.queue = deque()  # Pending messages
        self.processing = False
        self.stats = {
            "total_queued": 0,
            "total_sent": 0,
            "total_failed": 0,
            "total_retries": 0,
        }
        self.rate_limit = 10  # Messages per second max
        self.min_delay_ms = 100  # Minimum delay between messages (ms)
        self.max_retries = 3
        self._lock = threading.Lock()

    def enqueue(
        self,
        phone: str,
        message: str,
        business_id: str = None,
        priority: str = "normal",  # normal | high | bulk
        metadata: dict = None,
    ) -> str:
        """Message queue mein add karo - unique ID return."""
        import uuid
        msg_id = str(uuid.uuid4())[:8]

        item = {
            "id": msg_id,
            "phone": phone,
            "message": message,
            "business_id": business_id,
            "priority": priority,
            "metadata": metadata or {},
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
            "last_attempt": None,
            "error": None,
        }

        with self._lock:
            if priority == "high":
                # High priority messages aage jaate hain
                self.queue.appendleft(item)
            else:
                self.queue.append(item)
            self.stats["total_queued"] += 1

        return msg_id

    def get_status(self, msg_id: str) -> dict:
        """Message ka status check karo."""
        with self._lock:
            for item in self.queue:
                if item["id"] == msg_id:
                    return {
                        "id": item["id"],
                        "status": item["status"],
                        "attempts": item["attempts"],
                        "error": item["error"],
                    }
        return {"status": "not_found"}

    def get_stats(self) -> dict:
        """Queue statistics."""
        with self._lock:
            return {
                **self.stats,
                "pending": len([m for m in self.queue if m["status"] == "queued"]),
                "processing": len([m for m in self.queue if m["status"] == "processing"]),
                "failed": len([m for m in self.queue if m["status"] == "failed"]),
            }

    def get_queue_size(self) -> int:
        """Kitne messages pending hain."""
        with self._lock:
            return len([m for m in self.queue if m["status"] == "queued"])

    async def process_queue(self, send_callback):
        """
        Queue process karo - har message ko send karo with rate limiting.
        send_callback(phone, message) async function hona chahiye.
        """
        if self.processing:
            return  # Already processing

        self.processing = True

        try:
            while True:
                # Pending messages nikalo
                with self._lock:
                    pending = [m for m in self.queue if m["status"] == "queued"]

                if not pending:
                    break  # Queue khatam

                for item in pending:
                    item["status"] = "processing"
                    item["attempts"] += 1
                    item["last_attempt"] = datetime.utcnow().isoformat()

                    try:
                        # Send callback call karo
                        await send_callback(item["phone"], item["message"])

                        # Success
                        item["status"] = "sent"
                        with self._lock:
                            self.stats["total_sent"] += 1

                    except Exception as e:
                        item["error"] = str(e)

                        if item["attempts"] < self.max_retries:
                            # Retry ke liye wapas queue mein daalo
                            item["status"] = "queued"
                            with self._lock:
                                self.stats["total_retries"] += 1
                        else:
                            # Max retries ho gaye
                            item["status"] = "failed"
                            with self._lock:
                                self.stats["total_failed"] += 1

                    # Rate limiting - har message ke beech delay
                    await asyncio.sleep(self.min_delay_ms / 1000)

        finally:
            self.processing = False

    def clear_failed(self) -> int:
        """Failed messages hatao - count return."""
        with self._lock:
            before = len(self.queue)
            self.queue = deque(m for m in self.queue if m["status"] != "failed")
            return before - len(self.queue)

    def retry_failed(self) -> int:
        """Failed messages ko wapas queue mein daalo."""
        count = 0
        with self._lock:
            for item in self.queue:
                if item["status"] == "failed":
                    item["status"] = "queued"
                    item["attempts"] = 0
                    item["error"] = None
                    count += 1
        return count


# ─────────────────────────────────────────────────────
# Singleton instance - poora system ek queue use kare
# ─────────────────────────────────────────────────────
message_queue = MessageQueue()


# ─────────────────────────────────────────────────────
# Bulk messaging - 1000 customers ko ek saath bhejo
# ─────────────────────────────────────────────────────
async def bulk_send_messages(
    messages: list[dict],
    send_callback,
    batch_size: int = 50,
    delay_between_batches: float = 2.0,
) -> dict:
    """
    Bulk messages bhejo - 1000+ customers.
    
    messages = [
        {"phone": "919876543210", "message": "Hello!"},
        {"phone": "919876543211", "message": "Order confirm!"},
    ]
    
    send_callback(phone, message) async function.
    
    Returns stats.
    """
    total = len(messages)
    sent = 0
    failed = 0

    # Messages ko batches mein todo
    for i in range(0, total, batch_size):
        batch = messages[i:i + batch_size]

        for msg in batch:
            msg_id = message_queue.enqueue(
                phone=msg["phone"],
                message=msg["message"],
                business_id=msg.get("business_id"),
                priority=msg.get("priority", "normal"),
            )

        # Queue process karo
        await message_queue.process_queue(send_callback)

        # Batch ke beech delay - WhatsApp rate limit
        if i + batch_size < total:
            await asyncio.sleep(delay_between_batches)

    stats = message_queue.get_stats()

    return {
        "total_queued": total,
        "total_sent": stats["total_sent"],
        "total_failed": stats["total_failed"],
        "total_retries": stats["total_retries"],
    }
