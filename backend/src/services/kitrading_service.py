"""KITradingModel API integration service."""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..config import settings
from ..models import (
    KIRecommendation,
    KIForecast,
    ForecastPoint,
    ManagedSymbol,
    SymbolImportResult,
    SymbolStats,
    SymbolCategory,
    SymbolStatus,
)

logger = logging.getLogger(__name__)


class KITradingService:
    """Service for interacting with KITradingModel API."""

    def __init__(self):
        self.base_url = settings.kitrading_api_url
        self.timeout = settings.kitrading_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check KITradingModel service health."""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"KITradingModel health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_symbols(self) -> List[str]:
        """Get available trading symbols."""
        try:
            client = await self._get_client()
            response = await client.get("/symbols")
            response.raise_for_status()
            data = response.json()
            return data.get("symbols", [])
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []

    async def get_recommendation(
        self,
        symbol: str,
        use_llm: bool = False,
        strategy_id: Optional[str] = None,
    ) -> Optional[KIRecommendation]:
        """Get trading recommendation for a symbol."""
        try:
            client = await self._get_client()
            params = {"use_llm": use_llm}
            if strategy_id:
                params["strategy_id"] = strategy_id

            response = await client.get(
                f"/recommendation/{symbol}",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            # Handle key_levels - can be string or list
            key_levels = data.get("key_levels")
            if isinstance(key_levels, list):
                key_levels = ", ".join(str(level) for level in key_levels) if key_levels else None

            # Handle confidence - can be score (int) or text (high/medium/low)
            confidence = data.get("confidence_score")
            if confidence is None:
                conf_text = data.get("confidence", "medium")
                if isinstance(conf_text, str):
                    confidence = {"high": 80, "medium": 60, "low": 40}.get(conf_text.lower(), 50)
                else:
                    confidence = conf_text if isinstance(conf_text, int) else 50

            # Extract technical indicators
            indicators = data.get("indicators") or data.get("technical_indicators") or {}
            if not indicators:
                # Try to build indicators from individual fields
                indicators = {}
                if "rsi" in data or "RSI" in data:
                    indicators["RSI"] = data.get("rsi") or data.get("RSI")
                if "macd" in data or "MACD" in data:
                    indicators["MACD"] = data.get("macd") or data.get("MACD")
                if "sma_20" in data or "SMA_20" in data:
                    indicators["SMA 20"] = data.get("sma_20") or data.get("SMA_20")
                if "sma_50" in data or "SMA_50" in data:
                    indicators["SMA 50"] = data.get("sma_50") or data.get("SMA_50")
                if "ema_12" in data or "EMA_12" in data:
                    indicators["EMA 12"] = data.get("ema_12") or data.get("EMA_12")
                if "ema_26" in data or "EMA_26" in data:
                    indicators["EMA 26"] = data.get("ema_26") or data.get("EMA_26")
                if "atr" in data or "ATR" in data:
                    indicators["ATR"] = data.get("atr") or data.get("ATR")
                if "volume" in data:
                    indicators["Volume"] = data.get("volume")
                if "trend" in data:
                    indicators["Trend"] = data.get("trend")

            # Parse indicators from trend_analysis text if still empty
            if not indicators:
                import re
                trend_analysis = data.get("trend_analysis", "")
                key_levels_str = data.get("key_levels", "")

                # Helper to safely parse float (handles trailing dots)
                def safe_float(s):
                    try:
                        return float(s.rstrip('.'))
                    except (ValueError, AttributeError):
                        return None

                # Extract RSI from trend_analysis (e.g., "RSI bei 59.7")
                rsi_match = re.search(r'RSI\s*(?:bei|at|:)?\s*([\d.]+)', trend_analysis, re.IGNORECASE)
                if rsi_match:
                    val = safe_float(rsi_match.group(1))
                    if val is not None:
                        indicators["RSI"] = val

                # Extract trend
                trend_match = re.search(r'Trend:\s*(\w+)', trend_analysis, re.IGNORECASE)
                if trend_match:
                    indicators["Trend"] = trend_match.group(1).capitalize()

                # Extract BB Upper/Lower from key_levels
                bb_upper_match = re.search(r'BB Upper:\s*([\d.]+)', key_levels_str, re.IGNORECASE)
                if bb_upper_match:
                    val = safe_float(bb_upper_match.group(1))
                    if val is not None:
                        indicators["BB Upper"] = val

                bb_lower_match = re.search(r'BB Lower:\s*([\d.]+)', key_levels_str, re.IGNORECASE)
                if bb_lower_match:
                    val = safe_float(bb_lower_match.group(1))
                    if val is not None:
                        indicators["BB Lower"] = val

                sma200_match = re.search(r'SMA200:\s*([\d.]+)', key_levels_str, re.IGNORECASE)
                if sma200_match:
                    val = safe_float(sma200_match.group(1))
                    if val is not None:
                        indicators["SMA 200"] = val

                # Extract signal type
                if data.get("signal"):
                    indicators["Signal"] = data.get("signal").upper()

                # Extract timeframe
                if data.get("timeframe"):
                    indicators["Timeframe"] = data.get("timeframe")

            return KIRecommendation(
                symbol=symbol,
                direction=data.get("direction", data.get("signal", "NEUTRAL")).upper(),
                confidence_score=confidence,
                entry_price=data.get("entry_price"),
                stop_loss=data.get("stop_loss"),
                take_profit_1=data.get("take_profit_1"),
                take_profit_2=data.get("take_profit_2"),
                take_profit_3=data.get("take_profit_3"),
                risk_reward_ratio=data.get("risk_reward_ratio"),
                rationale=data.get("rationale", data.get("reasoning", data.get("trade_rationale"))),
                key_levels=key_levels,
                risks=data.get("risks", []),
                indicators=indicators if indicators else None,
            )
        except Exception as e:
            logger.error(f"Failed to get recommendation for {symbol}: {e}")
            return None

    async def analyze(
        self,
        symbol: str,
        lookback_days: int = 30,
        include_technical: bool = True,
        strategy_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get full market analysis with LLM."""
        try:
            client = await self._get_client()
            payload = {
                "symbol": symbol,
                "lookback_days": lookback_days,
                "include_technical": include_technical,
            }
            if strategy_id:
                payload["strategy_id"] = strategy_id

            response = await client.post("/analyze", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            return None

    async def get_forecast(
        self,
        symbol: str,
        horizon: int = 24,
    ) -> Optional[KIForecast]:
        """Get NHITS price forecast."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"/forecast/{symbol}",
                params={"horizon": horizon},
            )
            response.raise_for_status()
            data = response.json()

            predictions = []

            # Handle new format: predicted_prices as array of floats
            if "predicted_prices" in data and data["predicted_prices"]:
                predicted_prices = data["predicted_prices"]
                confidence_low = data.get("confidence_low", [])
                confidence_high = data.get("confidence_high", [])
                forecast_timestamp = datetime.fromisoformat(
                    data["forecast_timestamp"].replace("Z", "+00:00")
                ) if "forecast_timestamp" in data else datetime.utcnow()

                for i, price in enumerate(predicted_prices):
                    # Calculate timestamp: forecast_timestamp + i hours
                    point_timestamp = forecast_timestamp + timedelta(hours=i + 1)
                    predictions.append(ForecastPoint(
                        timestamp=point_timestamp,
                        predicted_price=price,
                        confidence_low=confidence_low[i] if i < len(confidence_low) else None,
                        confidence_high=confidence_high[i] if i < len(confidence_high) else None,
                    ))
            # Handle legacy format: predictions as list of objects
            elif "predictions" in data:
                for pred in data["predictions"]:
                    predictions.append(ForecastPoint(
                        timestamp=datetime.fromisoformat(pred["timestamp"].replace("Z", "+00:00"))
                        if isinstance(pred["timestamp"], str)
                        else pred["timestamp"],
                        predicted_price=pred["price"],
                        confidence_low=pred.get("confidence_low"),
                        confidence_high=pred.get("confidence_high"),
                    ))

            return KIForecast(
                symbol=symbol,
                current_price=data.get("current_price", 0),
                predictions=predictions,
                trend_probability_up=data.get("trend_up_probability", data.get("trend_probability_up")),
                trend_probability_down=data.get("trend_down_probability", data.get("trend_probability_down")),
                model_confidence=data.get("model_confidence"),
            )
        except Exception as e:
            logger.error(f"Failed to get forecast for {symbol}: {e}")
            return None

    async def get_strategies(self) -> List[Dict[str, Any]]:
        """Get available trading strategies."""
        try:
            client = await self._get_client()
            response = await client.get("/strategies")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get strategies: {e}")
            return []

    async def get_forecast_models(self) -> List[Dict[str, Any]]:
        """Get available NHITS forecast models."""
        try:
            client = await self._get_client()
            response = await client.get("/forecast/models")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get forecast models: {e}")
            return []

    async def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        try:
            client = await self._get_client()
            response = await client.get("/rag/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get RAG stats: {e}")
            return {}

    async def query_rag(
        self,
        query: str,
        symbol: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Query RAG system for relevant documents."""
        try:
            client = await self._get_client()
            params = {"query": query, "n_results": n_results}
            if symbol:
                params["symbol"] = symbol

            response = await client.get("/rag/query", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to query RAG: {e}")
            return []

    async def get_query_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get query logs history."""
        try:
            client = await self._get_client()
            params = {"limit": limit, "offset": offset}
            if symbol:
                params["symbol"] = symbol

            response = await client.get("/query-logs", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get query logs: {e}")
            return {"logs": [], "total": 0}

    # ==================== Symbol Management ====================

    async def get_managed_symbols(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        favorites_only: bool = False,
        with_data_only: bool = False,
    ) -> List[ManagedSymbol]:
        """Get all managed symbols with optional filtering."""
        try:
            client = await self._get_client()
            params = {}
            if category:
                params["category"] = category
            if status:
                params["status"] = status
            if favorites_only:
                params["favorites_only"] = "true"
            if with_data_only:
                params["with_data_only"] = "true"

            response = await client.get("/managed-symbols", params=params)
            response.raise_for_status()
            data = response.json()

            return [ManagedSymbol(**s) for s in data]
        except Exception as e:
            logger.error(f"Failed to get managed symbols: {e}")
            return []

    async def get_symbol_stats(self) -> Optional[SymbolStats]:
        """Get statistics about managed symbols."""
        try:
            client = await self._get_client()
            response = await client.get("/managed-symbols/stats")
            response.raise_for_status()
            return SymbolStats(**response.json())
        except Exception as e:
            logger.error(f"Failed to get symbol stats: {e}")
            return None

    async def search_symbols(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search managed symbols."""
        try:
            client = await self._get_client()
            response = await client.get(
                "/managed-symbols/search",
                params={"query": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to search symbols: {e}")
            return {"query": query, "count": 0, "symbols": []}

    async def import_symbols(self) -> Optional[SymbolImportResult]:
        """Import all symbols from TimescaleDB."""
        try:
            client = await self._get_client()
            response = await client.post("/managed-symbols/import")
            response.raise_for_status()
            return SymbolImportResult(**response.json())
        except Exception as e:
            logger.error(f"Failed to import symbols: {e}")
            return None

    async def get_managed_symbol(self, symbol_id: str) -> Optional[ManagedSymbol]:
        """Get a specific managed symbol."""
        try:
            client = await self._get_client()
            response = await client.get(f"/managed-symbols/{symbol_id}")
            response.raise_for_status()
            return ManagedSymbol(**response.json())
        except Exception as e:
            logger.error(f"Failed to get symbol {symbol_id}: {e}")
            return None

    async def create_symbol(self, data: Dict[str, Any]) -> Optional[ManagedSymbol]:
        """Create a new managed symbol."""
        try:
            client = await self._get_client()
            response = await client.post("/managed-symbols", json=data)
            response.raise_for_status()
            return ManagedSymbol(**response.json())
        except Exception as e:
            logger.error(f"Failed to create symbol: {e}")
            return None

    async def update_symbol(
        self, symbol_id: str, data: Dict[str, Any]
    ) -> Optional[ManagedSymbol]:
        """Update an existing managed symbol."""
        try:
            client = await self._get_client()
            response = await client.put(f"/managed-symbols/{symbol_id}", json=data)
            response.raise_for_status()
            return ManagedSymbol(**response.json())
        except Exception as e:
            logger.error(f"Failed to update symbol {symbol_id}: {e}")
            return None

    async def delete_symbol(self, symbol_id: str) -> bool:
        """Delete a managed symbol."""
        try:
            client = await self._get_client()
            response = await client.delete(f"/managed-symbols/{symbol_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to delete symbol {symbol_id}: {e}")
            return False

    async def toggle_favorite(self, symbol_id: str) -> Optional[ManagedSymbol]:
        """Toggle favorite status for a symbol."""
        try:
            client = await self._get_client()
            response = await client.post(f"/managed-symbols/{symbol_id}/favorite")
            response.raise_for_status()
            return ManagedSymbol(**response.json())
        except Exception as e:
            logger.error(f"Failed to toggle favorite for {symbol_id}: {e}")
            return None

    async def refresh_symbol(self, symbol_id: str) -> Optional[ManagedSymbol]:
        """Refresh TimescaleDB data for a symbol."""
        try:
            client = await self._get_client()
            response = await client.post(f"/managed-symbols/{symbol_id}/refresh")
            response.raise_for_status()
            return ManagedSymbol(**response.json())
        except Exception as e:
            logger.error(f"Failed to refresh symbol {symbol_id}: {e}")
            return None


# Singleton instance
kitrading_service = KITradingService()
