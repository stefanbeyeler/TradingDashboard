"""Alpha Vantage API integration for stock and forex data."""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from cachetools import TTLCache

from ..config import settings
from ..models import MarketTicker, AssetType, OHLCV, TechnicalIndicator

logger = logging.getLogger(__name__)

# Cache for API responses
_quote_cache = TTLCache(maxsize=100, ttl=60)
_forex_cache = TTLCache(maxsize=50, ttl=60)


class AlphaVantageService:
    """Service for Alpha Vantage stock and forex data."""

    def __init__(self):
        self.base_url = "https://www.alphavantage.co/query"
        self.api_key = settings.alpha_vantage_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Make API request with API key."""
        params["apikey"] = self.api_key
        try:
            client = await self._get_client()
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check for API limit error
            if "Note" in data or "Information" in data:
                logger.warning(f"Alpha Vantage API limit: {data}")
                return {}

            return data
        except Exception as e:
            logger.error(f"Alpha Vantage request failed: {e}")
            return {}

    async def get_stock_quote(self, symbol: str) -> Optional[MarketTicker]:
        """Get real-time stock quote."""
        cache_key = f"quote_{symbol}"
        if cache_key in _quote_cache:
            return _quote_cache[cache_key]

        data = await self._make_request({
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
        })

        if not data or "Global Quote" not in data:
            return None

        quote = data["Global Quote"]
        if not quote:
            return None

        ticker = MarketTicker(
            symbol=quote.get("01. symbol", symbol),
            asset_type=AssetType.STOCK,
            price=float(quote.get("05. price", 0)),
            change_24h=float(quote.get("09. change", 0)),
            change_percent_24h=float(quote.get("10. change percent", "0%").replace("%", "")),
            high_24h=float(quote.get("03. high", 0)),
            low_24h=float(quote.get("04. low", 0)),
            volume_24h=float(quote.get("06. volume", 0)),
        )

        _quote_cache[cache_key] = ticker
        return ticker

    async def get_forex_rate(
        self,
        from_currency: str,
        to_currency: str = "USD",
    ) -> Optional[MarketTicker]:
        """Get forex exchange rate."""
        cache_key = f"forex_{from_currency}_{to_currency}"
        if cache_key in _forex_cache:
            return _forex_cache[cache_key]

        data = await self._make_request({
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
        })

        if not data or "Realtime Currency Exchange Rate" not in data:
            return None

        rate = data["Realtime Currency Exchange Rate"]
        ticker = MarketTicker(
            symbol=f"{from_currency}/{to_currency}",
            name=f"{rate.get('2. From_Currency Name', '')} to {rate.get('4. To_Currency Name', '')}",
            asset_type=AssetType.FOREX,
            price=float(rate.get("5. Exchange Rate", 0)),
            last_updated=datetime.strptime(
                rate.get("6. Last Refreshed", ""),
                "%Y-%m-%d %H:%M:%S"
            ) if rate.get("6. Last Refreshed") else datetime.utcnow(),
        )

        _forex_cache[cache_key] = ticker
        return ticker

    async def get_stock_daily(
        self,
        symbol: str,
        outputsize: str = "compact",
    ) -> List[OHLCV]:
        """Get daily stock OHLCV data."""
        data = await self._make_request({
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
        })

        if not data or "Time Series (Daily)" not in data:
            return []

        candles = []
        time_series = data["Time Series (Daily)"]

        for date_str, values in time_series.items():
            candles.append(OHLCV(
                timestamp=datetime.strptime(date_str, "%Y-%m-%d"),
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=float(values["5. volume"]),
            ))

        return sorted(candles, key=lambda x: x.timestamp)

    async def get_forex_daily(
        self,
        from_symbol: str,
        to_symbol: str = "USD",
        outputsize: str = "compact",
    ) -> List[OHLCV]:
        """Get daily forex OHLCV data."""
        data = await self._make_request({
            "function": "FX_DAILY",
            "from_symbol": from_symbol,
            "to_symbol": to_symbol,
            "outputsize": outputsize,
        })

        if not data or "Time Series FX (Daily)" not in data:
            return []

        candles = []
        time_series = data["Time Series FX (Daily)"]

        for date_str, values in time_series.items():
            candles.append(OHLCV(
                timestamp=datetime.strptime(date_str, "%Y-%m-%d"),
                open=float(values["1. open"]),
                high=float(values["2. high"]),
                low=float(values["3. low"]),
                close=float(values["4. close"]),
                volume=0,
            ))

        return sorted(candles, key=lambda x: x.timestamp)

    async def get_rsi(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 14,
    ) -> Optional[TechnicalIndicator]:
        """Get RSI indicator."""
        data = await self._make_request({
            "function": "RSI",
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": "close",
        })

        if not data or "Technical Analysis: RSI" not in data:
            return None

        rsi_data = data["Technical Analysis: RSI"]
        latest_date = max(rsi_data.keys())
        rsi_value = float(rsi_data[latest_date]["RSI"])

        signal = "neutral"
        if rsi_value > 70:
            signal = "sell"
        elif rsi_value < 30:
            signal = "buy"

        return TechnicalIndicator(
            name="RSI",
            value=rsi_value,
            signal=signal,
            description=f"RSI({time_period}) = {rsi_value:.2f}",
        )

    async def get_macd(
        self,
        symbol: str,
        interval: str = "daily",
    ) -> Optional[TechnicalIndicator]:
        """Get MACD indicator."""
        data = await self._make_request({
            "function": "MACD",
            "symbol": symbol,
            "interval": interval,
            "series_type": "close",
        })

        if not data or "Technical Analysis: MACD" not in data:
            return None

        macd_data = data["Technical Analysis: MACD"]
        latest_date = max(macd_data.keys())
        values = macd_data[latest_date]

        macd_value = float(values["MACD"])
        signal_value = float(values["MACD_Signal"])

        signal = "buy" if macd_value > signal_value else "sell"

        return TechnicalIndicator(
            name="MACD",
            value=macd_value,
            signal=signal,
            description=f"MACD: {macd_value:.4f}, Signal: {signal_value:.4f}",
        )

    async def search_symbols(self, keywords: str) -> List[Dict[str, str]]:
        """Search for symbols."""
        data = await self._make_request({
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
        })

        if not data or "bestMatches" not in data:
            return []

        return [
            {
                "symbol": match["1. symbol"],
                "name": match["2. name"],
                "type": match["3. type"],
                "region": match["4. region"],
                "currency": match["8. currency"],
            }
            for match in data["bestMatches"]
        ]


# Singleton instance
alphavantage_service = AlphaVantageService()
