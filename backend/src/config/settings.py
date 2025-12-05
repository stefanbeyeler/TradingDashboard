"""Configuration settings for TradingDashboard backend."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = "0.0.0.0"
    port: int = 3010
    debug: bool = True

    # KITradingModel API
    kitrading_api_url: str = "http://localhost:3011/api/v1"
    kitrading_timeout: int = 120

    # CoinGecko (free, no key required)
    coingecko_api_url: str = "https://api.coingecko.com/api/v3"

    # Binance
    binance_api_key: str = ""
    binance_api_secret: str = ""

    # Alpha Vantage (free tier available)
    alpha_vantage_api_key: str = "demo"

    # Finnhub
    finnhub_api_key: str = ""

    # News API
    news_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # CORS - accepts both string and list
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://localhost:3010"

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
