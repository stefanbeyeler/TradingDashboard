"""Market data models for TradingDashboard."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AssetType(str, Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCK = "stock"
    COMMODITY = "commodity"


class TimeFrame(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


class OHLCV(BaseModel):
    """OHLCV candlestick data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketTicker(BaseModel):
    """Real-time market ticker data."""
    symbol: str
    name: Optional[str] = None
    asset_type: AssetType
    price: float
    change_24h: Optional[float] = None
    change_percent_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class OrderBookEntry(BaseModel):
    """Single order book entry."""
    price: float
    quantity: float


class OrderBook(BaseModel):
    """Order book with bids and asks."""
    symbol: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketNews(BaseModel):
    """Market news article."""
    title: str
    description: Optional[str] = None
    url: str
    source: str
    published_at: datetime
    sentiment: Optional[str] = None  # positive, negative, neutral
    related_symbols: List[str] = []


class TechnicalIndicator(BaseModel):
    """Technical indicator value."""
    name: str
    value: float
    signal: Optional[str] = None  # buy, sell, neutral
    description: Optional[str] = None


class MarketOverview(BaseModel):
    """Complete market overview for a symbol."""
    ticker: MarketTicker
    candles: List[OHLCV] = []
    indicators: List[TechnicalIndicator] = []
    news: List[MarketNews] = []
    order_book: Optional[OrderBook] = None


# KITradingModel Integration Models
class KIAnalysisRequest(BaseModel):
    """Request for KI Trading analysis."""
    symbol: str
    lookback_days: int = 30
    include_technical: bool = True
    include_forecast: bool = True
    strategy_id: Optional[str] = None


class KIRecommendation(BaseModel):
    """KI Trading recommendation response."""
    symbol: str
    direction: str  # LONG, SHORT, NEUTRAL
    confidence_score: int = Field(ge=0, le=100)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    rationale: Optional[str] = None
    key_levels: Optional[str] = None  # Can be string description or None
    risks: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ForecastPoint(BaseModel):
    """Single forecast point."""
    timestamp: datetime
    predicted_price: float
    confidence_low: Optional[float] = None
    confidence_high: Optional[float] = None


class KIForecast(BaseModel):
    """KI Trading NHITS forecast response."""
    symbol: str
    current_price: float
    predictions: List[ForecastPoint]
    trend_probability_up: Optional[float] = None
    trend_probability_down: Optional[float] = None
    model_confidence: Optional[float] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class DashboardData(BaseModel):
    """Complete dashboard data aggregation."""
    watchlist: List[MarketTicker] = []
    featured_analysis: Optional[KIRecommendation] = None
    featured_forecast: Optional[KIForecast] = None
    market_news: List[MarketNews] = []
    system_status: Dict[str, Any] = {}
