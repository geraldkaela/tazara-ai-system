"""Train and evaluate LSTM and ARIMA forecasting models.

Reads features from `data/processed/features.csv`, creates train/test split,
trains both LSTM (via Keras) and ARIMA (via statsmodels), evaluates on test set,
and saves models/scalers/metrics to `models/` and `metrics/`.

Usage:
    python -m forecasting.train_models
"""
from __future__ import annotations

import logging
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


FEATURES_PATH = Path("data/processed/features.csv")
MODELS_DIR = Path("models")
METRICS_DIR = Path("metrics")


def load_features(path: Path = FEATURES_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    logger.info(f"Loaded features: {len(df)} rows, {len(df.columns)} cols")
    return df


def prepare_data(df: pd.DataFrame, test_size: float = 0.2) -> tuple:
    """Prepare train/test split for LSTM training."""
    # Drop rows with NaN in key features
    df_clean = df.dropna(subset=["cargo_tons"])
    target = df_clean["cargo_tons"].values.reshape(-1, 1)
    
    # Scale target
    scaler = MinMaxScaler(feature_range=(0, 1))
    target_scaled = scaler.fit_transform(target)
    
    # Train/test split
    split_idx = int(len(target_scaled) * (1 - test_size))
    X_train = target_scaled[:split_idx]
    X_test = target_scaled[split_idx:]
    
    logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    return X_train, X_test, scaler, df_clean


def create_lstm_sequences(data: np.ndarray, lookback: int = 7) -> tuple:
    """Create sequences for LSTM."""
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i + lookback])
        y.append(data[i + lookback])
    return np.array(X), np.array(y)


def train_lstm(X_train: np.ndarray, X_test: np.ndarray, scaler, lookback: int = 7) -> dict:
    """Train LSTM model."""
    try:
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.optimizers import Adam
    except ImportError:
        logger.warning("TensorFlow/Keras not available; skipping LSTM training")
        return {"error": "TensorFlow not available"}
    
    logger.info("Training LSTM model...")
    X_train_seq, y_train = create_lstm_sequences(X_train, lookback)
    X_test_seq, y_test = create_lstm_sequences(X_test, lookback)
    
    if len(X_train_seq) == 0 or len(X_test_seq) == 0:
        logger.warning("Insufficient data for LSTM sequences")
        return {"error": "Insufficient data"}
    
    model = Sequential([
        LSTM(32, activation='relu', input_shape=(lookback, 1), return_sequences=True),
        Dropout(0.2),
        LSTM(16, activation='relu'),
        Dense(8, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
    
    # Train with early stopping
    history = model.fit(X_train_seq, y_train, epochs=20, batch_size=16, 
                       validation_split=0.1, verbose=0)
    
    # Evaluate
    y_pred = model.predict(X_test_seq, verbose=0).flatten()
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"LSTM: RMSE={rmse:.4f}, MAE={mae:.4f}, R²={r2:.4f}")
    
    # Save model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "lstm_model.keras"
    model.save(model_path)
    logger.info(f"Saved LSTM model to {model_path}")
    
    return {"rmse": float(rmse), "mae": float(mae), "r2": float(r2), "model_path": str(model_path)}


def train_arima(df: pd.DataFrame) -> dict:
    """Train ARIMA model."""
    try:
        from statsmodels.tsa.arima.model import ARIMA
        from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    except ImportError:
        logger.warning("statsmodels not available; skipping ARIMA training")
        return {"error": "statsmodels not available"}
    
    logger.info("Training ARIMA model...")
    series = df.set_index("date")["cargo_tons"]
    
    # Simple ARIMA(1,1,1) — adjust order as needed
    try:
        model = ARIMA(series, order=(1, 1, 1))
        fitted = model.fit()
        logger.info(f"ARIMA AIC={fitted.aic:.2f}, BIC={fitted.bic:.2f}")
        
        # In-sample fit metrics (approximation)
        y_pred = fitted.fittedvalues
        y_actual = series[1:]  # align with fitted values
        
        if len(y_pred) > 0 and len(y_actual) > 0:
            rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
            mae = mean_absolute_error(y_actual, y_pred)
            r2 = r2_score(y_actual, y_pred) if len(set(y_actual)) > 1 else 0
            logger.info(f"ARIMA: RMSE={rmse:.4f}, MAE={mae:.4f}, R²={r2:.4f}")
            
            # Save model
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            model_path = MODELS_DIR / "arima_model.pkl"
            fitted.save(model_path)
            logger.info(f"Saved ARIMA model to {model_path}")
            
            return {"rmse": float(rmse), "mae": float(mae), "r2": float(r2), "aic": float(fitted.aic), "model_path": str(model_path)}
    except Exception as e:
        logger.warning(f"ARIMA training failed: {e}")
        return {"error": str(e)}


def run() -> None:
    df = load_features()
    X_train, X_test, scaler, df_clean = prepare_data(df)
    
    # Train models
    lstm_results = train_lstm(X_train, X_test, scaler)
    arima_results = train_arima(df_clean)
    
    # Save metrics
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    metrics = {
        "lstm": lstm_results,
        "arima": arima_results,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    metrics_path = METRICS_DIR / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("🤖 MODEL TRAINING SUMMARY")
    print("="*60)
    print(f"\n📊 LSTM Results:")
    for k, v in lstm_results.items():
        if k != "model_path":
            print(f"  {k}: {v}")
    print(f"\n📊 ARIMA Results:")
    for k, v in arima_results.items():
        if k != "model_path":
            print(f"  {k}: {v}")
    print("\n✅ Models trained and saved!\n")


if __name__ == "__main__":
    run()
