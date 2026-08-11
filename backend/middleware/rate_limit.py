from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import asyncio
from typing import Dict


class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.last_access = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            self.last_access = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate: float = 1.0, capacity: int = 10):
        super().__init__(app)
        self.rate = rate
        self.capacity = capacity
        self.buckets: Dict[str, TokenBucket] = {}
        self._last_cleanup = time.time()
        self._cleanup_interval = 60  # seconds
        self._max_entries = 10_000
        self._entry_ttl = 300  # 5 minutes

    def _cleanup_stale_entries(self):
        """Remove buckets that haven't been used in _entry_ttl seconds."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now

        stale_keys = [
            ip for ip, bucket in self.buckets.items()
            if now - bucket.last_access > self._entry_ttl
        ]
        for ip in stale_keys:
            del self.buckets[ip]

        # If still over max, evict oldest entries
        if len(self.buckets) > self._max_entries:
            sorted_ips = sorted(
                self.buckets.keys(),
                key=lambda ip: self.buckets[ip].last_access,
            )
            to_remove = sorted_ips[: len(sorted_ips) - self._max_entries]
            for ip in to_remove:
                del self.buckets[ip]

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # Cleanup stale entries FIRST, then lazy init
        self._cleanup_stale_entries()

        # Lazy init for new IPs
        if client_ip not in self.buckets:
            self.buckets[client_ip] = TokenBucket(self.rate, self.capacity)

        bucket = self.buckets[client_ip]
        if not await bucket.consume():
            raise HTTPException(
                status_code=429,
                detail="Bahut zyada requests ho rahi hain. Thodi der baad try karein.",
            )

        response = await call_next(request)
        return response
