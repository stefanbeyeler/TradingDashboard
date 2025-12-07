"""Repository classes for database operations."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AppConfig,
    UserPreferences,
    TradingAnalysis,
    PriceForecast,
    Watchlist,
    WatchlistItem,
    PriceAlert,
    TradeJournalEntry,
)

logger = logging.getLogger(__name__)


class ConfigRepository:
    """Repository for app configuration operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> Optional[Any]:
        """Get a configuration value by key."""
        result = await self.session.execute(
            select(AppConfig.value).where(AppConfig.key == key)
        )
        row = result.scalar_one_or_none()
        return row

    async def set(self, key: str, value: Any, description: Optional[str] = None) -> AppConfig:
        """Set a configuration value."""
        result = await self.session.execute(
            select(AppConfig).where(AppConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if config:
            config.value = value
            if description:
                config.description = description
        else:
            config = AppConfig(key=key, value=value, description=description)
            self.session.add(config)

        return config

    async def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        result = await self.session.execute(select(AppConfig))
        configs = result.scalars().all()
        return {c.key: c.value for c in configs}

    async def delete(self, key: str) -> bool:
        """Delete a configuration value."""
        result = await self.session.execute(
            delete(AppConfig).where(AppConfig.key == key)
        )
        return result.rowcount > 0


class UserPreferencesRepository:
    """Repository for user preferences operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: str = "default") -> Optional[UserPreferences]:
        """Get user preferences."""
        result = await self.session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def save(self, prefs: UserPreferences) -> UserPreferences:
        """Save or update user preferences."""
        existing = await self.get(prefs.user_id)
        if existing:
            for key, value in vars(prefs).items():
                if not key.startswith("_") and value is not None:
                    setattr(existing, key, value)
            return existing
        else:
            self.session.add(prefs)
            return prefs

    async def update(self, user_id: str, updates: Dict[str, Any]) -> Optional[UserPreferences]:
        """Update specific preference fields."""
        prefs = await self.get(user_id)
        if prefs:
            for key, value in updates.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
        return prefs


class TradingAnalysisRepository:
    """Repository for trading analysis operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, analysis: TradingAnalysis) -> TradingAnalysis:
        """Create a new trading analysis."""
        self.session.add(analysis)
        return analysis

    async def get(self, analysis_id: UUID) -> Optional[TradingAnalysis]:
        """Get a trading analysis by ID."""
        result = await self.session.execute(
            select(TradingAnalysis).where(TradingAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def get_by_symbol(
        self,
        symbol: str,
        limit: int = 10,
        analysis_type: Optional[str] = None
    ) -> List[TradingAnalysis]:
        """Get analyses for a symbol."""
        query = select(TradingAnalysis).where(TradingAnalysis.symbol == symbol)
        if analysis_type:
            query = query.where(TradingAnalysis.analysis_type == analysis_type)
        query = query.order_by(TradingAnalysis.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent(
        self,
        limit: int = 20,
        analysis_type: Optional[str] = None,
        favorites_only: bool = False
    ) -> List[TradingAnalysis]:
        """Get recent analyses."""
        query = select(TradingAnalysis)

        if analysis_type:
            query = query.where(TradingAnalysis.analysis_type == analysis_type)
        if favorites_only:
            query = query.where(TradingAnalysis.is_favorite == True)

        query = query.order_by(TradingAnalysis.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def toggle_favorite(self, analysis_id: UUID) -> Optional[TradingAnalysis]:
        """Toggle favorite status."""
        analysis = await self.get(analysis_id)
        if analysis:
            analysis.is_favorite = not analysis.is_favorite
        return analysis

    async def delete(self, analysis_id: UUID) -> bool:
        """Delete an analysis."""
        result = await self.session.execute(
            delete(TradingAnalysis).where(TradingAnalysis.id == analysis_id)
        )
        return result.rowcount > 0


class PriceForecastRepository:
    """Repository for price forecast operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, forecast: PriceForecast) -> PriceForecast:
        """Create a new price forecast."""
        self.session.add(forecast)
        return forecast

    async def get_by_symbol(
        self,
        symbol: str,
        limit: int = 10
    ) -> List[PriceForecast]:
        """Get forecasts for a symbol."""
        result = await self.session.execute(
            select(PriceForecast)
            .where(PriceForecast.symbol == symbol)
            .order_by(PriceForecast.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest(self, symbol: str) -> Optional[PriceForecast]:
        """Get the latest forecast for a symbol."""
        result = await self.session.execute(
            select(PriceForecast)
            .where(PriceForecast.symbol == symbol)
            .order_by(PriceForecast.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class WatchlistRepository:
    """Repository for watchlist operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, watchlist: Watchlist) -> Watchlist:
        """Create a new watchlist."""
        self.session.add(watchlist)
        return watchlist

    async def get(self, watchlist_id: UUID) -> Optional[Watchlist]:
        """Get a watchlist by ID."""
        result = await self.session.execute(
            select(Watchlist).where(Watchlist.id == watchlist_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Watchlist]:
        """Get all watchlists."""
        result = await self.session.execute(
            select(Watchlist).order_by(Watchlist.sort_order)
        )
        return list(result.scalars().all())

    async def get_default(self) -> Optional[Watchlist]:
        """Get the default watchlist."""
        result = await self.session.execute(
            select(Watchlist).where(Watchlist.is_default == True)
        )
        return result.scalar_one_or_none()

    async def add_symbol(
        self,
        watchlist_id: UUID,
        symbol: str,
        notes: Optional[str] = None
    ) -> WatchlistItem:
        """Add a symbol to a watchlist."""
        item = WatchlistItem(
            watchlist_id=watchlist_id,
            symbol=symbol,
            notes=notes
        )
        self.session.add(item)
        return item

    async def remove_symbol(self, watchlist_id: UUID, symbol: str) -> bool:
        """Remove a symbol from a watchlist."""
        result = await self.session.execute(
            delete(WatchlistItem).where(
                and_(
                    WatchlistItem.watchlist_id == watchlist_id,
                    WatchlistItem.symbol == symbol
                )
            )
        )
        return result.rowcount > 0

    async def get_items(self, watchlist_id: UUID) -> List[WatchlistItem]:
        """Get all items in a watchlist."""
        result = await self.session.execute(
            select(WatchlistItem)
            .where(WatchlistItem.watchlist_id == watchlist_id)
            .order_by(WatchlistItem.sort_order)
        )
        return list(result.scalars().all())

    async def delete(self, watchlist_id: UUID) -> bool:
        """Delete a watchlist."""
        result = await self.session.execute(
            delete(Watchlist).where(Watchlist.id == watchlist_id)
        )
        return result.rowcount > 0


class PriceAlertRepository:
    """Repository for price alert operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, alert: PriceAlert) -> PriceAlert:
        """Create a new price alert."""
        self.session.add(alert)
        return alert

    async def get(self, alert_id: UUID) -> Optional[PriceAlert]:
        """Get an alert by ID."""
        result = await self.session.execute(
            select(PriceAlert).where(PriceAlert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def get_active(self, symbol: Optional[str] = None) -> List[PriceAlert]:
        """Get all active alerts."""
        query = select(PriceAlert).where(PriceAlert.is_active == True)
        if symbol:
            query = query.where(PriceAlert.symbol == symbol)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def trigger(self, alert_id: UUID, current_value: float) -> Optional[PriceAlert]:
        """Mark an alert as triggered."""
        alert = await self.get(alert_id)
        if alert:
            alert.is_triggered = True
            alert.triggered_at = datetime.utcnow()
            alert.current_value = current_value
            alert.is_active = False
        return alert

    async def delete(self, alert_id: UUID) -> bool:
        """Delete an alert."""
        result = await self.session.execute(
            delete(PriceAlert).where(PriceAlert.id == alert_id)
        )
        return result.rowcount > 0


class TradeJournalRepository:
    """Repository for trade journal operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, entry: TradeJournalEntry) -> TradeJournalEntry:
        """Create a new journal entry."""
        self.session.add(entry)
        return entry

    async def get(self, entry_id: UUID) -> Optional[TradeJournalEntry]:
        """Get a journal entry by ID."""
        result = await self.session.execute(
            select(TradeJournalEntry).where(TradeJournalEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_by_symbol(
        self,
        symbol: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[TradeJournalEntry]:
        """Get journal entries for a symbol."""
        query = select(TradeJournalEntry).where(TradeJournalEntry.symbol == symbol)
        if status:
            query = query.where(TradeJournalEntry.status == status)
        query = query.order_by(TradeJournalEntry.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_open_trades(self) -> List[TradeJournalEntry]:
        """Get all open trades."""
        result = await self.session.execute(
            select(TradeJournalEntry)
            .where(TradeJournalEntry.status == "open")
            .order_by(TradeJournalEntry.entry_time.desc())
        )
        return list(result.scalars().all())

    async def close_trade(
        self,
        entry_id: UUID,
        exit_price: float,
        exit_reason: Optional[str] = None
    ) -> Optional[TradeJournalEntry]:
        """Close a trade."""
        entry = await self.get(entry_id)
        if entry and entry.status == "open":
            entry.exit_price = exit_price
            entry.exit_time = datetime.utcnow()
            entry.exit_reason = exit_reason
            entry.status = "closed"

            # Calculate PnL
            if entry.entry_price and entry.position_size:
                if entry.direction == "LONG":
                    entry.pnl = (float(exit_price) - float(entry.entry_price)) * float(entry.position_size)
                else:
                    entry.pnl = (float(entry.entry_price) - float(exit_price)) * float(entry.position_size)
                entry.pnl_percent = (entry.pnl / (float(entry.entry_price) * float(entry.position_size))) * 100

        return entry

    async def get_statistics(self) -> Dict[str, Any]:
        """Get trading statistics."""
        result = await self.session.execute(
            select(
                func.count(TradeJournalEntry.id).label("total_trades"),
                func.count().filter(TradeJournalEntry.status == "closed").label("closed_trades"),
                func.count().filter(TradeJournalEntry.pnl > 0).label("winning_trades"),
                func.count().filter(TradeJournalEntry.pnl < 0).label("losing_trades"),
                func.sum(TradeJournalEntry.pnl).label("total_pnl"),
            )
        )
        row = result.one()
        return {
            "total_trades": row.total_trades or 0,
            "closed_trades": row.closed_trades or 0,
            "winning_trades": row.winning_trades or 0,
            "losing_trades": row.losing_trades or 0,
            "total_pnl": float(row.total_pnl) if row.total_pnl else 0,
            "win_rate": (row.winning_trades / row.closed_trades * 100) if row.closed_trades else 0,
        }

    async def delete(self, entry_id: UUID) -> bool:
        """Delete a journal entry."""
        result = await self.session.execute(
            delete(TradeJournalEntry).where(TradeJournalEntry.id == entry_id)
        )
        return result.rowcount > 0
