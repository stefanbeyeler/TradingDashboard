"""Pydantic schemas for database API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# App Configuration Schemas
# ============================================================================

class ConfigValueRequest(BaseModel):
    """Request to set a configuration value."""
    value: Any
    description: Optional[str] = None


class ConfigResponse(BaseModel):
    """Response for a single configuration entry."""
    key: str
    value: Any
    description: Optional[str] = None
    updated_at: Optional[datetime] = None


class ConfigListResponse(BaseModel):
    """Response for all configuration entries."""
    configs: Dict[str, Any]


# ============================================================================
# User Preferences Schemas
# ============================================================================

class UserPreferencesRequest(BaseModel):
    """Request to update user preferences."""
    theme: Optional[str] = None
    language: Optional[str] = None
    default_timeframe: Optional[str] = None
    default_symbol: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    auto_refresh_interval: Optional[int] = Field(None, ge=5, le=300)
    chart_settings: Optional[Dict[str, Any]] = None
    dashboard_layout: Optional[Dict[str, Any]] = None


class UserPreferencesResponse(BaseModel):
    """Response for user preferences."""
    id: UUID
    user_id: str
    theme: str
    language: str
    default_timeframe: str
    default_symbol: str
    notifications_enabled: bool
    auto_refresh_interval: int
    chart_settings: Dict[str, Any]
    dashboard_layout: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Trading Analysis Schemas
# ============================================================================

class TradingAnalysisCreate(BaseModel):
    """Request to create a trading analysis."""
    symbol: str
    timeframe: str = "1h"
    analysis_type: str = "ki_recommendation"
    direction: Optional[str] = None
    confidence_score: Optional[int] = Field(None, ge=0, le=100)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    rationale: Optional[str] = None
    key_levels: Optional[str] = None
    risks: List[str] = []
    raw_response: Optional[Dict[str, Any]] = None
    strategy_id: Optional[str] = None
    is_favorite: bool = False
    tags: List[str] = []
    notes: Optional[str] = None


class TradingAnalysisResponse(BaseModel):
    """Response for a trading analysis."""
    id: UUID
    symbol: str
    timeframe: str
    analysis_type: str
    direction: Optional[str]
    confidence_score: Optional[int]
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit_1: Optional[float]
    take_profit_2: Optional[float]
    take_profit_3: Optional[float]
    risk_reward_ratio: Optional[float]
    rationale: Optional[str]
    key_levels: Optional[str]
    risks: List[str]
    strategy_id: Optional[str]
    is_favorite: bool
    tags: List[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TradingAnalysisListResponse(BaseModel):
    """Response for list of trading analyses."""
    analyses: List[TradingAnalysisResponse]
    total: int


# ============================================================================
# Price Forecast Schemas
# ============================================================================

class PredictionPoint(BaseModel):
    """Single prediction point."""
    timestamp: datetime
    predicted_price: float
    confidence_low: Optional[float] = None
    confidence_high: Optional[float] = None


class PriceForecastCreate(BaseModel):
    """Request to save a price forecast."""
    symbol: str
    current_price: float
    horizon: int
    model_type: str = "nhits"
    predictions: List[PredictionPoint]
    trend_probability_up: Optional[float] = None
    trend_probability_down: Optional[float] = None
    model_confidence: Optional[float] = None
    raw_response: Optional[Dict[str, Any]] = None


class PriceForecastResponse(BaseModel):
    """Response for a price forecast."""
    id: UUID
    symbol: str
    current_price: float
    horizon: int
    model_type: str
    predictions: List[Dict[str, Any]]
    trend_probability_up: Optional[float]
    trend_probability_down: Optional[float]
    model_confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Watchlist Schemas
# ============================================================================

class WatchlistCreate(BaseModel):
    """Request to create a watchlist."""
    name: str
    description: Optional[str] = None
    is_default: bool = False


class WatchlistUpdate(BaseModel):
    """Request to update a watchlist."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None


class WatchlistItemAdd(BaseModel):
    """Request to add item to watchlist."""
    symbol: str
    notes: Optional[str] = None
    alert_price_above: Optional[float] = None
    alert_price_below: Optional[float] = None


class WatchlistItemResponse(BaseModel):
    """Response for watchlist item."""
    id: UUID
    symbol: str
    sort_order: int
    notes: Optional[str]
    alert_price_above: Optional[float]
    alert_price_below: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """Response for a watchlist."""
    id: UUID
    name: str
    description: Optional[str]
    is_default: bool
    sort_order: int
    items: List[WatchlistItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Price Alert Schemas
# ============================================================================

class PriceAlertCreate(BaseModel):
    """Request to create a price alert."""
    symbol: str
    alert_type: str  # price_above, price_below, percent_change
    target_value: float
    notes: Optional[str] = None


class PriceAlertResponse(BaseModel):
    """Response for a price alert."""
    id: UUID
    symbol: str
    alert_type: str
    target_value: float
    current_value: Optional[float]
    is_triggered: bool
    triggered_at: Optional[datetime]
    is_active: bool
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Trade Journal Schemas
# ============================================================================

class TradeJournalCreate(BaseModel):
    """Request to create a trade journal entry."""
    symbol: str
    direction: str  # LONG, SHORT
    entry_price: float
    position_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_reason: Optional[str] = None
    analysis_id: Optional[UUID] = None
    tags: List[str] = []
    entry_time: Optional[datetime] = None


class TradeJournalUpdate(BaseModel):
    """Request to update a trade journal entry."""
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    lessons_learned: Optional[str] = None
    screenshots: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class TradeJournalClose(BaseModel):
    """Request to close a trade."""
    exit_price: float
    exit_reason: Optional[str] = None


class TradeJournalResponse(BaseModel):
    """Response for a trade journal entry."""
    id: UUID
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float]
    position_size: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    status: str
    entry_reason: Optional[str]
    exit_reason: Optional[str]
    analysis_id: Optional[UUID]
    lessons_learned: Optional[str]
    tags: List[str]
    entry_time: Optional[datetime]
    exit_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeStatisticsResponse(BaseModel):
    """Response for trade statistics."""
    total_trades: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    win_rate: float


# ============================================================================
# Backup/Restore Schemas
# ============================================================================

class BackupMetadata(BaseModel):
    """Metadata about the backup."""
    version: str = "1.0"
    created_at: datetime
    tables_included: List[str]
    record_counts: Dict[str, int]


class BackupData(BaseModel):
    """Full backup data structure."""
    metadata: BackupMetadata
    config: Dict[str, Any] = {}
    user_preferences: List[Dict[str, Any]] = []
    watchlists: List[Dict[str, Any]] = []
    price_alerts: List[Dict[str, Any]] = []
    trading_analyses: List[Dict[str, Any]] = []
    trade_journal: List[Dict[str, Any]] = []


class RestoreRequest(BaseModel):
    """Request to restore from backup."""
    backup: BackupData
    restore_config: bool = True
    restore_preferences: bool = True
    restore_watchlists: bool = True
    restore_alerts: bool = True
    restore_analyses: bool = True
    restore_journal: bool = True
    clear_existing: bool = False


class RestoreResult(BaseModel):
    """Result of restore operation."""
    success: bool
    records_restored: Dict[str, int]
    errors: List[str] = []
