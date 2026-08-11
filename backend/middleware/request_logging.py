from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger("request_logger")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        url = str(request.url)

        response = await call_next(request)

        duration = time.time() - start_time
        status_code = response.status_code
        logger.info(f"{method} {url} - {status_code} - {duration:.3f}s")

        return response
