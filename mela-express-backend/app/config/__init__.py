from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://mela:mela@localhost:5432/mela_express"

    # Telegram
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""  # without @ — used for t.me links; also filled from getMe
    telegram_support_url: str = ""   # optional support chat URL

    # Chapa
    chapa_secret_key: str = ""
    chapa_webhook_secret: str = ""  # used to verify incoming webhook signatures
    chapa_base_url: str = "https://api.chapa.co/v1"

    # Branding — set in .env only (see repo root .env.example). No hardcoded names in code.
    brand_name: str = ""
    brand_short: str = ""
    tracking_prefix: str = ""

    # App — external URLs (Chapa webhooks, public links)
    app_base_url: str = "https://your-domain.example.com"
    # Bot/worker → API inside Docker (e.g. http://api:8000). Falls back to app_base_url.
    internal_api_url: str = ""
    # Public tracking portal (Telegram Mini App host). Telegram web-app buttons
    # require https; non-https URLs fall back to a regular browser-open button.
    public_portal_url: str = "http://localhost:3001"
    environment: str = "development"

    # CORS — explicit allow-list. NEVER combine ["*"] with allow_credentials=True.
    # Set as JSON array in .env, e.g. CORS_ORIGINS='["https://app.example.com"]'
    cors_origins: list[str] = [
        "http://localhost:3000",   # dashboard dev
        "http://localhost:3001",   # public portal dev
    ]

    # JWT & Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Redis & Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # S3 Storage
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket_name: str = "mela-express-assets"
    s3_public_base_url: str = ""

    # SMS
    sms_api_url: str = ""
    sms_api_key: str = ""
    sms_sender_id: str = ""

    # Flight tracking (optional — ETA still works from staff-entered times)
    aviationstack_api_key: str = ""
    opensky_client_id: str = ""
    opensky_client_secret: str = ""

    # Sentry
    sentry_dsn: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
