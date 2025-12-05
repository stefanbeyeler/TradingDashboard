"""CoinGecko API integration for cryptocurrency data."""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from cachetools import TTLCache

from ..config import settings
from ..models import MarketTicker, AssetType, OHLCV, MarketNews

logger = logging.getLogger(__name__)

# Cache for API responses (5 minute TTL)
_price_cache = TTLCache(maxsize=100, ttl=60)
_market_cache = TTLCache(maxsize=50, ttl=300)


class CoinGeckoService:
    """Service for CoinGecko cryptocurrency data."""

    def __init__(self):
        self.base_url = settings.coingecko_api_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0),
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_price(
        self,
        coin_ids: List[str],
        vs_currency: str = "usd",
    ) -> Dict[str, float]:
        """Get simple price for coins."""
        cache_key = f"price_{','.join(coin_ids)}_{vs_currency}"
        if cache_key in _price_cache:
            return _price_cache[cache_key]

        try:
            client = await self._get_client()
            response = await client.get(
                "/simple/price",
                params={
                    "ids": ",".join(coin_ids),
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true",
                },
            )
            response.raise_for_status()
            data = response.json()
            _price_cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"CoinGecko price fetch failed: {e}")
            return {}

    async def get_markets(
        self,
        vs_currency: str = "usd",
        order: str = "market_cap_desc",
        per_page: int = 50,
        page: int = 1,
    ) -> List[MarketTicker]:
        """Get top cryptocurrencies by market cap."""
        cache_key = f"markets_{vs_currency}_{order}_{per_page}_{page}"
        if cache_key in _market_cache:
            return _market_cache[cache_key]

        try:
            client = await self._get_client()
            response = await client.get(
                "/coins/markets",
                params={
                    "vs_currency": vs_currency,
                    "order": order,
                    "per_page": per_page,
                    "page": page,
                    "sparkline": "false",
                    "price_change_percentage": "24h,7d",
                },
            )
            response.raise_for_status()
            data = response.json()

            tickers = []
            for coin in data:
                tickers.append(MarketTicker(
                    symbol=coin["symbol"].upper(),
                    name=coin["name"],
                    asset_type=AssetType.CRYPTO,
                    price=coin["current_price"] or 0,
                    change_24h=coin.get("price_change_24h"),
                    change_percent_24h=coin.get("price_change_percentage_24h"),
                    high_24h=coin.get("high_24h"),
                    low_24h=coin.get("low_24h"),
                    volume_24h=coin.get("total_volume"),
                    market_cap=coin.get("market_cap"),
                    last_updated=datetime.fromisoformat(
                        coin["last_updated"].replace("Z", "+00:00")
                    ) if coin.get("last_updated") else datetime.utcnow(),
                ))

            _market_cache[cache_key] = tickers
            return tickers
        except Exception as e:
            logger.error(f"CoinGecko markets fetch failed: {e}")
            return []

    async def get_coin_data(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed coin data."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "false",
                    "developer_data": "false",
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CoinGecko coin data fetch failed: {e}")
            return None

    async def get_ohlc(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30,
    ) -> List[OHLCV]:
        """Get OHLC candlestick data."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"/coins/{coin_id}/ohlc",
                params={
                    "vs_currency": vs_currency,
                    "days": days,
                },
            )
            response.raise_for_status()
            data = response.json()

            candles = []
            for item in data:
                candles.append(OHLCV(
                    timestamp=datetime.fromtimestamp(item[0] / 1000),
                    open=item[1],
                    high=item[2],
                    low=item[3],
                    close=item[4],
                    volume=0,  # CoinGecko OHLC doesn't include volume
                ))
            return candles
        except Exception as e:
            logger.error(f"CoinGecko OHLC fetch failed: {e}")
            return []

    async def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30,
    ) -> Dict[str, List]:
        """Get market chart data (prices, market_caps, volumes)."""
        try:
            client = await self._get_client()
            response = await client.get(
                f"/coins/{coin_id}/market_chart",
                params={
                    "vs_currency": vs_currency,
                    "days": days,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CoinGecko market chart fetch failed: {e}")
            return {"prices": [], "market_caps": [], "total_volumes": []}

    async def get_trending(self) -> List[Dict[str, Any]]:
        """Get trending coins."""
        try:
            client = await self._get_client()
            response = await client.get("/search/trending")
            response.raise_for_status()
            data = response.json()
            return data.get("coins", [])
        except Exception as e:
            logger.error(f"CoinGecko trending fetch failed: {e}")
            return []

    async def get_global_data(self) -> Dict[str, Any]:
        """Get global cryptocurrency market data."""
        try:
            client = await self._get_client()
            response = await client.get("/global")
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            logger.error(f"CoinGecko global data fetch failed: {e}")
            return {}

    async def search(self, query: str) -> Dict[str, List]:
        """Search for coins, exchanges, etc."""
        try:
            client = await self._get_client()
            response = await client.get(
                "/search",
                params={"query": query},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"CoinGecko search failed: {e}")
            return {"coins": [], "exchanges": []}


# Singleton instance
coingecko_service = CoinGeckoService()
