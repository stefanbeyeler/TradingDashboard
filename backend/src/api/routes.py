"""API routes for TradingDashboard."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services import (
    kitrading_service,
    coingecko_service,
    alphavantage_service,
    binance_service,
    news_service,
)
from ..models import (
    MarketTicker,
    OHLCV,
    OrderBook,
    MarketNews,
    KIRecommendation,
    KIForecast,
    KIAnalysisRequest,
    DashboardData,
)

router = APIRouter()


# ============================================================================
# Health & System
# ============================================================================

@router.get("/health")
async def health_check():
    """Check health of all services."""
    ki_health = await kitrading_service.health_check()
    binance_time = await binance_service.get_server_time()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "kitrading": ki_health.get("status", "unknown"),
            "binance": "healthy" if binance_time else "unavailable",
            "coingecko": "healthy",  # Free API, usually available
            "alphavantage": "healthy" if alphavantage_service.api_key else "not_configured",
        },
    }


@router.get("/dashboard")
async def get_dashboard_data(
    watchlist: str = Query("BTC,ETH,SOL,XRP", description="Comma-separated crypto symbols"),
) -> DashboardData:
    """Get aggregated dashboard data."""
    # Parse watchlist
    symbols = [s.strip().upper() for s in watchlist.split(",")]

    # Get market data for watchlist from CoinGecko
    markets = await coingecko_service.get_markets(per_page=100)
    watchlist_tickers = [
        ticker for ticker in markets
        if ticker.symbol in symbols
    ]

    # Get latest news
    news = await news_service.get_crypto_news(limit=10)

    # Get KI system status
    ki_health = await kitrading_service.health_check()

    return DashboardData(
        watchlist=watchlist_tickers,
        market_news=news,
        system_status=ki_health,
    )


# ============================================================================
# KITradingModel Integration
# ============================================================================

@router.get("/ki/symbols")
async def get_ki_symbols() -> Dict[str, List[str]]:
    """Get available symbols from KITradingModel."""
    symbols = await kitrading_service.get_symbols()
    return {"symbols": symbols}


@router.get("/ki/recommendation/{symbol}")
async def get_ki_recommendation(
    symbol: str,
    use_llm: bool = Query(False, description="Use LLM for enhanced analysis"),
    strategy_id: Optional[str] = Query(None, description="Strategy ID to use"),
) -> Optional[KIRecommendation]:
    """Get trading recommendation from KITradingModel."""
    recommendation = await kitrading_service.get_recommendation(
        symbol=symbol,
        use_llm=use_llm,
        strategy_id=strategy_id,
    )
    if not recommendation:
        raise HTTPException(status_code=404, detail=f"No recommendation for {symbol}")
    return recommendation


@router.post("/ki/analyze")
async def analyze_symbol(request: KIAnalysisRequest) -> Dict[str, Any]:
    """Get full market analysis from KITradingModel."""
    result = await kitrading_service.analyze(
        symbol=request.symbol,
        lookback_days=request.lookback_days,
        include_technical=request.include_technical,
        strategy_id=request.strategy_id,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Analysis failed")
    return result


@router.get("/ki/forecast/{symbol}")
async def get_ki_forecast(
    symbol: str,
    horizon: int = Query(24, ge=1, le=168, description="Forecast horizon in hours"),
) -> Optional[KIForecast]:
    """Get NHITS price forecast from KITradingModel."""
    forecast = await kitrading_service.get_forecast(symbol=symbol, horizon=horizon)
    if not forecast:
        raise HTTPException(status_code=404, detail=f"No forecast for {symbol}")
    return forecast


@router.get("/ki/strategies")
async def get_ki_strategies() -> List[Dict[str, Any]]:
    """Get available trading strategies."""
    return await kitrading_service.get_strategies()


@router.get("/ki/forecast-models")
async def get_forecast_models() -> List[Dict[str, Any]]:
    """Get available NHITS forecast models."""
    return await kitrading_service.get_forecast_models()


@router.get("/ki/rag/query")
async def query_rag(
    query: str,
    symbol: Optional[str] = None,
    n_results: int = Query(5, ge=1, le=20),
) -> List[Dict[str, Any]]:
    """Query RAG system for relevant documents."""
    return await kitrading_service.query_rag(
        query=query,
        symbol=symbol,
        n_results=n_results,
    )


@router.get("/ki/query-logs")
async def get_query_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """Get query logs history."""
    return await kitrading_service.get_query_logs(
        limit=limit,
        offset=offset,
        symbol=symbol,
    )


# ============================================================================
# Cryptocurrency Data (CoinGecko + Binance)
# ============================================================================

@router.get("/crypto/markets")
async def get_crypto_markets(
    per_page: int = Query(50, ge=1, le=250),
    page: int = Query(1, ge=1),
) -> List[MarketTicker]:
    """Get top cryptocurrencies by market cap."""
    return await coingecko_service.get_markets(per_page=per_page, page=page)


@router.get("/crypto/trending")
async def get_trending_crypto() -> List[Dict[str, Any]]:
    """Get trending cryptocurrencies."""
    return await coingecko_service.get_trending()


@router.get("/crypto/global")
async def get_global_crypto_data() -> Dict[str, Any]:
    """Get global cryptocurrency market data."""
    return await coingecko_service.get_global_data()


@router.get("/crypto/{coin_id}/ohlc")
async def get_crypto_ohlc(
    coin_id: str,
    days: int = Query(30, ge=1, le=365),
) -> List[OHLCV]:
    """Get OHLC data for a cryptocurrency."""
    return await coingecko_service.get_ohlc(coin_id=coin_id, days=days)


@router.get("/crypto/{coin_id}/chart")
async def get_crypto_chart(
    coin_id: str,
    days: int = Query(30, ge=1, le=365),
) -> Dict[str, List]:
    """Get market chart data for a cryptocurrency."""
    return await coingecko_service.get_market_chart(coin_id=coin_id, days=days)


@router.get("/crypto/search")
async def search_crypto(query: str) -> Dict[str, List]:
    """Search for cryptocurrencies."""
    return await coingecko_service.search(query)


# Binance-specific endpoints
@router.get("/binance/ticker")
async def get_binance_tickers(
    symbol: Optional[str] = None,
) -> List[MarketTicker]:
    """Get 24hr ticker from Binance."""
    return await binance_service.get_ticker_24h(symbol)


@router.get("/binance/klines/{symbol}")
async def get_binance_klines(
    symbol: str,
    interval: str = Query("1h", description="Kline interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(100, ge=1, le=1000),
) -> List[OHLCV]:
    """Get kline/candlestick data from Binance."""
    return await binance_service.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )


@router.get("/binance/orderbook/{symbol}")
async def get_binance_orderbook(
    symbol: str,
    limit: int = Query(20, ge=5, le=100),
) -> Optional[OrderBook]:
    """Get order book from Binance."""
    orderbook = await binance_service.get_order_book(symbol, limit)
    if not orderbook:
        raise HTTPException(status_code=404, detail=f"Order book not found for {symbol}")
    return orderbook


@router.get("/binance/trades/{symbol}")
async def get_binance_trades(
    symbol: str,
    limit: int = Query(50, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Get recent trades from Binance."""
    return await binance_service.get_recent_trades(symbol, limit)


