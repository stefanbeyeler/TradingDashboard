"""Binance API integration for cryptocurrency trading data."""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from cachetools import TTLCache
import hmac
import hashlib
import time

from ..config import settings
from ..models import MarketTicker, AssetType, OHLCV, OrderBook, OrderBookEntry

logger = logging.getLogger(__name__)

# Cache for API responses
_ticker_cache = TTLCache(maxsize=500, ttl=10)
_orderbook_cache = TTLCache(maxsize=100, ttl=5)


class BinanceService:
    """Service for Binance cryptocurrency data."""

    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.api_key = settings.binance_api_key
        self.api_secret = settings.binance_api_secret
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["X-MBX-APIKEY"] = self.api_key

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0),
                headers=headers,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _sign_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sign request with API secret (for authenticated endpoints)."""
        if not self.api_secret:
            return params

        params["timestamp"] = int(time.time() * 1000)
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    async def get_ticker_24h(self, symbol: Optional[str] = None) -> List[MarketTicker]:
        """Get 24hr ticker price change statistics."""
        cache_key = f"ticker24h_{symbol or 'all'}"
        if cache_key in _ticker_cache:
            return _ticker_cache[cache_key]

        try:
            client = await self._get_client()
            params = {}
            if symbol:
                params["symbol"] = symbol

            response = await client.get("/ticker/24hr", params=params)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict):
                data = [data]

            tickers = []
            for item in data:
                # Only include USDT pairs for simplicity
                if not symbol and not item["symbol"].endswith("USDT"):
                    continue

                tickers.append(MarketTicker(
                    symbol=item["symbol"],
                    asset_type=AssetType.CRYPTO,
                    price=float(item["lastPrice"]),
                    change_24h=float(item["priceChange"]),
                    change_percent_24h=float(item["priceChangePercent"]),
                    high_24h=float(item["highPrice"]),
                    low_24h=float(item["lowPrice"]),
                    volume_24h=float(item["volume"]),
                ))

            _ticker_cache[cache_key] = tickers
            return tickers
        except Exception as e:
            logger.error(f"Binance ticker fetch failed: {e}")
            return []

    async def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        try:
            client = await self._get_client()
            response = await client.get("/ticker/price", params={"symbol": symbol})
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
        except Exception as e:
            logger.error(f"Binance price fetch failed: {e}")
            return None

    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[OHLCV]:
        """Get kline/candlestick data."""
        try:
            client = await self._get_client()
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            }
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time

            response = await client.get("/klines", params=params)
            response.raise_for_status()
            data = response.json()

            candles = []
            for item in data:
                candles.append(OHLCV(
                    timestamp=datetime.fromtimestamp(item[0] / 1000),
                    open=float(item[1]),
                    high=float(item[2]),
                    low=float(item[3]),
                    close=float(item[4]),
                    volume=float(item[5]),
                ))
            return candles
        except Exception as e:
            logger.error(f"Binance klines fetch failed: {e}")
            return []

    async def get_order_book(
        self,
        symbol: str,
        limit: int = 20,
    ) -> Optional[OrderBook]:
        """Get order book depth."""
        cache_key = f"orderbook_{symbol}_{limit}"
        if cache_key in _orderbook_cache:
            return _orderbook_cache[cache_key]

        try:
            client = await self._get_client()
            response = await client.get(
                "/depth",
                params={"symbol": symbol, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            order_book = OrderBook(
                symbol=symbol,
                bids=[
                    OrderBookEntry(price=float(bid[0]), quantity=float(bid[1]))
                    for bid in data["bids"]
                ],
                asks=[
                    OrderBookEntry(price=float(ask[0]), quantity=float(ask[1]))
                    for ask in data["asks"]
                ],
            )

            _orderbook_cache[cache_key] = order_book
            return order_book
        except Exception as e:
            logger.error(f"Binance order book fetch failed: {e}")
            return None

    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent trades."""
        try:
            client = await self._get_client()
            response = await client.get(
                "/trades",
                params={"symbol": symbol, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "price": float(trade["price"]),
                    "quantity": float(trade["qty"]),
                    "time": datetime.fromtimestamp(trade["time"] / 1000),
                    "is_buyer_maker": trade["isBuyerMaker"],
                }
                for trade in data
            ]
        except Exception as e:
            logger.error(f"Binance trades fetch failed: {e}")
            return []

    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information."""
        try:
            client = await self._get_client()
            response = await client.get("/exchangeInfo")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Binance exchange info fetch failed: {e}")
            return {}

    async def get_avg_price(self, symbol: str) -> Optional[float]:
        """Get current average price for a symbol."""
        try:
            client = await self._get_client()
            response = await client.get("/avgPrice", params={"symbol": symbol})
            response.raise_for_status()
            data = response.json()
            return float(data["price"])
        except Exception as e:
            logger.error(f"Binance avg price fetch failed: {e}")
            return None

    async def get_server_time(self) -> Optional[datetime]:
        """Get Binance server time."""
        try:
            client = await self._get_client()
            response = await client.get("/time")
            response.raise_for_status()
            data = response.json()
            return datetime.fromtimestamp(data["serverTime"] / 1000)
        except Exception as e:
            logger.error(f"Binance server time fetch failed: {e}")
            return None


# Singleton instance
binance_service = BinanceService()
