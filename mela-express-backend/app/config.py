from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://mela:mela@localhost:5432/mela_express"

    # Telegram
    telegram_bot_token: str = ""

    # Chapa
    chapa_secret_key: str = ""
    chapa_webhook_secret: str = ""  # used to verify incoming webhook signatures
    chapa_base_url: str = "https://api.chapa.co/v1"

    # App
    app_base_url: str = "https://your-domain.example.com"  # used for Chapa callback/return URLs
    environment: str = "development"

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
    sms_sender_id: str = "MelaExpress"

    # Sentry
    sentry_dsn: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