# ============================================================================
# Stock & Forex Data (Alpha Vantage)
# ============================================================================

@router.get("/stocks/quote/{symbol}")
async def get_stock_quote(symbol: str) -> Optional[MarketTicker]:
    """Get real-time stock quote."""
    ticker = await alphavantage_service.get_stock_quote(symbol)
    if not ticker:
        raise HTTPException(status_code=404, detail=f"Quote not found for {symbol}")
    return ticker


@router.get("/stocks/daily/{symbol}")
async def get_stock_daily(
    symbol: str,
    outputsize: str = Query("compact", description="compact (100) or full"),
) -> List[OHLCV]:
    """Get daily stock OHLCV data."""
    return await alphavantage_service.get_stock_daily(symbol, outputsize)


@router.get("/stocks/search")
async def search_stocks(keywords: str) -> List[Dict[str, str]]:
    """Search for stocks."""
    return await alphavantage_service.search_symbols(keywords)


@router.get("/forex/rate")
async def get_forex_rate(
    from_currency: str,
    to_currency: str = "USD",
) -> Optional[MarketTicker]:
    """Get forex exchange rate."""
    ticker = await alphavantage_service.get_forex_rate(from_currency, to_currency)
    if not ticker:
        raise HTTPException(status_code=404, detail=f"Rate not found for {from_currency}/{to_currency}")
    return ticker


@router.get("/forex/daily")
async def get_forex_daily(
    from_symbol: str,
    to_symbol: str = "USD",
    outputsize: str = Query("compact", description="compact (100) or full"),
) -> List[OHLCV]:
    """Get daily forex OHLCV data."""
    return await alphavantage_service.get_forex_daily(from_symbol, to_symbol, outputsize)


@router.get("/indicators/rsi/{symbol}")
async def get_rsi(
    symbol: str,
    interval: str = Query("daily"),
    time_period: int = Query(14, ge=2, le=100),
) -> Dict[str, Any]:
    """Get RSI indicator for a symbol."""
    indicator = await alphavantage_service.get_rsi(symbol, interval, time_period)
    if not indicator:
        raise HTTPException(status_code=404, detail=f"RSI not found for {symbol}")
    return indicator.model_dump()


@router.get("/indicators/macd/{symbol}")
async def get_macd(
    symbol: str,
    interval: str = Query("daily"),
) -> Dict[str, Any]:
    """Get MACD indicator for a symbol."""
    indicator = await alphavantage_service.get_macd(symbol, interval)
    if not indicator:
        raise HTTPException(status_code=404, detail=f"MACD not found for {symbol}")
    return indicator.model_dump()


# ============================================================================
# News
# ============================================================================

@router.get("/news/crypto")
async def get_crypto_news(
    limit: int = Query(20, ge=1, le=50),
) -> List[MarketNews]:
    """Get cryptocurrency news."""
    return await news_service.get_crypto_news(limit)


@router.get("/news/market")
async def get_market_news(
    query: str = Query("stock market trading"),
    limit: int = Query(20, ge=1, le=50),
) -> List[MarketNews]:
    """Get market news."""
    return await news_service.get_market_news(query, limit)


@router.get("/news/combined")
async def get_combined_news(
    limit: int = Query(30, ge=1, le=100),
) -> List[MarketNews]:
    """Get combined news from all sources."""
    return await news_service.get_combined_news(limit)
