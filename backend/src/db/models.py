"""SQLAlchemy models for TradingDashboard database."""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    ForeignKey, Numeric, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class AppConfig(Base):
    """Application configuration key-value store."""
    __tablename__ = "app_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPreferences(Base):
    """User preferences and settings."""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), unique=True, default="default")
    theme = Column(String(50), default="dark")
    language = Column(String(10), default="de")
    default_timeframe = Column(String(10), default="1h")
    default_symbol = Column(String(50), default="EURUSD")
    notifications_enabled = Column(Boolean, default=True)
    auto_refresh_interval = Column(Integer, default=30)
    chart_settings = Column(JSONB, default=dict)
    dashboard_layout = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class TradingAnalysis(Base):
    """Saved trading analyses from KI recommendations."""
    __tablename__ = "trading_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # 'ki_recommendation', 'technical', 'forecast'
    direction = Column(String(20))  # 'LONG', 'SHORT', 'NEUTRAL'
    confidence_score = Column(Integer)
    entry_price = Column(Numeric(20, 8))
    stop_loss = Column(Numeric(20, 8))
    take_profit_1 = Column(Numeric(20, 8))
    take_profit_2 = Column(Numeric(20, 8))
    take_profit_3 = Column(Numeric(20, 8))
    risk_reward_ratio = Column(Numeric(10, 2))
    rationale = Column(Text)
    key_levels = Column(Text)
    risks = Column(JSONB, default=list)
    raw_response = Column(JSONB)
    strategy_id = Column(String(100))
    is_favorite = Column(Boolean, default=False, index=True)
    tags = Column(JSONB, default=list)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Relationships
    journal_entries = relationship("TradeJournalEntry", back_populates="analysis")

    __table_args__ = (
        Index("idx_trading_analyses_type", "analysis_type"),
    )


class PriceForecast(Base):
    """Price forecast history from NHITS model."""
    __tablename__ = "price_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol = Column(String(50), nullable=False, index=True)
    current_price = Column(Numeric(20, 8), nullable=False)
    horizon = Column(Integer, nullable=False)  # forecast horizon in periods
    model_type = Column(String(50), default="nhits")
    predictions = Column(JSONB, nullable=False)  # array of prediction points
    trend_probability_up = Column(Numeric(5, 4))
    trend_probability_down = Column(Numeric(5, 4))
    model_confidence = Column(Numeric(5, 4))
    raw_response = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class Watchlist(Base):
    """User watchlists for symbols."""
    __tablename__ = "watchlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    """Items within a watchlist."""
    __tablename__ = "watchlist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    watchlist_id = Column(UUID(as_uuid=True), ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    notes = Column(Text)
    alert_price_above = Column(Numeric(20, 8))
    alert_price_below = Column(Numeric(20, 8))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),
    )


class PriceAlert(Base):
    """Price alerts for symbols."""
    __tablename__ = "price_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # 'price_above', 'price_below', 'percent_change'
    target_value = Column(Numeric(20, 8), nullable=False)
    current_value = Column(Numeric(20, 8))
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    notification_sent = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class TradeJournalEntry(Base):
    """Trade journal for tracking trades."""
    __tablename__ = "trade_journal"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol = Column(String(50), nullable=False, index=True)
    direction = Column(String(20), nullable=False)  # 'LONG', 'SHORT'
    entry_price = Column(Numeric(20, 8), nullable=False)
    exit_price = Column(Numeric(20, 8))
    position_size = Column(Numeric(20, 8))
    stop_loss = Column(Numeric(20, 8))
    take_profit = Column(Numeric(20, 8))
    pnl = Column(Numeric(20, 8))
    pnl_percent = Column(Numeric(10, 4))
    status = Column(String(20), default="open", index=True)  # 'open', 'closed', 'cancelled'
    entry_reason = Column(Text)
    exit_reason = Column(Text)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("trading_analyses.id"), nullable=True)
    screenshots = Column(JSONB, default=list)
    lessons_learned = Column(Text)
    tags = Column(JSONB, default=list)
    entry_time = Column(DateTime(timezone=True))
    exit_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    analysis = relationship("TradingAnalysis", back_populates="journal_entries")
