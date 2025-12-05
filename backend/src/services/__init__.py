"""Services module for external API integrations."""
from .kitrading_service import kitrading_service, KITradingService
from .coingecko_service import coingecko_service, CoinGeckoService
from .alphavantage_service import alphavantage_service, AlphaVantageService
from .binance_service import binance_service, BinanceService
from .news_service import news_service, NewsService

__all__ = [
    "kitrading_service",
    "KITradingService",
    "coingecko_service",
    "CoinGeckoService",
    "alphavantage_service",
    "AlphaVantageService",
    "binance_service",
    "BinanceService",
    "news_service",
    "NewsService",
]
