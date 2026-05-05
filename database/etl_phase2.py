"""ETL pipeline for Phase 2 forecast and risk data into database.

Reads analysis outputs (training metrics, risk analysis, schedule fragility, backtests)
and populates the forecasting and risk tables in the database via SQLite.

Usage:
    python -m database.etl_phase2
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Data paths
METRICS_PATH = Path("metrics/training_metrics.json")
RISK_REPORT_PATH = Path("metrics/risk_analysis.json")
FRAGILITY_REPORT_PATH = Path("metrics/schedule_fragility.json")
BACKTEST_PATH = Path("metrics/backtest_results.json")
SCHEMA_PATH = Path("database/phase2_schema.sql")
DB_PATH = Path("database/tazara.db")  # Consolidate into main database


class Phase2ETL:
    """ETL for Phase 2 forecasting and risk data."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
    
    def connect(self) -> None:
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Closed database connection")
    
    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute SQL query."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
    
    def fetch(self, query: str, params: tuple = ()) -> list:
        """Fetch query results."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def init_schema(self) -> None:
        """Initialize database schema from SQL file."""
        if not SCHEMA_PATH.exists():
            logger.warning(f"Schema file not found: {SCHEMA_PATH}")
            return
        
        with open(SCHEMA_PATH) as f:
            schema_sql = f.read()
        
        # Execute schema script
        cursor = self.conn.cursor()
        cursor.executescript(schema_sql)
        self.conn.commit()
        logger.info("Database schema initialized")
    
    def load_forecasting_models(self) -> None:
        """Load trained models into forecasting_models table."""
        if not METRICS_PATH.exists():
            logger.warning(f"Metrics file not found: {METRICS_PATH}")
            return
        
        with open(METRICS_PATH) as f:
            metrics = json.load(f)
        
        # Register LSTM model
        if "lstm" in metrics and "error" not in metrics["lstm"]:
            lstm_metrics = metrics["lstm"]
            self.execute(
                """INSERT OR REPLACE INTO forecasting_models 
                   (model_name, model_type, model_path, version, rmse, mae, mape, r2)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "lstm",
                    "LSTM",
                    lstm_metrics.get("model_path", "models/lstm_model.keras"),
                    1,
                    lstm_metrics.get("rmse"),
                    lstm_metrics.get("mae"),
                    lstm_metrics.get("mape", None),
                    lstm_metrics.get("r2")
                )
            )
            logger.info("Loaded LSTM model")
        
        # Register ARIMA model
        if "arima" in metrics and "error" not in metrics["arima"]:
            arima_metrics = metrics["arima"]
            self.execute(
                """INSERT OR REPLACE INTO forecasting_models 
                   (model_name, model_type, model_path, version, rmse, mae, mape, r2)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "arima",
                    "ARIMA",
                    arima_metrics.get("model_path", "models/arima_model.pkl"),
                    1,
                    arima_metrics.get("rmse"),
                    arima_metrics.get("mae"),
                    arima_metrics.get("mape", None),
                    arima_metrics.get("r2")
                )
            )
            logger.info("Loaded ARIMA model")
    
    def load_daily_risk_analysis(self) -> None:
        """Load daily risk analysis results."""
        if not RISK_REPORT_PATH.exists():
            logger.warning(f"Risk report not found: {RISK_REPORT_PATH}")
            return
        
        with open(RISK_REPORT_PATH) as f:
            risk_data = json.load(f)
        
        daily_risks = risk_data.get("daily_risk_scores", [])
        for risk in daily_risks:
            self.execute(
                """INSERT OR REPLACE INTO risk_analysis 
                   (analysis_date, demand_tons, volatility, trend, is_anomaly, 
                    risk_score, risk_level, duration_uncertainty_lower_pct, duration_uncertainty_upper_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    risk["date"],
                    risk["demand_tons"],
                    risk["volatility"],
                    risk["trend"],
                    1 if risk["is_anomaly"] else 0,
                    risk["risk_score"],
                    risk["risk_level"],
                    risk["duration_uncertainty_pct"]["lower"],
                    risk["duration_uncertainty_pct"]["upper"]
                )
            )
        logger.info(f"Loaded {len(daily_risks)} daily risk records")
        
        # Load bottleneck periods
        bottlenecks = risk_data.get("bottleneck_periods", [])
        for bn in bottlenecks:
            self.execute(
                """INSERT INTO bottleneck_periods 
                   (start_date, end_date, duration_days, avg_demand, max_demand, avg_volatility)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    bn["start_date"],
                    bn["end_date"],
                    bn["duration_days"],
                    bn["avg_demand"],
                    bn["max_demand"],
                    bn["avg_volatility"]
                )
            )
        logger.info(f"Loaded {len(bottlenecks)} bottleneck periods")
    
    def load_schedule_fragility(self) -> None:
        """Load schedule fragility analysis results."""
        if not FRAGILITY_REPORT_PATH.exists():
            logger.warning(f"Fragility report not found: {FRAGILITY_REPORT_PATH}")
            return
        
        with open(FRAGILITY_REPORT_PATH) as f:
            fragility_data = json.load(f)
        
        daily_fragility = fragility_data.get("daily_fragility_scores", [])
        for frag in daily_fragility:
            self.execute(
                """INSERT OR REPLACE INTO schedule_fragility 
                   (analysis_date, demand_tons, capacity_utilization_pct, slack_time_pct, 
                    fragility_score, fragility_level)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    frag["date"],
                    frag["demand_tons"],
                    frag["capacity_utilization_pct"],
                    frag["slack_time_pct"],
                    frag["fragility_score"],
                    frag["fragility_level"]
                )
            )
        logger.info(f"Loaded {len(daily_fragility)} daily fragility records")
        
        # Load what-if scenarios
        scenarios = fragility_data.get("what_if_scenarios", {})
        for scenario_name, scenario_data in scenarios.items():
            parts = scenario_name.split("_")
            scenario_type = parts[0]
            magnitude = float(parts[1].rstrip("pct")) / 100.0
            
            self.execute(
                """INSERT OR REPLACE INTO what_if_scenarios 
                   (scenario_name, scenario_type, magnitude, avg_fragility_score, 
                    max_fragility_score, avg_demand, capacity_util_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    scenario_name,
                    scenario_type,
                    magnitude,
                    scenario_data["avg_fragility_score"],
                    scenario_data["max_fragility_score"],
                    scenario_data["avg_demand"],
                    scenario_data["capacity_util_pct"]
                )
            )
        logger.info(f"Loaded {len(scenarios)} what-if scenarios")
    
    def load_backtest_results(self) -> None:
        """Load backtesting results."""
        if not BACKTEST_PATH.exists():
            logger.warning(f"Backtest results not found: {BACKTEST_PATH}")
            return
        
        with open(BACKTEST_PATH) as f:
            backtest_data = json.load(f)
        
        window_results = backtest_data.get("window_results", [])
        for wr in window_results:
            self.execute(
                """INSERT INTO backtest_results 
                   (window_number, train_start, train_end, test_start, test_end, 
                    rmse, mae, mape, r2)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    wr["window"],
                    wr["train_start"],
                    wr["train_end"],
                    wr["test_start"],
                    wr["test_end"],
                    wr["rmse"],
                    wr["mae"],
                    wr["mape"],
                    wr["r2"]
                )
            )
        logger.info(f"Loaded {len(window_results)} backtest windows")
    
    def run(self) -> None:
        """Run full ETL pipeline."""
        logger.info("Starting Phase 2 ETL pipeline...")
        
        self.connect()
        try:
            self.init_schema()
            self.load_forecasting_models()
            self.load_daily_risk_analysis()
            self.load_schedule_fragility()
            self.load_backtest_results()
            logger.info("ETL pipeline completed successfully")
            
            # Print summary
            print("\n" + "="*70)
            print("✅ PHASE 2 DATA INGESTION COMPLETE")
            print("="*70)
            
            # Count records in key tables
            cursor = self.conn.cursor()
            for table in ["forecasting_models", "risk_analysis", "schedule_fragility", "bottleneck_periods", "what_if_scenarios"]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} records")
            
            print("  Database: database/tazara_ai.db")
            print("\n✅ ETL pipeline complete!\n")
        
        finally:
            self.close()


if __name__ == "__main__":
    etl = Phase2ETL()
    etl.run()
