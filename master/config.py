"""Master Backend Configuration"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─── Writable data dir ───
# Packaged Windows app (C:\Program Files is read-only) → AppData\Roaming\AuraBiz
# Linux (Render) → /var/lib/aurabiz or home dir
IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    _appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    _master_writable = Path(_appdata) / "AuraBiz" / "master" / "data"
else:
    # Linux/container — use a dedicated writable dir, NOT the repo (may be read-only)
    _master_writable = Path(os.environ.get("AURABIZ_DATA_DIR", "/var/lib/aurabiz"))
if not _master_writable.exists():
    _master_writable.mkdir(parents=True, exist_ok=True)

DATA_DIR = _master_writable
TENANTS_DIR = DATA_DIR / "tenants"

# Load .env files (dev convenience — harmless in prod, env vars take priority)
try:
    from dotenv import load_dotenv
    _repo_root = BASE_DIR.parent
    load_dotenv(_repo_root / ".env")
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
TENANTS_DIR.mkdir(exist_ok=True)

# ─── Database ───
# Priority: MASTER_DB_URL env var (Postgres on Render) > local SQLite in writable dir
MASTER_DB_URL = os.getenv("MASTER_DB_URL", f"sqlite+aiosqlite:///{DATA_DIR / 'master.db'}")

# Render Postgres connection strings usually start with "postgres://" (not +asyncpg).
# Normalize so SQLAlchemy async engine works out of the box.
if MASTER_DB_URL.startswith("postgres://") or MASTER_DB_URL.startswith("postgresql://"):
    if "+asyncpg" not in MASTER_DB_URL:
        MASTER_DB_URL = MASTER_DB_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        MASTER_DB_URL = MASTER_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ─── JWT — REQUIRED in production ───
# Priority: MASTER_JWT_SECRET > JWT_SECRET_KEY > generate temp (dev only)
import secrets as _secrets
_jwt_secret = os.getenv("MASTER_JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
if not _jwt_secret:
    _jwt_secret = _secrets.token_hex(32)
    print("\n[WARNING] MASTER_JWT_SECRET not set — using dev fallback")
MASTER_JWT_SECRET = _jwt_secret
MASTER_JWT_ALGORITHM = "HS256"
MASTER_JWT_EXPIRY_HOURS = 24

# Server
MASTER_PORT = int(os.getenv("MASTER_PORT", "8010"))

# Default super admin (set in render.yaml / env for production)
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@platform.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "")
