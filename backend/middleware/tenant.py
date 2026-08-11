from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from jose import jwt

# Use the SAME secret source as auth.py (pydantic-settings, not os.getenv,
# because pydantic-settings does not export values to os.environ).
from config import settings

SECRET_KEY = settings.SECRET_KEY or settings.JWT_SECRET_KEY
ALGORITHM = "HS256"


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = "default"

        # ── SECURITY FIX ──
        # Source of truth = verified JWT claim. A logged-in user must NOT be
        # able to switch tenant via the X-Tenant-ID header (isolation bypass).
        # The header is only honored for unauthenticated (public) requests,
        # e.g. /auth/register or /auth/login where no token exists yet.
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer ") and SECRET_KEY:
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                if "tenant_id" in payload:
                    tenant_id = payload["tenant_id"]
            except Exception:
                # Invalid/expired token — do NOT fall back to the header either,
                # otherwise a spoofed header would win. Keep default tenant.
                tenant_id = "default"
        else:
            # No valid bearer token → public request. Header is acceptable here
            # (e.g. super-admin panel selecting a tenant context pre-login).
            header_tenant_id = request.headers.get("X-Tenant-ID")
            if header_tenant_id:
                tenant_id = header_tenant_id

        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response
