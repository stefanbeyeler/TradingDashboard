"""KITradingModel API integration service."""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..config import settings
from ..models import KIRecommendation, KIForecast, ForecastPoint

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


# Singleton instance
kitrading_service = KITradingService()
