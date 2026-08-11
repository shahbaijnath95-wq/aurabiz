from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


_env_file = os.path.join(os.path.dirname(__file__), ".env") if os.path.exists(os.path.join(os.path.dirname(__file__), ".env")) else os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AI-Powered WhatsApp Business Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = ""  # .env mein set karo — required in production
    JWT_SECRET_KEY: str = ""  # fallback for .env compatibility
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_agent.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # WhatsApp Business API
    WHATSAPP_API_VERSION: str = "v19.0"
    WHATSAPP_BASE_URL: str = "https://graph.facebook.com"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "my_verify_token"
    WHATSAPP_APP_SECRET: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Google Business Profile
    GOOGLE_BUSINESS_API_KEY: str = ""

    # Instagram Graph API
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # PhonePe
    PHONEPE_MERCHANT_ID: str = ""
    PHONEPE_API_KEY: str = ""
    PHONEPE_SALT_KEY: str = ""
    PHONEPE_SALT_INDEX: int = 1
    PHONEPE_BASE_URL: str = "https://api-preprod.phonepe.com/apis/pg-sandbox"

    # Tally
    TALLY_API_URL: str = "https://connect.tallysolutions.com"
    TALLY_API_KEY: str = ""

    # Qdrant (Vector DB for AI memory)
    QDRANT_URL: str = ""  # full URL (e.g. "qdrant" or "http://qdrant:6333"); overrides HOST when set
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "ai_memory"
    QDRANT_KNOWLEDGE_COLLECTION: str = "business_knowledge"  # RAG knowledge base
    QDRANT_ENABLED: bool = True  # False => fall back to in-process embeddings

    # Embeddings (for Knowledge Base / Memory)
    EMBEDDING_PROVIDER: str = "gemini"  # gemini | local
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIM: int = 768  # Gemini text-embedding-004 produces 768-dim vectors

    # LLM
    LLM_PROVIDER: str = "openai"  # openai, anthropic, groq
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"
    GOOGLE_AI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_MODEL: str = "@cf/meta/llama-4-scout-17b-16e-instruct"

    # Resend (Email)
    RESEND_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://127.0.0.1:3001", "http://127.0.0.1:3002", "http://127.0.0.1:3003"]
    FRONTEND_URL: str = "http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Message Delay Defaults (human behavior simulation)
    DEFAULT_MIN_DELAY: int = 3
    DEFAULT_MAX_DELAY: int = 10
    DEFAULT_TYPING_DURATION: int = 3


settings = Settings()
