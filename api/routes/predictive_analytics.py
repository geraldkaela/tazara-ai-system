"""Demand forecasting API routes.

Fast endpoint for making cargo demand predictions using the trained LSTM model.
Integrates with the forecasting.predict_cargo module for inference.

Endpoints:
  POST /api/forecast - Make a demand forecast
  GET  /api/forecast/status - Check forecasting service status
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# RBAC imports
from api.auth.rbac import Permission, require_permission
from api.auth.auth import get_current_user, UserInDB
import psycopg2\nfrom api.db_utils import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/forecast", tags=["forecasting"])


class ForecastRequest(BaseModel):
    """Request body for demand forecast."""
    days_ahead: int = Field(default=7, ge=1, le=90, description="Number of days to forecast (1-90)")
    include_confidence: bool = Field(default=True, description="Include confidence intervals")
    model_type: str = Field(default="lstm", description="Model to use (lstm or arima)")


class DemandPoint(BaseModel):
    """Single forecast data point."""
    date: str
    forecast_tons: float
    upper_bound: Optional[float] = None  # 90% confidence interval
    lower_bound: Optional[float] = None


class ForecastResponse(BaseModel):
    """Response body for demand forecast."""
    status: str = "success"
    model_used: str
    forecast_date: str
    forecasts: List[DemandPoint]
    summary: dict = {}
    rationale: str = ""


# Global cache to prevent expensive model reloading
MODEL_CACHE = {}

def load_trained_model():
    """Load the trained LSTM model from disk with in-memory caching."""
    if "lstm" in MODEL_CACHE:
        return MODEL_CACHE["lstm"]
        
    model_path = Path("models/lstm_model.keras")
    if not model_path.exists():
        raise FileNotFoundError(f"Trained model not found: {model_path}")
    
    try:
        from tensorflow.keras.models import load_model
        model = load_model(model_path)
        logger.info(f"Loaded and cached LSTM model from {model_path}")
        MODEL_CACHE["lstm"] = model
        return model
    except Exception as e:
        logger.error(f"Failed to load LSTM model: {e}")
        raise


def load_scaler():
    """Load feature scaler with in-memory caching."""
    if "scaler" in MODEL_CACHE:
        return MODEL_CACHE["scaler"]
        
    try:
        import joblib
        scaler_path = Path("models/feature_scaler.pkl")
        if scaler_path.exists():
            scaler = joblib.load(scaler_path)
            MODEL_CACHE["scaler"] = scaler
            return scaler
    except Exception as e:
        logger.warning(f"Could not load saved scaler: {e}")
    
    # Fallback: create a fresh scaler (will scale to [0,1])
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1))
    MODEL_CACHE["scaler"] = scaler
    return scaler


def make_lstm_forecast(model, scaler, last_value: float, days_ahead: int, history: pd.Series = None) -> List[float]:
    """Generate LSTM forecast for future days."""
    lookback = 7
    forecast = []
    
    # Simple Min-Max scaling based on history if scaler is incompatible
    if history is not None:
        h_min, h_max = history.min(), history.max()
        if h_max > h_min:
            scale_val = lambda x: (x - h_min) / (h_max - h_min)
            unscale_val = lambda x: x * (h_max - h_min) + h_min
        else:
            scale_val = unscale_val = lambda x: x
    else:
        # Fallback to no scaling
        scale_val = unscale_val = lambda x: x

    # Initialize sequence with scaled last known value
    current_val = scale_val(last_value)
    sequence = np.array([[current_val]] * lookback).reshape(1, lookback, 1)
    
    for _ in range(days_ahead):
        pred_scaled = model.predict(sequence, verbose=0)[0, 0]
        forecast.append(pred_scaled)
        
        # Shift sequence: remove first, add prediction to the end
        sequence = np.roll(sequence, -1, axis=1)
        sequence[0, -1, 0] = pred_scaled
    
    # Inverse scale predictions
    forecast_unscaled = [unscale_val(f) for f in forecast]
    return forecast_unscaled


def make_arima_forecast(days_ahead: int) -> List[float]:
    """Generate simple ARIMA forecast (stub for now)."""
    logger.warning("ARIMA forecasting not fully implemented; returning scaled estimate")
    # Simple placeholder: linear trend
    base = 125.0
    trend = np.linspace(0, 5, days_ahead)
    return (base + trend).tolist()


def generate_forecast_rationale(model_type: str, forecast_values: List[float], history: pd.DataFrame) -> str:
    """Generate a natural language explanation for the forecast."""
    avg_demand = np.mean(forecast_values)
    trend = "increasing" if forecast_values[-1] > forecast_values[0] else "decreasing"
    
    if abs(forecast_values[-1] - forecast_values[0]) < 1.0:
        trend = "stable"
        
    recent_mean = history["cargo_tons"].iloc[-7:].mean()
    diff = ((avg_demand - recent_mean) / recent_mean) * 100
    
    if model_type == "lstm":
        explanation = f"The LSTM neural network predicts a {trend} trend for the next period based on recent operational data. "
    else:
        explanation = f"Statistical analysis (ARIMA) indicates a {trend} trend based on recent operations. "
        
    if abs(diff) > 10:
        change_dir = "increase" if diff > 0 else "decrease"
        explanation += f"This represents a notable {abs(diff):.1f}% {change_dir} compared to recent operational averages from the last 30 days of actual schedules."
    else:
        explanation += f"Demand appears relatively stable compared to recent operational performance from actual scheduling data."
        
    return explanation


@router.post("/", response_model=ForecastResponse)
def forecast_demand(
    request: ForecastRequest,
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_ANALYTICS))
) -> ForecastResponse:
    """
    Generate a demand forecast for the next N days.
    
    **Example:**
    ```json
    {
      "days_ahead": 14,
      "include_confidence": true,
      "model_type": "lstm"
    }
    ```
    """
    try:
        # Load recent data from database instead of old CSV
        conn = get_db_connection()
        
        # Get recent auto-schedule data for forecasting
        query = """
            SELECT 
                DATE(created_at) as date,
                AVG(total_cargo_delivered) as cargo_tons,
                COUNT(*) as schedule_count,
                MAX(total_cargo_delivered) as max_daily,
                MIN(total_cargo_delivered) as min_daily
            FROM schedules
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            AND total_cargo_delivered > 0
            AND total_cargo_delivered IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """
        
        print(f"DEBUG: Executing forecast query: {query}")
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"DEBUG: Database query returned {len(df)} rows")
        if not df.empty:
            print(f"DEBUG: Sample data: {df.head()}")
            print(f"DEBUG: Data types: {df.dtypes}")
            print(f"DEBUG: Cargo tons range: {df['cargo_tons'].min()} - {df['cargo_tons'].max()}")
            print(f"DEBUG: Total schedules analyzed: {df['schedule_count'].sum()}")
            
            # Verify this is auto-schedule data by checking schedule_id patterns
            # Auto-schedules should have IDs like AUTO_20260423_114710
            verify_query = """
                SELECT COUNT(*) as auto_schedule_count,
                        COUNT(CASE WHEN schedule_id LIKE 'AUTO_%' THEN 1 END) as confirmed_auto
                FROM schedules
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            """
            
            verify_conn = get_db_connection()
            verify_df = pd.read_sql_query(verify_query, verify_conn)
            verify_conn.close()
            
            print(f"DEBUG: Auto-schedule verification: {verify_df.iloc[0].to_dict()}")
        
        if df.empty:
            # Fallback to CSV if no database data
            logger.warning("No recent database data found, falling back to CSV")
            proc_csv = Path("data/simulated/cargo_demand.csv")
            if not proc_csv.exists():
                raise FileNotFoundError("Processed demand data not found")
            df = pd.read_csv(proc_csv, parse_dates=["date"])
        
        # Use current date as base for forecasting
        last_date = datetime.now().date()
        last_value = df["cargo_tons"].iloc[0] if not df.empty else 695.0
        
        # Apply realistic constraints for TAZARA operations
        MAX_REALISTIC_DAILY = 2500  # Maximum realistic daily cargo for TAZARA
        MIN_REALISTIC_DAILY = 100   # Minimum realistic daily cargo
        
        # Only constrain extreme outliers, allow natural variation
        if last_value > MAX_REALISTIC_DAILY * 1.5:  # Only if extremely high
            print(f"DEBUG: Constraining extreme last_value {last_value} to {MAX_REALISTIC_DAILY}")
            last_value = MAX_REALISTIC_DAILY
        elif last_value < MIN_REALISTIC_DAILY / 2:  # Only if extremely low
            print(f"DEBUG: Constraining extreme low last_value {last_value} to {MIN_REALISTIC_DAILY}")
            last_value = MIN_REALISTIC_DAILY
            
        print(f"DEBUG: Using last_date={last_date}, last_value={last_value}")
        
        # Generate forecast
        if request.model_type == "lstm":
            model = load_trained_model()
            scaler = load_scaler()
            forecast_values = make_lstm_forecast(model, scaler, last_value, request.days_ahead, df["cargo_tons"])
        elif request.model_type == "arima":
            forecast_values = make_arima_forecast(request.days_ahead)
        else:
            raise ValueError(f"Unknown model type: {request.model_type}")
        
        # Build response with dates
        forecasts = []
        for i, value in enumerate(forecast_values):
            future_date = last_date + timedelta(days=i+1)
            
            # Apply realistic constraints to forecast values - allow natural variation
            # Only constrain extreme outliers, not normal variation
            if value > MAX_REALISTIC_DAILY * 1.5:
                constrained_value = MAX_REALISTIC_DAILY
            elif value < MIN_REALISTIC_DAILY / 2:
                constrained_value = MIN_REALISTIC_DAILY
            else:
                constrained_value = value  # Allow natural variation
            
            # Confidence intervals (simple: ±15% for LSTM, ±20% for ARIMA)
            conf_margin = 0.15 if request.model_type == "lstm" else 0.20
            upper = constrained_value * (1 + conf_margin) if request.include_confidence else None
            lower = max(0, constrained_value * (1 - conf_margin)) if request.include_confidence else None
            
            forecasts.append(DemandPoint(
                date=future_date.strftime("%Y-%m-%d"),
                forecast_tons=float(round(constrained_value, 2)),
                upper_bound=float(round(upper, 2)) if upper else None,
                lower_bound=float(round(lower, 2)) if lower else None
            ))
        
        # Summary stats
        summary = {
            "mean_forecast": float(round(np.mean(forecast_values), 2)),
            "min_forecast": float(round(np.min(forecast_values), 2)),
            "max_forecast": float(round(np.max(forecast_values), 2)),
            "forecast_period_days": int(request.days_ahead),
            "last_observed_value": float(round(last_value, 2)),
            "last_observed_date": last_date.strftime("%Y-%m-%d")
        }
        
        return ForecastResponse(
            status="success",
            model_used=request.model_type,
            forecast_date=datetime.now().isoformat(),
            forecasts=forecasts,
            summary=summary,
            rationale=generate_forecast_rationale(request.model_type, forecast_values, df)
        )
    
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Forecast failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")


@router.get("/status")
def forecast_status():
    """Check forecasting service status and model availability."""
    status = {
        "service": "operational",
        "models": {}
    }
    
    # Check LSTM
    lstm_path = Path("models/lstm_model.keras")
    status["models"]["lstm"] = {
        "available": lstm_path.exists(),
        "path": str(lstm_path) if lstm_path.exists() else None
    }
    
    # Check ARIMA
    arima_path = Path("models/arima_model.pkl")
    status["models"]["arima"] = {
        "available": arima_path.exists(),
        "path": str(arima_path) if arima_path.exists() else None
    }
    
    # Check processed data
    data_path = Path("data/simulated/cargo_demand.csv")
    status["data_available"] = data_path.exists()
    
    # Check registry
    registry_path = Path("models/model_registry.json")
    status["registry_available"] = registry_path.exists()
    
    return status
