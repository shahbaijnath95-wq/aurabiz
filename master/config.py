"""Master Backend Configuration"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TENANTS_DIR = DATA_DIR / "tenants"

# Load .env file from repo root (if exists)
from dotenv import load_dotenv
_repo_root = BASE_DIR.parent
load_dotenv(_repo_root / ".env")
load_dotenv(BASE_DIR / ".env")  # master/.env overrides root .env

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
TENANTS_DIR.mkdir(exist_ok=True)

# Master Database (SQLite for simplicity, switch to PostgreSQL for production)
MASTER_DB_URL = os.getenv("MASTER_DB_URL", f"sqlite+aiosqlite:///{DATA_DIR / 'master.db'}")

# JWT - SECURE secret (do not use default in production)
# Priority: MASTER_JWT_SECRET > JWT_SECRET_KEY > generate temp
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

# Default super admin
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@platform.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")
