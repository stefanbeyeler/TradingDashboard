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


# Symbol Management Models (via KITradingModel)
class SymbolCategory(str, Enum):
    """Categories for trading symbols."""
    FOREX = "forex"
    CRYPTO = "crypto"
    STOCK = "stock"
    INDEX = "index"
    COMMODITY = "commodity"
    ETF = "etf"
    OTHER = "other"


class SymbolStatus(str, Enum):
    """Status of a trading symbol."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class SymbolSubcategory(str, Enum):
    """Sub-categories for more granular symbol classification."""
    # Forex subcategories
    MAJOR = "major"
    MINOR = "minor"
    EXOTIC = "exotic"
    # Crypto subcategories
    LARGE_CAP = "large_cap"
    MID_CAP = "mid_cap"
    SMALL_CAP = "small_cap"
    DEFI = "defi"
    MEME = "meme"
    STABLECOIN = "stablecoin"
    # Stock subcategories
    TECH = "tech"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    ENERGY = "energy"
    CONSUMER = "consumer"
    INDUSTRIAL = "industrial"
    # Index subcategories
    GLOBAL = "global"
    REGIONAL = "regional"
    SECTOR = "sector"
    # Commodity subcategories
    PRECIOUS_METAL = "precious_metal"
    BASE_METAL = "base_metal"
    AGRICULTURE = "agriculture"
    ENERGY_COMMODITY = "energy_commodity"
    # General
    OTHER = "other"



class ManagedSymbol(BaseModel):
    """A managed trading symbol with metadata."""
    symbol: str
    display_name: Optional[str] = None
    category: SymbolCategory = SymbolCategory.FOREX
    subcategory: Optional[SymbolSubcategory] = None
    status: SymbolStatus = SymbolStatus.ACTIVE
    description: Optional[str] = None
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    pip_value: Optional[float] = None
    min_lot_size: Optional[float] = 0.01
    max_lot_size: Optional[float] = 100.0
    has_timescaledb_data: bool = False
    first_data_timestamp: Optional[datetime] = None
    last_data_timestamp: Optional[datetime] = None
    total_records: Optional[int] = None
    has_nhits_model: bool = False
    nhits_model_trained_at: Optional[datetime] = None
    is_favorite: bool = False
    notes: Optional[str] = None
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SymbolCreateRequest(BaseModel):
    """Request to create a new managed symbol."""
    symbol: str
    display_name: Optional[str] = None
    category: SymbolCategory = SymbolCategory.FOREX
    subcategory: Optional[SymbolSubcategory] = None
    description: Optional[str] = None
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    pip_value: Optional[float] = None
    min_lot_size: Optional[float] = 0.01
    max_lot_size: Optional[float] = 100.0
    notes: Optional[str] = None
    tags: List[str] = []


class SymbolUpdateRequest(BaseModel):
    """Request to update an existing managed symbol."""
    display_name: Optional[str] = None
    category: Optional[SymbolCategory] = None
    subcategory: Optional[SymbolSubcategory] = None
    status: Optional[SymbolStatus] = None
    description: Optional[str] = None
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    pip_value: Optional[float] = None
    min_lot_size: Optional[float] = None
    max_lot_size: Optional[float] = None
    is_favorite: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class SymbolImportResult(BaseModel):
    """Result of importing symbols from TimescaleDB."""
    total_found: int
    imported: int
    updated: int
    skipped: int
    errors: List[str] = []
    symbols: List[str] = []


class SymbolStats(BaseModel):
    """Statistics about managed symbols."""
    total_symbols: int
    active_symbols: int
    inactive_symbols: int
    suspended_symbols: int
    with_timescaledb_data: int
    with_nhits_model: int
    by_category: Dict[str, int]
    by_subcategory: Dict[str, int] = {}
    favorites_count: int
