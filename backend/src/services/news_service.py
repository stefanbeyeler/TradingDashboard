"""News aggregation service for market-related news."""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from cachetools import TTLCache

from ..config import settings
from ..models import MarketNews

logger = logging.getLogger(__name__)

# Cache for news (15 minute TTL)
_news_cache = TTLCache(maxsize=50, ttl=900)


class NewsService:
    """Service for aggregating market news from various sources."""

    def __init__(self):
        self.newsapi_key = settings.news_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_crypto_news(self, limit: int = 20) -> List[MarketNews]:
        """Get cryptocurrency news from CryptoCompare (free)."""
        cache_key = f"crypto_news_{limit}"
        if cache_key in _news_cache:
            return _news_cache[cache_key]

        try:
            client = await self._get_client()
            response = await client.get(
                "https://min-api.cryptocompare.com/data/v2/news/",
                params={"lang": "EN", "sortOrder": "latest"},
            )
            response.raise_for_status()
            data = response.json()

            news_items = []
            for item in data.get("Data", [])[:limit]:
                news_items.append(MarketNews(
                    title=item["title"],
                    description=item.get("body", "")[:500],
                    url=item["url"],
                    source=item.get("source", "CryptoCompare"),
                    published_at=datetime.fromtimestamp(item["published_on"]),
                    sentiment=self._analyze_sentiment(item.get("title", "")),
                    related_symbols=item.get("categories", "").split("|")[:5],
                ))

            _news_cache[cache_key] = news_items
            return news_items
        except Exception as e:
            logger.error(f"CryptoCompare news fetch failed: {e}")
            return []

    async def get_market_news(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[MarketNews]:
        """Get general market news using NewsAPI (requires API key)."""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return []

        cache_key = f"market_news_{query}_{limit}"
        if cache_key in _news_cache:
            return _news_cache[cache_key]

        try:
            client = await self._get_client()
            response = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "sortBy": "publishedAt",
                    "pageSize": limit,
                    "language": "en",
                    "apiKey": self.newsapi_key,
                },
            )
            response.raise_for_status()
            data = response.json()

            news_items = []
            for article in data.get("articles", []):
                published_at = datetime.utcnow()
                if article.get("publishedAt"):
                    try:
                        published_at = datetime.fromisoformat(
                            article["publishedAt"].replace("Z", "+00:00")
                        )
                    except:
                        pass

                news_items.append(MarketNews(
                    title=article["title"] or "",
                    description=article.get("description", ""),
                    url=article["url"],
                    source=article.get("source", {}).get("name", "Unknown"),
                    published_at=published_at,
                    sentiment=self._analyze_sentiment(article.get("title", "")),
                ))

            _news_cache[cache_key] = news_items
            return news_items
        except Exception as e:
            logger.error(f"NewsAPI fetch failed: {e}")
            return []

    async def get_forex_news(self, limit: int = 20) -> List[MarketNews]:
        """Get forex-related news."""
        # Using free forex news from ForexFactory RSS alternative
        cache_key = f"forex_news_{limit}"
        if cache_key in _news_cache:
            return _news_cache[cache_key]

        try:
            client = await self._get_client()
            # Using DailyFX RSS as free alternative
            response = await client.get(
                "https://www.dailyfx.com/feeds/market-news",
                headers={"Accept": "application/rss+xml"},
            )

            # If RSS fails, return empty (would need XML parsing)
            if response.status_code != 200:
                return []

            # For now, return empty as proper RSS parsing would be needed
            return []
        except Exception as e:
            logger.error(f"Forex news fetch failed: {e}")
            return []

    async def get_combined_news(self, limit: int = 30) -> List[MarketNews]:
        """Get combined news from all sources."""
        all_news = []

        # Get crypto news (always available, free)
        crypto_news = await self.get_crypto_news(limit=limit // 2)
        all_news.extend(crypto_news)

        # Get market news if API key available
        if self.newsapi_key:
            market_news = await self.get_market_news(
                query="trading OR forex OR cryptocurrency",
                limit=limit // 2,
            )
            all_news.extend(market_news)

        # Sort by publish date
        all_news.sort(key=lambda x: x.published_at, reverse=True)
        return all_news[:limit]

    def _analyze_sentiment(self, text: str) -> str:
        """Simple rule-based sentiment analysis."""
        text_lower = text.lower()

        positive_words = [
            "surge", "rally", "gain", "rise", "bullish", "soar", "jump",
            "profit", "growth", "up", "high", "record", "boom", "breakthrough",
        ]
        negative_words = [
            "crash", "fall", "drop", "bearish", "plunge", "loss", "decline",
            "down", "low", "dump", "sell-off", "fear", "warning", "risk",
        ]

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"


# Singleton instance
news_service = NewsService()
