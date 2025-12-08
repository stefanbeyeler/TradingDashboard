"""Background scheduler service for periodic favorite symbol analyses."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from ..config import settings
from .kitrading_service import kitrading_service
from ..db import DatabaseSession
from ..db.models import TradingAnalysis

logger = logging.getLogger(__name__)


class ScheduledAnalysis:
    """Represents a scheduled analysis result for a favorite symbol."""

    def __init__(
        self,
        symbol: str,
        direction: str,
        confidence_score: int,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit_1: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
        rationale: Optional[str] = None,
        category: Optional[str] = None,
        analyzed_at: Optional[datetime] = None,
        indicators: Optional[Dict[str, Any]] = None,
    ):
        self.symbol = symbol
        self.direction = direction
        self.confidence_score = confidence_score
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit_1 = take_profit_1
        self.risk_reward_ratio = risk_reward_ratio
        self.rationale = rationale
        self.category = category
        self.analyzed_at = analyzed_at or datetime.utcnow()
        self.indicators = indicators or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "confidence_score": self.confidence_score,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "risk_reward_ratio": self.risk_reward_ratio,
            "rationale": self.rationale,
            "category": self.category,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "indicators": self.indicators,
        }


class SchedulerService:
    """Service for scheduling periodic analyses of favorite symbols."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._latest_analyses: Dict[str, ScheduledAnalysis] = {}
        self._last_run: Optional[datetime] = None
        self._interval_minutes: int = 30  # Default: analyze every 30 minutes
        self._is_analyzing = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def interval_minutes(self) -> int:
        return self._interval_minutes

    @interval_minutes.setter
    def interval_minutes(self, value: int):
        self._interval_minutes = max(5, min(value, 1440))  # 5 min to 24 hours

    @property
    def last_run(self) -> Optional[datetime]:
        return self._last_run

    @property
    def next_run(self) -> Optional[datetime]:
        if self._last_run and self._running:
            return self._last_run + timedelta(minutes=self._interval_minutes)
        return None

    def get_latest_analyses(self) -> List[Dict[str, Any]]:
        """Get the latest scheduled analyses for all favorite symbols."""
        return [analysis.to_dict() for analysis in self._latest_analyses.values()]

    def get_analysis_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the latest scheduled analysis for a specific symbol."""
        analysis = self._latest_analyses.get(symbol)
        return analysis.to_dict() if analysis else None

    async def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Scheduler started with {self._interval_minutes} minute interval")

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Scheduler stopped")

    async def _run_loop(self):
        """Main scheduler loop."""
        # Run immediately on start
        await self._analyze_favorites()

        while self._running:
            try:
                # Wait for the interval
                await asyncio.sleep(self._interval_minutes * 60)

                if self._running:
                    await self._analyze_favorites()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def run_now(self) -> List[Dict[str, Any]]:
        """Run analysis immediately (manual trigger)."""
        await self._analyze_favorites()
        return self.get_latest_analyses()

    async def _analyze_favorites(self):
        """Analyze all favorite symbols."""
        if self._is_analyzing:
            logger.warning("Analysis already in progress, skipping")
            return

        self._is_analyzing = True
        logger.info("Starting scheduled analysis of favorite symbols")

        try:
            # Get favorite symbols from KITradingModel
            favorites = await kitrading_service.get_managed_symbols(favorites_only=True)

            if not favorites:
                logger.info("No favorite symbols to analyze")
                self._last_run = datetime.utcnow()
                return

            logger.info(f"Analyzing {len(favorites)} favorite symbols")

            # Analyze each symbol
            for symbol_data in favorites:
                try:
                    symbol = symbol_data.symbol
                    category = symbol_data.category

                    # Get quick recommendation (without LLM for speed)
                    recommendation = await kitrading_service.get_recommendation(
                        symbol=symbol,
                        use_llm=False,
                    )

                    if recommendation:
                        analysis = ScheduledAnalysis(
                            symbol=symbol,
                            direction=recommendation.direction,
                            confidence_score=recommendation.confidence_score or 50,
                            entry_price=recommendation.entry_price,
                            stop_loss=recommendation.stop_loss,
                            take_profit_1=recommendation.take_profit_1,
                            risk_reward_ratio=recommendation.risk_reward_ratio,
                            rationale=recommendation.rationale,
                            category=category,
                            analyzed_at=datetime.utcnow(),
                            indicators=recommendation.indicators or {},
                        )
                        self._latest_analyses[symbol] = analysis
                        logger.debug(f"Analyzed {symbol}: {recommendation.direction} ({recommendation.confidence_score}%)")
                    else:
                        logger.warning(f"No recommendation received for {symbol}")

                    # Small delay between API calls to avoid rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Failed to analyze {symbol_data.symbol}: {e}")

            self._last_run = datetime.utcnow()
            logger.info(f"Scheduled analysis completed for {len(self._latest_analyses)} symbols")

            # Optionally save to database
            await self._save_analyses_to_db()

        except Exception as e:
            logger.error(f"Error during scheduled analysis: {e}")
        finally:
            self._is_analyzing = False

    async def _save_analyses_to_db(self):
        """Save the latest analyses to the database."""
        try:
            async with DatabaseSession() as session:
                for symbol, analysis in self._latest_analyses.items():
                    db_analysis = TradingAnalysis(
                        id=uuid4(),
                        symbol=analysis.symbol,
                        timeframe="scheduled",
                        analysis_type="scheduled_quick",
                        direction=analysis.direction,
                        confidence_score=analysis.confidence_score,
                        entry_price=analysis.entry_price,
                        stop_loss=analysis.stop_loss,
                        take_profit_1=analysis.take_profit_1,
                        risk_reward_ratio=analysis.risk_reward_ratio,
                        rationale=analysis.rationale,
                        raw_response={"indicators": analysis.indicators, "category": analysis.category},
                        created_at=analysis.analyzed_at,
                    )
                    session.add(db_analysis)
                await session.commit()
                logger.debug("Saved scheduled analyses to database")
        except Exception as e:
            logger.error(f"Failed to save analyses to database: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self._running,
            "is_analyzing": self._is_analyzing,
            "interval_minutes": self._interval_minutes,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "analyzed_symbols": len(self._latest_analyses),
        }


# Singleton instance
scheduler_service = SchedulerService()
