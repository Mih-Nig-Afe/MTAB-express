"""
Central config, loaded from environment variables.
Copy .env.example to .env and fill these in before running anything.
"""
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

    class Config:
        env_file = ".env"


settings = Settings()
