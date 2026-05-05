"""
Phase 2 Week 4: ML Demand Forecasting Models
LSTM, ARIMA, and ensemble approaches with confidence intervals
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import HistGradientBoostingRegressor
import logging
import warnings

# TensorFlow/Keras imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow not available - LSTM models will be disabled")

# Statsmodels imports for ARIMA
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logging.warning("Statsmodels not available - ARIMA models will be disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class DemandForecastingEngine:
    """ML-powered demand forecasting with multiple models"""
    
    def __init__(self, data_path: str = "data/simulated/cargo_demand.csv"):
        """Initialize forecasting engine"""
        self.data_path = data_path
        self.df = None
        self.scaler = MinMaxScaler()
        self.models = {}
        self.forecasts = {}
        self.accuracy_metrics = {}
        self._load_prepare_data()
    
    def _load_prepare_data(self):
        """Load and prepare data for forecasting"""
        try:
            self.df = pd.read_csv(self.data_path)
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df = self.df.sort_values('date')
            
            # Extract time series
            self.ts_data = self.df['cargo_tons'].values
            self.ts_dates = self.df['date'].values
            
            logger.info(f"✅ Loaded {len(self.ts_data)} records for forecasting")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def prepare_lstm_data(self, lookback: int = 12) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM model"""
        logger.info(f"📊 Preparing LSTM data (lookback={lookback})...")
        
        # Normalize data
        scaled_data = self.scaler.fit_transform(self.ts_data.reshape(-1, 1))
        
        X, y = [], []
        for i in range(len(scaled_data) - lookback):
            X.append(scaled_data[i:i+lookback])
            y.append(scaled_data[i+lookback])
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"✅ LSTM data prepared: X shape {X.shape}, y shape {y.shape}")
        return X, y
    
    def build_lstm_model(self, input_shape: Tuple, units: int = 128) -> keras.Model:
        """Build LSTM neural network model"""
        logger.info("🧠 Building LSTM model...")
        
        model = Sequential([
            LSTM(units, activation='relu', input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(units // 2, activation='relu', return_sequences=False),
            Dropout(0.2),
            Dense(64, activation='relu'),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        logger.info("✅ LSTM model built successfully")
        
        return model
    
    def train_lstm(self, lookback: int = 12, epochs: int = 50, batch_size: int = 16) -> Dict:
        """Train LSTM model for demand forecasting"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("⚠️ TensorFlow not available - skipping LSTM training")
            return {"status": "tensorflow_not_available"}
        
        logger.info("🚀 Training LSTM forecasting model...")
        
        try:
            # Prepare data
            X, y = self.prepare_lstm_data(lookback)
            
            # Split into train/test
            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            # Build and train model
            model = self.build_lstm_model((X_train.shape[1], 1))
            
            history = model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=0.1,
                verbose=0
            )
            
            # Evaluate
            train_pred = model.predict(X_train, verbose=0)
            test_pred = model.predict(X_test, verbose=0)
            
            # Inverse transform for metrics
            train_pred = self.scaler.inverse_transform(train_pred)
            test_pred = self.scaler.inverse_transform(test_pred)
            y_train_orig = self.scaler.inverse_transform(y_train.reshape(-1, 1))
            y_test_orig = self.scaler.inverse_transform(y_test.reshape(-1, 1))
            
            train_mae = mean_absolute_error(y_train_orig, train_pred)
            test_mae = mean_absolute_error(y_test_orig, test_pred)
            test_rmse = np.sqrt(mean_squared_error(y_test_orig, test_pred))
            test_r2 = r2_score(y_test_orig, test_pred)
            
            self.models['lstm'] = model
            self.accuracy_metrics['lstm'] = {
                'train_mae': float(train_mae),
                'test_mae': float(test_mae),
                'test_rmse': float(test_rmse),
                'test_r2': float(test_r2)
            }
            
            logger.info(f"✅ LSTM Training Complete:")
            logger.info(f"   Train MAE: {train_mae:.2f}")
            logger.info(f"   Test MAE: {test_mae:.2f}")
            logger.info(f"   Test RMSE: {test_rmse:.2f}")
            logger.info(f"   Test R²: {test_r2:.3f}")
            
            return {
                "status": "success",
                "model": "lstm",
                "metrics": self.accuracy_metrics['lstm'],
                "history": {
                    "loss": history.history['loss'],
                    "val_loss": history.history['val_loss']
                }
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM: {e}")
            return {"status": "error", "message": str(e)}
    
    def train_arima(self, order: Tuple = (5, 1, 2)) -> Dict:
        """Train ARIMA model for demand forecasting"""
        if not STATSMODELS_AVAILABLE:
            logger.warning("⚠️ Statsmodels not available - skipping ARIMA training")
            return {"status": "statsmodels_not_available"}
        
        logger.info(f"📈 Training ARIMA({order[0]}, {order[1]}, {order[2]}) model...")
        
        try:
            # Split data
            split = int(len(self.ts_data) * 0.8)
            train_data = self.ts_data[:split]
            test_data = self.ts_data[split:]
            
            # Train ARIMA
            model = ARIMA(train_data, order=order)
            fitted_model = model.fit()
            
            # Make predictions
            forecast_steps = len(test_data)
            forecast = fitted_model.get_forecast(steps=forecast_steps)
            forecast_values = forecast.predicted_mean.values
            confidence_intervals = forecast.conf_int(alpha=0.05)
            
            # Calculate metrics
            mae = mean_absolute_error(test_data, forecast_values)
            rmse = np.sqrt(mean_squared_error(test_data, forecast_values))
            r2 = r2_score(test_data, forecast_values)
            
            self.models['arima'] = fitted_model
            self.accuracy_metrics['arima'] = {
                'mae': float(mae),
                'rmse': float(rmse),
                'r2': float(r2),
                'order': order
            }
            
            logger.info(f"✅ ARIMA Training Complete:")
            logger.info(f"   MAE: {mae:.2f}")
            logger.info(f"   RMSE: {rmse:.2f}")
            logger.info(f"   R²: {r2:.3f}")
            
            return {
                "status": "success",
                "model": "arima",
                "order": order,
                "metrics": self.accuracy_metrics['arima'],
                "forecast_sample": forecast_values[:5].tolist(),
                "confidence_intervals": confidence_intervals.values[:5].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error training ARIMA: {e}")
            return {"status": "error", "message": str(e)}
    
    def train_gbm(self, test_size: float = 0.2) -> Dict:
        """Train standard Sklearn HistGradientBoostingRegressor model"""
        logger.info("🌲 Training GBM model...")
        
        try:
            # Simple feature engineering for GBM (lookback window)
            lookback = 12
            X, y = [], []
            for i in range(len(self.ts_data) - lookback):
                X.append(self.ts_data[i:i+lookback])
                y.append(self.ts_data[i+lookback])
            
            X, y = np.array(X), np.array(y)
            
            # Split
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Build and train
            model = HistGradientBoostingRegressor(
                max_iter=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            model.fit(X_train, y_train)
            
            # Evaluate
            predictions = model.predict(X_test)
            metrics = {
                'mae': float(mean_absolute_error(y_test, predictions)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, predictions))),
                'r2': float(r2_score(y_test, predictions))
            }
            
            self.models['gbm'] = model
            self.accuracy_metrics['gbm'] = metrics
            
            logger.info(f"✅ GBM model trained with R²: {metrics['r2']:.4f}")
            return {"status": "success", "metrics": metrics}
            
        except Exception as e:
            logger.error(f"Error training GBM model: {e}")
            return {"status": "error", "message": str(e)}

    def forecast_lstm(self, forecast_steps: int = 30, confidence_level: float = 0.95) -> Dict:
        """Generate LSTM-based forecast with confidence intervals"""
        if 'lstm' not in self.models:
            logger.warning("LSTM model not trained")
            return {"status": "model_not_found"}
        
        logger.info(f"🔮 Generating LSTM forecast for {forecast_steps} steps ahead...")
        
        try:
            model = self.models['lstm']
            lookback = 12
            
            # Prepare input (last 12 values)
            last_sequence = self.scaler.transform(self.ts_data[-lookback:].reshape(-1, 1))
            
            forecast = []
            predictions_std = []
            
            for _ in range(forecast_steps):
                # Predict next value
                inp = last_sequence[-lookback:].reshape(1, lookback, 1)
                pred = model.predict(inp, verbose=0)[0, 0]
                forecast.append(pred)
                
                # Estimate uncertainty (simple approach: increase with distance)
                uncertainty = np.std(self.ts_data[-100:]) * (1 + _ * 0.02)
                predictions_std.append(uncertainty)
                
                # Update sequence
                last_sequence = np.append(last_sequence, [[pred]], axis=0)
            
            # Inverse transform
            forecast_values = self.scaler.inverse_transform(np.array(forecast).reshape(-1, 1))
            
            # Calculate confidence intervals
            confidence_factor = 1.96 if confidence_level == 0.95 else 1.645
            upper_bound = forecast_values.flatten() + confidence_factor * np.array(predictions_std)
            lower_bound = forecast_values.flatten() - confidence_factor * np.array(predictions_std)
            
            # Generate dates
            last_date = pd.to_datetime(self.ts_dates[-1])
            forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, forecast_steps + 1)]
            
            result = {
                'model': 'lstm',
                'forecast_steps': forecast_steps,
                'confidence_level': confidence_level,
                'forecast': forecast_values.flatten().tolist(),
                'upper_bound': upper_bound.tolist(),
                'lower_bound': lower_bound.tolist(),
                'forecast_dates': [str(d)[:10] for d in forecast_dates]
            }
            
            self.forecasts['lstm'] = result
            logger.info(f"✅ LSTM forecast generated")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating LSTM forecast: {e}")
            return {"status": "error", "message": str(e)}
    
    def forecast_arima(self, forecast_steps: int = 30, confidence_level: float = 0.95) -> Dict:
        """Generate ARIMA-based forecast with confidence intervals"""
        if 'arima' not in self.models:
            logger.warning("ARIMA model not trained")
            return {"status": "model_not_found"}
        
        logger.info(f"🔮 Generating ARIMA forecast for {forecast_steps} steps ahead...")
        
        try:
            model = self.models['arima']
            
            # Generate forecast
            forecast_obj = model.get_forecast(steps=forecast_steps)
            forecast_values = forecast_obj.predicted_mean.values
            
            # Confidence intervals
            alpha = 1 - confidence_level
            confidence_intervals = forecast_obj.conf_int(alpha=alpha)
            lower_bound = confidence_intervals.iloc[:, 0].values
            upper_bound = confidence_intervals.iloc[:, 1].values
            
            # Generate dates
            last_date = pd.to_datetime(self.ts_dates[-1])
            forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, forecast_steps + 1)]
            
            result = {
                'model': 'arima',
                'forecast_steps': forecast_steps,
                'confidence_level': confidence_level,
                'forecast': forecast_values.tolist(),
                'upper_bound': upper_bound.tolist(),
                'lower_bound': lower_bound.tolist(),
                'forecast_dates': [str(d)[:10] for d in forecast_dates]
            }
            
            self.forecasts['arima'] = result
            logger.info(f"✅ ARIMA forecast generated")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating ARIMA forecast: {e}")
            return {"status": "error", "message": str(e)}

    def forecast_gbm(self, forecast_steps: int = 30) -> Dict:
        """Generate forecast using trained GBM model"""
        if 'gbm' not in self.models:
            logger.error("GBM model not trained yet")
            return {"status": "error", "message": "GBM model not trained"}
            
        logger.info(f"🔮 Generating GBM forecast for {forecast_steps} steps ahead...")
        
        try:
            model = self.models['gbm']
            current_batch = self.ts_data[-12:].tolist()
            forecast_values = []
            
            for _ in range(forecast_steps):
                pred = model.predict(np.array(current_batch[-12:]).reshape(1, -1))[0]
                forecast_values.append(pred)
                current_batch.append(pred)
            
            # Generate dates
            last_date = pd.to_datetime(self.ts_dates[-1])
            forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, forecast_steps + 1)]
            
            result = {
                'model': 'gbm',
                'forecast_steps': forecast_steps,
                'forecast': [float(f) for f in forecast_values],
                'forecast_dates': [str(d)[:10] for d in forecast_dates]
            }
            
            self.forecasts['gbm'] = result
            logger.info(f"✅ GBM forecast generated")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating GBM forecast: {e}")
            return {"status": "error", "message": str(e)}
    
    def ensemble_forecast(self, forecast_steps: int = 30) -> Dict:
        """Generate ensemble forecast combining LSTM and ARIMA"""
        logger.info("🎯 Generating ensemble forecast...")
        
        forecasts = []
        weights = []
        
        # Get LSTM forecast if available
        if 'lstm' in self.models:
            lstm_forecast = self.forecast_lstm(forecast_steps)
            if 'forecast' in lstm_forecast:
                forecasts.append(lstm_forecast['forecast'])
                weights.append(self.accuracy_metrics.get('lstm', {}).get('test_r2', 0.5))
        
        # Get ARIMA forecast if available
        if 'arima' in self.models:
            arima_forecast = self.forecast_arima(forecast_steps)
            if 'forecast' in arima_forecast:
                forecasts.append(arima_forecast['forecast'])
                weights.append(self.accuracy_metrics.get('arima', {}).get('r2', 0.5))
        
        # Get GBM forecast if available
        if 'gbm' in self.models:
            gbm_forecast = self.forecast_gbm(forecast_steps)
            if 'forecast' in gbm_forecast:
                forecasts.append(gbm_forecast['forecast'])
                weights.append(self.accuracy_metrics.get('gbm', {}).get('r2', 0.5))
        
        if not forecasts:
            logger.error("No models available for ensemble forecast")
            return {"status": "no_models_available"}
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Weighted average
        ensemble_forecast = np.average(np.array(forecasts), axis=0, weights=weights)
        
        # Generate dates
        last_date = pd.to_datetime(self.ts_dates[-1])
        forecast_dates = [last_date + pd.Timedelta(days=i) for i in range(1, forecast_steps + 1)]
        
        result = {
            'model': 'ensemble',
            'forecast_steps': forecast_steps,
            'models_combined': list(self.models.keys()),
            'model_weights': dict(zip(self.models.keys(), weights)),
            'forecast': ensemble_forecast.tolist(),
            'forecast_dates': [str(d)[:10] for d in forecast_dates]
        }
        
        self.forecasts['ensemble'] = result
        logger.info(f"✅ Ensemble forecast generated")
        
        return result
    
    def get_forecasting_report(self) -> Dict:
        """Generate comprehensive forecasting report"""
        logger.info("\n📊 Generating forecasting report...")
        
        report = {
            'data_summary': {
                'total_records': len(self.ts_data),
                'mean_demand': float(np.mean(self.ts_data)),
                'std_demand': float(np.std(self.ts_data)),
                'min_demand': float(np.min(self.ts_data)),
                'max_demand': float(np.max(self.ts_data))
            },
            'models_trained': list(self.models.keys()),
            'accuracy_metrics': self.accuracy_metrics,
            'forecasts': self.forecasts,
            'recommendations': self._generate_recommendations()
        }
        
        logger.info("✅ Forecasting report generated")
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate forecasting recommendations"""
        recommendations = []
        
        if 'lstm' in self.accuracy_metrics and 'arima' in self.accuracy_metrics:
            lstm_r2 = self.accuracy_metrics['lstm'].get('test_r2', 0)
            arima_r2 = self.accuracy_metrics['arima'].get('r2', 0)
            
            if lstm_r2 > arima_r2:
                recommendations.append("LSTM model performs better - use for long-term forecasts")
            else:
                recommendations.append("ARIMA model performs better - better for statistical patterns")
        
        if self.accuracy_metrics:
            avg_mae = np.mean([m.get('test_mae', m.get('mae', 0)) for m in self.accuracy_metrics.values()])
            if avg_mae > np.std(self.ts_data):
                recommendations.append("Forecast error is high - consider additional features or more training data")
        
        recommendations.append("Use ensemble forecasts for balanced predictions")
        
        return recommendations


# Test the forecasting engine
if __name__ == "__main__":
    engine = DemandForecastingEngine()
    
    print("\n" + "="*60)
    print("🚀 ML DEMAND FORECASTING ENGINE - WEEK 4")
    print("="*60)
    
    # Train models
    print("\n🧠 Training Models...")
    lstm_result = engine.train_lstm(epochs=30)
    arima_result = engine.train_arima()
    
    # Generate forecasts 
    print("\n🔮 Generating Forecasts...")
    engine.forecast_lstm(forecast_steps=30)
    engine.forecast_arima(forecast_steps=30)
    ensemble = engine.ensemble_forecast(forecast_steps=30)
    
    # Report
    report = engine.get_forecasting_report()
    
    print("\n📊 FORECASTING SUMMARY:")
    print(f"  Models Trained: {len(report['models_trained'])}")
    print(f"  Forecast Horizon: 30 days")
    print(f"  Data Points Used: {report['data_summary']['total_records']}")
    
    if ensemble.get('forecast'):
        print(f"\n📈 30-Day Ensemble Forecast:")
        print(f"  First 5 Days: {[f'{f:.0f}' for f in ensemble['forecast'][:5]]}")
    
    print("\n✅ Phase 2 Week 4 - Demand Forecasting Complete!")
