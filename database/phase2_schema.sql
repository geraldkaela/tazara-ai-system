-- Phase 2 Database Schema for Forecasts and Risk Analysis
-- Tables: forecasting_models, forecasts, risk_analysis, schedule_fragility, bottleneck_periods

-- Forecasting models registry
CREATE TABLE IF NOT EXISTS forecasting_models (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL UNIQUE,
    model_type TEXT NOT NULL,
    model_path TEXT,
    version INTEGER,
    rmse REAL,
    mae REAL,
    mape REAL,
    r2 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Demand forecasts
CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_horizon_days INTEGER,
    forecast_tons REAL NOT NULL,
    lower_bound REAL,
    upper_bound REAL,
    confidence_level REAL DEFAULT 0.90,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES forecasting_models(model_id),
    UNIQUE(model_id, forecast_date, forecast_horizon_days)
);

-- Risk analysis daily summary
CREATE TABLE IF NOT EXISTS risk_analysis (
    risk_id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date DATE NOT NULL,
    demand_tons REAL,
    volatility REAL,
    trend REAL,
    is_anomaly BOOLEAN DEFAULT 0,
    risk_score REAL,
    risk_level TEXT,  -- 'low', 'medium', 'high', 'critical'
    duration_uncertainty_lower_pct REAL,
    duration_uncertainty_upper_pct REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_date)
);

-- Schedule fragility daily summary
CREATE TABLE IF NOT EXISTS schedule_fragility (
    fragility_id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date DATE NOT NULL,
    demand_tons REAL,
    capacity_utilization_pct REAL,
    slack_time_pct REAL,
    fragility_score REAL,
    fragility_level TEXT,  -- 'robust', 'flexible', 'fragile', 'critical'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_date)
);

-- Bottleneck periods
CREATE TABLE IF NOT EXISTS bottleneck_periods (
    bottleneck_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INTEGER,
    avg_demand REAL,
    max_demand REAL,
    avg_volatility REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation/backtest results
CREATE TABLE IF NOT EXISTS backtest_results (
    backtest_id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_number INTEGER,
    train_start INTEGER,
    train_end INTEGER,
    test_start INTEGER,
    test_end INTEGER,
    rmse REAL,
    mae REAL,
    mape REAL,
    r2 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- What-if scenario results
CREATE TABLE IF NOT EXISTS what_if_scenarios (
    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_name TEXT NOT NULL,
    scenario_type TEXT,  -- 'surge', 'drop', 'volatility'
    magnitude REAL,
    avg_fragility_score REAL,
    max_fragility_score REAL,
    avg_demand REAL,
    capacity_util_pct REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scenario_name)
);

-- Indices for fast queries
CREATE INDEX IF NOT EXISTS idx_forecasts_model_date ON forecasts(model_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_horizon ON forecasts(forecast_horizon_days);
CREATE INDEX IF NOT EXISTS idx_risk_analysis_date ON risk_analysis(analysis_date);
CREATE INDEX IF NOT EXISTS idx_risk_analysis_level ON risk_analysis(risk_level);
CREATE INDEX IF NOT EXISTS idx_schedule_fragility_date ON schedule_fragility(analysis_date);
CREATE INDEX IF NOT EXISTS idx_schedule_fragility_level ON schedule_fragility(fragility_level);
CREATE INDEX IF NOT EXISTS idx_bottleneck_period ON bottleneck_periods(start_date, end_date);
