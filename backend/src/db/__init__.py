"""Database module for TradingDashboard."""
from .database import (
    get_db,
    init_db,
    close_db,
    DatabaseSession,
)
from .models import (
    Base,
    AppConfig,
    UserPreferences,
    TradingAnalysis,
    PriceForecast,
    Watchlist,
    WatchlistItem,
    PriceAlert,
    TradeJournalEntry,
)

__all__ = [
    # Database connection
    "get_db",
    "init_db",
    "close_db",
    "DatabaseSession",
    # Models
    "Base",
    "AppConfig",
    "UserPreferences",
    "TradingAnalysis",
    "PriceForecast",
    "Watchlist",
    "WatchlistItem",
    "PriceAlert",
    "TradeJournalEntry",
]
