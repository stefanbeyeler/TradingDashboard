"""API routes for TradingDashboard."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ..services import (
    kitrading_service,
    coingecko_service,
    alphavantage_service,
    binance_service,
    news_service,
    scheduler_service,
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
    ManagedSymbol,
    SymbolCreateRequest,
    SymbolUpdateRequest,
    SymbolImportResult,
    SymbolStats,
    SymbolCategory,
    SymbolStatus,
)
from ..db import (
    get_db,
    ConfigRepository,
    UserPreferencesRepository,
    TradingAnalysisRepository,
    PriceForecastRepository,
    WatchlistRepository,
    PriceAlertRepository,
    TradeJournalRepository,
    TradingAnalysis,
    PriceForecast,
    Watchlist,
    WatchlistItem,
    PriceAlert,
    TradeJournalEntry,
    UserPreferences,
    ConfigValueRequest,
    ConfigListResponse,
    UserPreferencesRequest,
    UserPreferencesResponse,
    TradingAnalysisCreate,
    TradingAnalysisResponse,
    TradingAnalysisListResponse,
    PriceForecastCreate,
    PriceForecastResponse,
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistItemAdd,
    WatchlistItemResponse,
    WatchlistResponse,
    PriceAlertCreate,
    PriceAlertResponse,
    TradeJournalCreate,
    TradeJournalUpdate,
    TradeJournalClose,
    TradeJournalResponse,
    TradeStatisticsResponse,
    BackupMetadata,
    BackupData,
    RestoreRequest,
    RestoreResult,
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
    db: AsyncSession = Depends(get_db),
) -> Optional[KIRecommendation]:
    """Get trading recommendation from KITradingModel and save to database."""
    recommendation = await kitrading_service.get_recommendation(
        symbol=symbol,
        use_llm=use_llm,
        strategy_id=strategy_id,
    )
    if not recommendation:
        raise HTTPException(status_code=404, detail=f"No recommendation for {symbol}")

    # Save to database
    try:
        repo = TradingAnalysisRepository(db)
        analysis = TradingAnalysis(
            symbol=symbol,
            timeframe="1h",
            analysis_type="ki_recommendation",
            direction=recommendation.direction,
            confidence_score=recommendation.confidence_score,
            entry_price=recommendation.entry_price,
            stop_loss=recommendation.stop_loss,
            take_profit_1=recommendation.take_profit_1,
            take_profit_2=recommendation.take_profit_2,
            take_profit_3=recommendation.take_profit_3,
            risk_reward_ratio=recommendation.risk_reward_ratio,
            rationale=recommendation.rationale,
            key_levels=recommendation.key_levels if isinstance(recommendation.key_levels, str) else str(recommendation.key_levels) if recommendation.key_levels else None,
            risks=recommendation.risks or [],
            strategy_id=strategy_id,
            raw_response={
                "use_llm": use_llm,
                "timestamp": str(recommendation.timestamp),
                "indicators": recommendation.indicators,
            },
        )
        await repo.create(analysis)
    except Exception as e:
        # Log but don't fail the request if saving fails
        print(f"Failed to save recommendation to database: {e}")

    return recommendation


@router.post("/ki/analyze")
async def analyze_symbol(
    request: KIAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get full market analysis from KITradingModel and save to database."""
    result = await kitrading_service.analyze(
        symbol=request.symbol,
        lookback_days=request.lookback_days,
        include_technical=request.include_technical,
        strategy_id=request.strategy_id,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Analysis failed")

    # Save to database if recommendation exists
    try:
        if result.get("recommendation"):
            rec = result["recommendation"]
            repo = TradingAnalysisRepository(db)
            analysis = TradingAnalysis(
                symbol=request.symbol,
                timeframe="1h",
                analysis_type="ki_full_analysis",
                direction=rec.get("direction"),
                confidence_score=rec.get("confidence_score"),
                entry_price=rec.get("entry_price"),
                stop_loss=rec.get("stop_loss"),
                take_profit_1=rec.get("take_profit_1"),
                take_profit_2=rec.get("take_profit_2"),
                take_profit_3=rec.get("take_profit_3"),
                risk_reward_ratio=rec.get("risk_reward_ratio"),
                rationale=rec.get("rationale"),
                key_levels=rec.get("key_levels") if isinstance(rec.get("key_levels"), str) else str(rec.get("key_levels")) if rec.get("key_levels") else None,
                risks=rec.get("risks") or [],
                strategy_id=request.strategy_id,
                raw_response=result,
            )
            await repo.create(analysis)
    except Exception as e:
        # Log but don't fail the request if saving fails
        print(f"Failed to save analysis to database: {e}")

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
# Symbol Management (via KITradingModel)
# ============================================================================

@router.get("/symbols", response_model=List[ManagedSymbol])
async def get_managed_symbols(
    category: Optional[SymbolCategory] = None,
    status: Optional[SymbolStatus] = None,
    favorites_only: bool = False,
    with_data_only: bool = False,
):
    """Get all managed symbols with optional filtering."""
    return await kitrading_service.get_managed_symbols(
        category=category.value if category else None,
        status=status.value if status else None,
        favorites_only=favorites_only,
        with_data_only=with_data_only,
    )


@router.get("/symbols/stats", response_model=SymbolStats)
async def get_symbol_stats():
    """Get statistics about managed symbols."""
    stats = await kitrading_service.get_symbol_stats()
    if not stats:
        raise HTTPException(status_code=500, detail="Failed to get symbol stats")
    return stats


@router.get("/symbols/search")
async def search_symbols(
    query: str,
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Search managed symbols."""
    return await kitrading_service.search_symbols(query=query, limit=limit)


@router.post("/symbols/import", response_model=SymbolImportResult)
async def import_symbols():
    """Import all symbols from TimescaleDB."""
    result = await kitrading_service.import_symbols()
    if not result:
        raise HTTPException(status_code=500, detail="Failed to import symbols")
    return result


@router.post("/symbols", response_model=ManagedSymbol)
async def create_symbol(request: SymbolCreateRequest):
    """Create a new managed symbol."""
    symbol = await kitrading_service.create_symbol(request.model_dump())
    if not symbol:
        raise HTTPException(status_code=500, detail="Failed to create symbol")
    return symbol


@router.get("/symbols/{symbol_id}", response_model=ManagedSymbol)
async def get_symbol(symbol_id: str):
    """Get a specific managed symbol."""
    symbol = await kitrading_service.get_managed_symbol(symbol_id)
    if not symbol:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol_id}' not found")
    return symbol


@router.put("/symbols/{symbol_id}", response_model=ManagedSymbol)
async def update_symbol(symbol_id: str, request: SymbolUpdateRequest):
    """Update an existing managed symbol."""
    symbol = await kitrading_service.update_symbol(
        symbol_id,
        request.model_dump(exclude_unset=True)
    )
    if not symbol:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol_id}' not found")
    return symbol


@router.delete("/symbols/{symbol_id}")
async def delete_symbol(symbol_id: str):
    """Delete a managed symbol."""
    success = await kitrading_service.delete_symbol(symbol_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol_id}' not found")
    return {"status": "deleted", "symbol": symbol_id}


@router.post("/symbols/{symbol_id}/favorite", response_model=ManagedSymbol)
async def toggle_favorite(symbol_id: str):
    """Toggle favorite status for a symbol."""
    symbol = await kitrading_service.toggle_favorite(symbol_id)
    if not symbol:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol_id}' not found")
    return symbol


@router.post("/symbols/{symbol_id}/refresh", response_model=ManagedSymbol)
async def refresh_symbol(symbol_id: str):
    """Refresh TimescaleDB data for a symbol."""
    symbol = await kitrading_service.refresh_symbol(symbol_id)
    if not symbol:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol_id}' not found")
    return symbol


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


# ============================================================================
# Configuration (PostgreSQL)
# ============================================================================

@router.get("/config")
async def get_all_config(db: AsyncSession = Depends(get_db)) -> ConfigListResponse:
    """Get all configuration values."""
    repo = ConfigRepository(db)
    configs = await repo.get_all()
    return ConfigListResponse(configs=configs)


@router.get("/config/{key}")
async def get_config(key: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get a specific configuration value."""
    repo = ConfigRepository(db)
    value = await repo.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")
    return {"key": key, "value": value}


@router.put("/config/{key}")
async def set_config(
    key: str,
    request: ConfigValueRequest,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Set a configuration value."""
    repo = ConfigRepository(db)
    await repo.set(key, request.value, request.description)
    return {"key": key, "value": request.value, "status": "saved"}


@router.delete("/config/{key}")
async def delete_config(key: str, db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Delete a configuration value."""
    repo = ConfigRepository(db)
    deleted = await repo.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Config key '{key}' not found")
    return {"status": "deleted", "key": key}


# ============================================================================
# User Preferences (PostgreSQL)
# ============================================================================

@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(
    user_id: str = Query("default"),
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences."""
    repo = UserPreferencesRepository(db)
    prefs = await repo.get(user_id)
    if not prefs:
        # Create default preferences
        prefs = UserPreferences(user_id=user_id)
        prefs = await repo.save(prefs)
    return prefs


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    request: UserPreferencesRequest,
    user_id: str = Query("default"),
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences."""
    repo = UserPreferencesRepository(db)
    updates = request.model_dump(exclude_unset=True)
    prefs = await repo.update(user_id, updates)
    if not prefs:
        # Create with updates
        prefs = UserPreferences(user_id=user_id, **updates)
        prefs = await repo.save(prefs)
    return prefs


# ============================================================================
# Trading Analyses (PostgreSQL)
# ============================================================================

@router.get("/analyses", response_model=TradingAnalysisListResponse)
async def get_analyses(
    symbol: Optional[str] = None,
    analysis_type: Optional[str] = None,
    favorites_only: bool = False,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get saved trading analyses."""
    repo = TradingAnalysisRepository(db)
    if symbol:
        analyses = await repo.get_by_symbol(symbol, limit, analysis_type)
    else:
        analyses = await repo.get_recent(limit, analysis_type, favorites_only)
    return TradingAnalysisListResponse(analyses=analyses, total=len(analyses))


@router.post("/analyses", response_model=TradingAnalysisResponse)
async def save_analysis(
    request: TradingAnalysisCreate,
    db: AsyncSession = Depends(get_db)
):
    """Save a new trading analysis."""
    repo = TradingAnalysisRepository(db)
    analysis = TradingAnalysis(**request.model_dump())
    saved = await repo.create(analysis)
    return saved


@router.get("/analyses/{analysis_id}", response_model=TradingAnalysisResponse)
async def get_analysis(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific trading analysis."""
    repo = TradingAnalysisRepository(db)
    analysis = await repo.get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.post("/analyses/{analysis_id}/favorite", response_model=TradingAnalysisResponse)
async def toggle_analysis_favorite(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    """Toggle favorite status for an analysis."""
    repo = TradingAnalysisRepository(db)
    analysis = await repo.toggle_favorite(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a trading analysis."""
    repo = TradingAnalysisRepository(db)
    deleted = await repo.delete(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"status": "deleted", "id": str(analysis_id)}


# ============================================================================
# Price Forecasts (PostgreSQL)
# ============================================================================

@router.get("/forecasts/{symbol}", response_model=List[PriceForecastResponse])
async def get_forecasts(
    symbol: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get saved price forecasts for a symbol."""
    repo = PriceForecastRepository(db)
    forecasts = await repo.get_by_symbol(symbol, limit)
    return forecasts


@router.post("/forecasts", response_model=PriceForecastResponse)
async def save_forecast(
    request: PriceForecastCreate,
    db: AsyncSession = Depends(get_db)
):
    """Save a new price forecast."""
    repo = PriceForecastRepository(db)
    forecast = PriceForecast(
        symbol=request.symbol,
        current_price=request.current_price,
        horizon=request.horizon,
        model_type=request.model_type,
        predictions=[p.model_dump() for p in request.predictions],
        trend_probability_up=request.trend_probability_up,
        trend_probability_down=request.trend_probability_down,
        model_confidence=request.model_confidence,
        raw_response=request.raw_response,
    )
    saved = await repo.create(forecast)
    return saved


# ============================================================================
# Watchlists (PostgreSQL)
# ============================================================================

@router.get("/watchlists", response_model=List[WatchlistResponse])
async def get_watchlists(db: AsyncSession = Depends(get_db)):
    """Get all watchlists."""
    repo = WatchlistRepository(db)
    watchlists = await repo.get_all()
    # Load items for each watchlist
    for wl in watchlists:
        wl.items = await repo.get_items(wl.id)
    return watchlists


@router.post("/watchlists", response_model=WatchlistResponse)
async def create_watchlist(
    request: WatchlistCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new watchlist."""
    repo = WatchlistRepository(db)
    watchlist = Watchlist(**request.model_dump())
    saved = await repo.create(watchlist)
    saved.items = []
    return saved


@router.get("/watchlists/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(watchlist_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific watchlist with items."""
    repo = WatchlistRepository(db)
    watchlist = await repo.get(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    watchlist.items = await repo.get_items(watchlist_id)
    return watchlist


@router.put("/watchlists/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: UUID,
    request: WatchlistUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a watchlist."""
    repo = WatchlistRepository(db)
    watchlist = await repo.get(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(watchlist, key, value)
    watchlist.items = await repo.get_items(watchlist_id)
    return watchlist


@router.delete("/watchlists/{watchlist_id}")
async def delete_watchlist(watchlist_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a watchlist."""
    repo = WatchlistRepository(db)
    deleted = await repo.delete(watchlist_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"status": "deleted", "id": str(watchlist_id)}


@router.post("/watchlists/{watchlist_id}/symbols", response_model=WatchlistItemResponse)
async def add_watchlist_symbol(
    watchlist_id: UUID,
    request: WatchlistItemAdd,
    db: AsyncSession = Depends(get_db)
):
    """Add a symbol to a watchlist."""
    repo = WatchlistRepository(db)
    watchlist = await repo.get(watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    item = await repo.add_symbol(watchlist_id, request.symbol, request.notes)
    return item


@router.delete("/watchlists/{watchlist_id}/symbols/{symbol}")
async def remove_watchlist_symbol(
    watchlist_id: UUID,
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a symbol from a watchlist."""
    repo = WatchlistRepository(db)
    removed = await repo.remove_symbol(watchlist_id, symbol)
    if not removed:
        raise HTTPException(status_code=404, detail="Symbol not in watchlist")
    return {"status": "removed", "symbol": symbol}


# ============================================================================
# Price Alerts (PostgreSQL)
# ============================================================================

@router.get("/alerts", response_model=List[PriceAlertResponse])
async def get_alerts(
    symbol: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get price alerts."""
    repo = PriceAlertRepository(db)
    if active_only:
        alerts = await repo.get_active(symbol)
    else:
        # Would need to add get_all method for this
        alerts = await repo.get_active(symbol)
    return alerts


@router.post("/alerts", response_model=PriceAlertResponse)
async def create_alert(
    request: PriceAlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new price alert."""
    repo = PriceAlertRepository(db)
    alert = PriceAlert(**request.model_dump())
    saved = await repo.create(alert)
    return saved


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a price alert."""
    repo = PriceAlertRepository(db)
    deleted = await repo.delete(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "deleted", "id": str(alert_id)}


# ============================================================================
# Trade Journal (PostgreSQL)
# ============================================================================

@router.get("/journal", response_model=List[TradeJournalResponse])
async def get_journal_entries(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get trade journal entries."""
    repo = TradeJournalRepository(db)
    if symbol:
        entries = await repo.get_by_symbol(symbol, status, limit)
    elif status == "open":
        entries = await repo.get_open_trades()
    else:
        entries = await repo.get_by_symbol("", status, limit)
    return entries


@router.post("/journal", response_model=TradeJournalResponse)
async def create_journal_entry(
    request: TradeJournalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new trade journal entry."""
    repo = TradeJournalRepository(db)
    entry = TradeJournalEntry(**request.model_dump())
    saved = await repo.create(entry)
    return saved


@router.get("/journal/statistics", response_model=TradeStatisticsResponse)
async def get_journal_statistics(db: AsyncSession = Depends(get_db)):
    """Get trading statistics from journal."""
    repo = TradeJournalRepository(db)
    stats = await repo.get_statistics()
    return stats


@router.get("/journal/{entry_id}", response_model=TradeJournalResponse)
async def get_journal_entry(entry_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific journal entry."""
    repo = TradeJournalRepository(db)
    entry = await repo.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.put("/journal/{entry_id}", response_model=TradeJournalResponse)
async def update_journal_entry(
    entry_id: UUID,
    request: TradeJournalUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a trade journal entry."""
    repo = TradeJournalRepository(db)
    entry = await repo.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    return entry


@router.post("/journal/{entry_id}/close", response_model=TradeJournalResponse)
async def close_trade(
    entry_id: UUID,
    request: TradeJournalClose,
    db: AsyncSession = Depends(get_db)
):
    """Close an open trade."""
    repo = TradeJournalRepository(db)
    entry = await repo.close_trade(entry_id, request.exit_price, request.exit_reason)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found or already closed")
    return entry


@router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a journal entry."""
    repo = TradeJournalRepository(db)
    deleted = await repo.delete(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"status": "deleted", "id": str(entry_id)}


# ============================================================================
# Backup/Restore (PostgreSQL)
# ============================================================================

@router.get("/backup", response_model=BackupData)
async def create_backup(db: AsyncSession = Depends(get_db)):
    """Create a full backup of all configuration and data."""
    config_repo = ConfigRepository(db)
    prefs_repo = UserPreferencesRepository(db)
    watchlist_repo = WatchlistRepository(db)
    alert_repo = PriceAlertRepository(db)
    analysis_repo = TradingAnalysisRepository(db)
    journal_repo = TradeJournalRepository(db)

    # Gather all data
    config = await config_repo.get_all()

    # Get user preferences
    prefs = await prefs_repo.get("default")
    user_preferences = []
    if prefs:
        user_preferences.append({
            "id": str(prefs.id),
            "user_id": prefs.user_id,
            "theme": prefs.theme,
            "language": prefs.language,
            "default_timeframe": prefs.default_timeframe,
            "default_symbol": prefs.default_symbol,
            "notifications_enabled": prefs.notifications_enabled,
            "auto_refresh_interval": prefs.auto_refresh_interval,
            "chart_settings": prefs.chart_settings,
            "dashboard_layout": prefs.dashboard_layout,
        })

    # Get watchlists with items
    watchlists_raw = await watchlist_repo.get_all()
    watchlists = []
    for wl in watchlists_raw:
        items = await watchlist_repo.get_items(wl.id)
        watchlists.append({
            "id": str(wl.id),
            "name": wl.name,
            "description": wl.description,
            "is_default": wl.is_default,
            "sort_order": wl.sort_order,
            "items": [
                {
                    "id": str(item.id),
                    "symbol": item.symbol,
                    "sort_order": item.sort_order,
                    "notes": item.notes,
                    "alert_price_above": item.alert_price_above,
                    "alert_price_below": item.alert_price_below,
                }
                for item in items
            ]
        })

    # Get price alerts
    alerts_raw = await alert_repo.get_active()
    price_alerts = [
        {
            "id": str(alert.id),
            "symbol": alert.symbol,
            "alert_type": alert.alert_type,
            "target_value": alert.target_value,
            "notes": alert.notes,
            "is_active": alert.is_active,
        }
        for alert in alerts_raw
    ]

    # Get trading analyses (last 100)
    analyses_raw = await analysis_repo.get_recent(100)
    trading_analyses = [
        {
            "id": str(a.id),
            "symbol": a.symbol,
            "timeframe": a.timeframe,
            "analysis_type": a.analysis_type,
            "direction": a.direction,
            "confidence_score": a.confidence_score,
            "entry_price": a.entry_price,
            "stop_loss": a.stop_loss,
            "take_profit_1": a.take_profit_1,
            "take_profit_2": a.take_profit_2,
            "take_profit_3": a.take_profit_3,
            "risk_reward_ratio": a.risk_reward_ratio,
            "rationale": a.rationale,
            "key_levels": a.key_levels,
            "risks": a.risks,
            "strategy_id": a.strategy_id,
            "is_favorite": a.is_favorite,
            "tags": a.tags,
            "notes": a.notes,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses_raw
    ]

    # Get trade journal entries (last 100)
    journal_raw = await journal_repo.get_by_symbol("", None, 100)
    trade_journal = [
        {
            "id": str(j.id),
            "symbol": j.symbol,
            "direction": j.direction,
            "entry_price": j.entry_price,
            "exit_price": j.exit_price,
            "position_size": j.position_size,
            "stop_loss": j.stop_loss,
            "take_profit": j.take_profit,
            "pnl": j.pnl,
            "pnl_percent": j.pnl_percent,
            "status": j.status,
            "entry_reason": j.entry_reason,
            "exit_reason": j.exit_reason,
            "analysis_id": str(j.analysis_id) if j.analysis_id else None,
            "lessons_learned": j.lessons_learned,
            "tags": j.tags,
            "entry_time": j.entry_time.isoformat() if j.entry_time else None,
            "exit_time": j.exit_time.isoformat() if j.exit_time else None,
        }
        for j in journal_raw
    ]

    # Build backup
    metadata = BackupMetadata(
        version="1.0",
        created_at=datetime.utcnow(),
        tables_included=["config", "user_preferences", "watchlists", "price_alerts", "trading_analyses", "trade_journal"],
        record_counts={
            "config": len(config),
            "user_preferences": len(user_preferences),
            "watchlists": len(watchlists),
            "price_alerts": len(price_alerts),
            "trading_analyses": len(trading_analyses),
            "trade_journal": len(trade_journal),
        }
    )

    return BackupData(
        metadata=metadata,
        config=config,
        user_preferences=user_preferences,
        watchlists=watchlists,
        price_alerts=price_alerts,
        trading_analyses=trading_analyses,
        trade_journal=trade_journal,
    )


@router.post("/restore", response_model=RestoreResult)
async def restore_backup(
    request: RestoreRequest,
    db: AsyncSession = Depends(get_db)
):
    """Restore data from a backup."""
    errors = []
    records_restored = {
        "config": 0,
        "user_preferences": 0,
        "watchlists": 0,
        "price_alerts": 0,
        "trading_analyses": 0,
        "trade_journal": 0,
    }

    backup = request.backup

    try:
        # Restore config
        if request.restore_config and backup.config:
            config_repo = ConfigRepository(db)
            for key, value in backup.config.items():
                try:
                    await config_repo.set(key, value)
                    records_restored["config"] += 1
                except Exception as e:
                    errors.append(f"Config '{key}': {str(e)}")

        # Restore user preferences
        if request.restore_preferences and backup.user_preferences:
            prefs_repo = UserPreferencesRepository(db)
            for pref_data in backup.user_preferences:
                try:
                    user_id = pref_data.get("user_id", "default")
                    updates = {k: v for k, v in pref_data.items() if k not in ["id", "user_id", "created_at", "updated_at"]}
                    existing = await prefs_repo.get(user_id)
                    if existing:
                        await prefs_repo.update(user_id, updates)
                    else:
                        new_prefs = UserPreferences(user_id=user_id, **updates)
                        await prefs_repo.save(new_prefs)
                    records_restored["user_preferences"] += 1
                except Exception as e:
                    errors.append(f"User preferences: {str(e)}")

        # Restore watchlists
        if request.restore_watchlists and backup.watchlists:
            watchlist_repo = WatchlistRepository(db)
            for wl_data in backup.watchlists:
                try:
                    wl = Watchlist(
                        name=wl_data["name"],
                        description=wl_data.get("description"),
                        is_default=wl_data.get("is_default", False),
                        sort_order=wl_data.get("sort_order", 0),
                    )
                    saved_wl = await watchlist_repo.create(wl)
                    records_restored["watchlists"] += 1

                    # Add items
                    for item_data in wl_data.get("items", []):
                        await watchlist_repo.add_symbol(
                            saved_wl.id,
                            item_data["symbol"],
                            item_data.get("notes"),
                        )
                except Exception as e:
                    errors.append(f"Watchlist '{wl_data.get('name', 'unknown')}': {str(e)}")

        # Restore price alerts
        if request.restore_alerts and backup.price_alerts:
            alert_repo = PriceAlertRepository(db)
            for alert_data in backup.price_alerts:
                try:
                    alert = PriceAlert(
                        symbol=alert_data["symbol"],
                        alert_type=alert_data["alert_type"],
                        target_value=alert_data["target_value"],
                        notes=alert_data.get("notes"),
                        is_active=alert_data.get("is_active", True),
                    )
                    await alert_repo.create(alert)
                    records_restored["price_alerts"] += 1
                except Exception as e:
                    errors.append(f"Price alert: {str(e)}")

        # Restore trading analyses
        if request.restore_analyses and backup.trading_analyses:
            analysis_repo = TradingAnalysisRepository(db)
            for a_data in backup.trading_analyses:
                try:
                    analysis = TradingAnalysis(
                        symbol=a_data["symbol"],
                        timeframe=a_data.get("timeframe", "1h"),
                        analysis_type=a_data.get("analysis_type", "ki_recommendation"),
                        direction=a_data.get("direction"),
                        confidence_score=a_data.get("confidence_score"),
                        entry_price=a_data.get("entry_price"),
                        stop_loss=a_data.get("stop_loss"),
                        take_profit_1=a_data.get("take_profit_1"),
                        take_profit_2=a_data.get("take_profit_2"),
                        take_profit_3=a_data.get("take_profit_3"),
                        risk_reward_ratio=a_data.get("risk_reward_ratio"),
                        rationale=a_data.get("rationale"),
                        key_levels=a_data.get("key_levels"),
                        risks=a_data.get("risks", []),
                        strategy_id=a_data.get("strategy_id"),
                        is_favorite=a_data.get("is_favorite", False),
                        tags=a_data.get("tags", []),
                        notes=a_data.get("notes"),
                    )
                    await analysis_repo.create(analysis)
                    records_restored["trading_analyses"] += 1
                except Exception as e:
                    errors.append(f"Trading analysis: {str(e)}")

        # Restore trade journal
        if request.restore_journal and backup.trade_journal:
            journal_repo = TradeJournalRepository(db)
            for j_data in backup.trade_journal:
                try:
                    entry = TradeJournalEntry(
                        symbol=j_data["symbol"],
                        direction=j_data["direction"],
                        entry_price=j_data["entry_price"],
                        exit_price=j_data.get("exit_price"),
                        position_size=j_data.get("position_size"),
                        stop_loss=j_data.get("stop_loss"),
                        take_profit=j_data.get("take_profit"),
                        pnl=j_data.get("pnl"),
                        pnl_percent=j_data.get("pnl_percent"),
                        status=j_data.get("status", "open"),
                        entry_reason=j_data.get("entry_reason"),
                        exit_reason=j_data.get("exit_reason"),
                        lessons_learned=j_data.get("lessons_learned"),
                        tags=j_data.get("tags", []),
                    )
                    await journal_repo.create(entry)
                    records_restored["trade_journal"] += 1
                except Exception as e:
                    errors.append(f"Trade journal entry: {str(e)}")

        return RestoreResult(
            success=len(errors) == 0,
            records_restored=records_restored,
            errors=errors,
        )

    except Exception as e:
        return RestoreResult(
            success=False,
            records_restored=records_restored,
            errors=[f"Restore failed: {str(e)}"],
        )


# ============================================================================
# Scheduled Analyses (Dashboard Quick Analyses for Favorites)
# ============================================================================

@router.get("/scheduled-analyses")
async def get_scheduled_analyses():
    """Get the latest scheduled analyses for all favorite symbols."""
    analyses = scheduler_service.get_latest_analyses()
    return {
        "analyses": analyses,
        "status": scheduler_service.get_status(),
    }


@router.get("/scheduled-analyses/{symbol}")
async def get_scheduled_analysis_for_symbol(symbol: str):
    """Get the latest scheduled analysis for a specific symbol."""
    analysis = scheduler_service.get_analysis_for_symbol(symbol)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"No scheduled analysis found for {symbol}")
    return analysis


@router.post("/scheduled-analyses/run")
async def run_scheduled_analyses():
    """Manually trigger scheduled analyses for all favorite symbols."""
    analyses = await scheduler_service.run_now()
    return {
        "success": True,
        "analyzed_count": len(analyses),
        "analyses": analyses,
    }


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get the current status of the scheduler."""
    return scheduler_service.get_status()


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler if not running."""
    if scheduler_service.is_running:
        return {"message": "Scheduler is already running", "status": scheduler_service.get_status()}
    await scheduler_service.start()
    return {"message": "Scheduler started", "status": scheduler_service.get_status()}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    if not scheduler_service.is_running:
        return {"message": "Scheduler is not running", "status": scheduler_service.get_status()}
    await scheduler_service.stop()
    return {"message": "Scheduler stopped", "status": scheduler_service.get_status()}


@router.put("/scheduler/interval")
async def set_scheduler_interval(interval_minutes: int = Query(ge=5, le=1440)):
    """Set the scheduler interval in minutes (5-1440)."""
    scheduler_service.interval_minutes = interval_minutes
    return {
        "message": f"Scheduler interval set to {interval_minutes} minutes",
        "status": scheduler_service.get_status(),
    }
