-- Trading Dashboard Database Initialization
-- PostgreSQL 16

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Configuration Tables
-- =====================================================

-- App Configuration (key-value store for settings)
CREATE TABLE IF NOT EXISTS app_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) DEFAULT 'default',
    theme VARCHAR(50) DEFAULT 'dark',
    language VARCHAR(10) DEFAULT 'de',
    default_timeframe VARCHAR(10) DEFAULT '1h',
    default_symbol VARCHAR(50) DEFAULT 'EURUSD',
    notifications_enabled BOOLEAN DEFAULT true,
    auto_refresh_interval INTEGER DEFAULT 30,
    chart_settings JSONB DEFAULT '{}',
    dashboard_layout JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- =====================================================
-- Trading Analysis Tables
-- =====================================================

-- Saved Trading Analyses
CREATE TABLE IF NOT EXISTS trading_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,  -- 'ki_recommendation', 'technical', 'forecast'
    direction VARCHAR(20),  -- 'LONG', 'SHORT', 'NEUTRAL'
    confidence_score INTEGER,
    entry_price DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    take_profit_1 DECIMAL(20, 8),
    take_profit_2 DECIMAL(20, 8),
    take_profit_3 DECIMAL(20, 8),
    risk_reward_ratio DECIMAL(10, 2),
    rationale TEXT,
    key_levels TEXT,
    risks JSONB DEFAULT '[]',
    raw_response JSONB,
    strategy_id VARCHAR(100),
    is_favorite BOOLEAN DEFAULT false,
    tags JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price Forecasts History
CREATE TABLE IF NOT EXISTS price_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    current_price DECIMAL(20, 8) NOT NULL,
    horizon INTEGER NOT NULL,  -- forecast horizon in periods
    model_type VARCHAR(50) DEFAULT 'nhits',
    predictions JSONB NOT NULL,  -- array of {timestamp, predicted_price, confidence_low, confidence_high}
    trend_probability_up DECIMAL(5, 4),
    trend_probability_down DECIMAL(5, 4),
    model_confidence DECIMAL(5, 4),
    raw_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Watchlist and Favorites
-- =====================================================

-- Watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Watchlist Items
CREATE TABLE IF NOT EXISTS watchlist_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watchlist_id UUID NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    notes TEXT,
    alert_price_above DECIMAL(20, 8),
    alert_price_below DECIMAL(20, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(watchlist_id, symbol)
);

-- =====================================================
-- Alert System
-- =====================================================

-- Price Alerts
CREATE TABLE IF NOT EXISTS price_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- 'price_above', 'price_below', 'percent_change'
    target_value DECIMAL(20, 8) NOT NULL,
    current_value DECIMAL(20, 8),
    is_triggered BOOLEAN DEFAULT false,
    triggered_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    notification_sent BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Trading Journal
-- =====================================================

-- Trade Journal Entries
CREATE TABLE IF NOT EXISTS trade_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,  -- 'LONG', 'SHORT'
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    position_size DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    pnl DECIMAL(20, 8),
    pnl_percent DECIMAL(10, 4),
    status VARCHAR(20) DEFAULT 'open',  -- 'open', 'closed', 'cancelled'
    entry_reason TEXT,
    exit_reason TEXT,
    analysis_id UUID REFERENCES trading_analyses(id),
    screenshots JSONB DEFAULT '[]',
    lessons_learned TEXT,
    tags JSONB DEFAULT '[]',
    entry_time TIMESTAMP WITH TIME ZONE,
    exit_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Indexes
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_trading_analyses_symbol ON trading_analyses(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_analyses_created_at ON trading_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trading_analyses_type ON trading_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_trading_analyses_favorite ON trading_analyses(is_favorite) WHERE is_favorite = true;

CREATE INDEX IF NOT EXISTS idx_price_forecasts_symbol ON price_forecasts(symbol);
CREATE INDEX IF NOT EXISTS idx_price_forecasts_created_at ON price_forecasts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_price_alerts_symbol ON price_alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_price_alerts_active ON price_alerts(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
CREATE INDEX IF NOT EXISTS idx_trade_journal_status ON trade_journal(status);
CREATE INDEX IF NOT EXISTS idx_trade_journal_created_at ON trade_journal(created_at DESC);

-- =====================================================
-- Default Data
-- =====================================================

-- Insert default watchlist
INSERT INTO watchlists (name, description, is_default, sort_order)
VALUES ('Hauptwatchlist', 'Standard-Watchlist für wichtige Symbole', true, 0)
ON CONFLICT DO NOTHING;

-- Insert default user preferences
INSERT INTO user_preferences (user_id, theme, language, default_symbol, default_timeframe)
VALUES ('default', 'dark', 'de', 'EURUSD', '1h')
ON CONFLICT (user_id) DO NOTHING;

-- Insert default app config
INSERT INTO app_config (key, value, description)
VALUES
    ('api_rate_limits', '{"coingecko": 10, "binance": 100, "kitrading": 50}', 'API rate limits per minute'),
    ('cache_ttl', '{"market_data": 60, "analysis": 300, "forecast": 600}', 'Cache TTL in seconds'),
    ('default_symbols', '["EURUSD", "BTCUSD", "XAUUSD", "SPX500"]', 'Default symbols for dashboard')
ON CONFLICT (key) DO NOTHING;

-- =====================================================
-- Update Trigger Function
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
DROP TRIGGER IF EXISTS update_app_config_updated_at ON app_config;
CREATE TRIGGER update_app_config_updated_at
    BEFORE UPDATE ON app_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_watchlists_updated_at ON watchlists;
CREATE TRIGGER update_watchlists_updated_at
    BEFORE UPDATE ON watchlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_trade_journal_updated_at ON trade_journal;
CREATE TRIGGER update_trade_journal_updated_at
    BEFORE UPDATE ON trade_journal
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
