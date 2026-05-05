"""
Phase 2 Week 4 Task 2: Advanced ML Demand Models
LSTM optimization, ARIMA refinement, and model selection
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from sklearn.ensemble import HistGradientBoostingRegressor
import logging
import warnings

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, Conv1D, MaxPooling1D
    from tensorflow.keras.optimizers import Adam, RMSprop
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller, kpss
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class AdvancedLSTMForecaster:
    """Advanced LSTM model with optimization and hyperparameter tuning"""
    
    def __init__(self, lookback: int = 12):
        """Initialize LSTM forecaster"""
        self.lookback = lookback
        self.scaler = MinMaxScaler()
        self.model = None
        self.history = None
        self.metrics = {}
    
    def prepare_data(self, data: np.ndarray, test_size: float = 0.2) -> Tuple:
        """Prepare time series data for LSTM"""
        logger.info(f"📊 Preparing data with lookback={self.lookback}...")
        
        # Normalize
        scaled_data = self.scaler.fit_transform(data.reshape(-1, 1))
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - self.lookback):
            X.append(scaled_data[i:i+self.lookback])
            y.append(scaled_data[i+self.lookback])
        
        X, y = np.array(X), np.array(y)
        
        # Split
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        logger.info(f"✅ Data prepared: Train {X_train.shape}, Test {X_test.shape}")
        
        return X_train, X_test, y_train, y_test
    
    def build_advanced_model(self, input_shape: Tuple, model_type: str = 'standard') -> keras.Model:
        """Build different LSTM architectures"""
        logger.info(f"🧠 Building {model_type} LSTM model...")
        
        if model_type == 'standard':
            model = Sequential([
                LSTM(128, activation='relu', input_shape=input_shape, return_sequences=True),
                Dropout(0.2),
                LSTM(64, activation='relu', return_sequences=False),
                Dropout(0.2),
                Dense(32, activation='relu'),
                Dense(1)
            ])
        
        elif model_type == 'bidirectional':
            model = Sequential([
                Bidirectional(LSTM(64, return_sequences=True), input_shape=input_shape),
                Dropout(0.2),
                Bidirectional(LSTM(32, return_sequences=False)),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1)
            ])
        
        elif model_type == 'deep':
            model = Sequential([
                LSTM(256, activation='relu', input_shape=input_shape, return_sequences=True),
                Dropout(0.3),
                LSTM(128, activation='relu', return_sequences=True),
                Dropout(0.3),
                LSTM(64, activation='relu', return_sequences=False),
                Dropout(0.2),
                Dense(64, activation='relu'),
                Dense(32, activation='relu'),
                Dense(1)
            ])
        
        elif model_type == 'cnn_lstm':
            model = Sequential([
                Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape),
                MaxPooling1D(pool_size=2),
                LSTM(128, activation='relu', return_sequences=True),
                Dropout(0.2),
                LSTM(64, activation='relu'),
                Dropout(0.2),
                Dense(32, activation='relu'),
                Dense(1)
            ])
        
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info(f"✅ {model_type.upper()} model built")
        return model
    
    def train(self, X_train: np.ndarray, X_test: np.ndarray, 
              y_train: np.ndarray, y_test: np.ndarray,
              model_type: str = 'standard', epochs: int = 50) -> Dict:
        """Train LSTM model with advanced callbacks"""
        logger.info(f"🚀 Training {model_type} LSTM for {epochs} epochs...")
        
        try:
            # Build model
            self.model = self.build_advanced_model(
                (X_train.shape[1], 1),
                model_type=model_type
            )
            
            # Callbacks
            early_stop = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
            
            reduce_lr = ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
            
            # Train
            self.history = self.model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=16,
                validation_split=0.1,
                callbacks=[early_stop, reduce_lr],
                verbose=0
            )
            
            # Evaluate
            train_pred = self.model.predict(X_train, verbose=0)
            test_pred = self.model.predict(X_test, verbose=0)
            
            # Inverse transform
            train_pred = self.scaler.inverse_transform(train_pred)
            test_pred = self.scaler.inverse_transform(test_pred)
            y_train_orig = self.scaler.inverse_transform(y_train.reshape(-1, 1))
            y_test_orig = self.scaler.inverse_transform(y_test.reshape(-1, 1))
            
            # Metrics
            self.metrics = {
                'train_mae': float(mean_absolute_error(y_train_orig, train_pred)),
                'train_rmse': float(np.sqrt(mean_squared_error(y_train_orig, train_pred))),
                'train_r2': float(r2_score(y_train_orig, train_pred)),
                'test_mae': float(mean_absolute_error(y_test_orig, test_pred)),
                'test_rmse': float(np.sqrt(mean_squared_error(y_test_orig, test_pred))),
                'test_r2': float(r2_score(y_test_orig, test_pred)),
                'test_mape': float(mean_absolute_percentage_error(y_test_orig, test_pred)),
                'epochs_trained': len(self.history.history['loss']),
                'model_type': model_type
            }
            
            logger.info(f"✅ Training Complete:")
            logger.info(f"   Test MAE: {self.metrics['test_mae']:.2f}")
            logger.info(f"   Test RMSE: {self.metrics['test_rmse']:.2f}")
            logger.info(f"   Test R²: {self.metrics['test_r2']:.3f}")
            logger.info(f"   Test MAPE: {self.metrics['test_mape']:.2f}%")
            
            return {
                'status': 'success',
                'metrics': self.metrics,
                'model_type': model_type
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def forecast(self, data: np.ndarray, forecast_steps: int = 30) -> np.ndarray:
        """Generate forecast"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        logger.info(f"🔮 Generating forecast for {forecast_steps} steps...")
        
        # Prepare input
        last_sequence = self.scaler.transform(data[-self.lookback:].reshape(-1, 1))
        forecast = []
        
        for _ in range(forecast_steps):
            pred = self.model.predict(last_sequence[-self.lookback:].reshape(1, self.lookback, 1), verbose=0)[0, 0]
            forecast.append(pred)
            last_sequence = np.append(last_sequence, [[pred]], axis=0)
        
        # Inverse transform
        forecast = self.scaler.inverse_transform(np.array(forecast).reshape(-1, 1))
        
        logger.info(f"✅ Forecast generated")
        return forecast.flatten()


class OptimizedARIMAForecaster:
    """Optimized ARIMA model with automatic parameter selection"""
    
    def __init__(self):
        """Initialize ARIMA forecaster"""
        self.model = None
        self.fitted_model = None
        self.metrics = {}
        self.best_order = None
    
    def test_stationarity(self, data: np.ndarray) -> Dict:
        """Test if data is stationary using ADF and KPSS tests"""
        logger.info("📈 Testing stationarity...")
        
        if not STATSMODELS_AVAILABLE:
            logger.warning("Statsmodels not available")
            return {"status": "statsmodels_unavailable"}
        
        try:
            # ADF test
            adf_result = adfuller(data, autolag='AIC')
            adf_pvalue = adf_result[1]
            
            # KPSS test
            kpss_result = kpss(data, regression='c', nlags='auto')
            kpss_pvalue = kpss_result[1]
            
            is_stationary = adf_pvalue < 0.05 and kpss_pvalue > 0.05
            
            result = {
                'adf_pvalue': float(adf_pvalue),
                'kpss_pvalue': float(kpss_pvalue),
                'is_stationary': bool(is_stationary),
                'recommended_d': 0 if is_stationary else 1
            }
            
            logger.info(f"✅ ADF p-value: {adf_pvalue:.4f}, KPSS p-value: {kpss_pvalue:.4f}")
            logger.info(f"   Data is {'stationary' if is_stationary else 'non-stationary'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing stationarity: {e}")
            return {"error": str(e)}
    
    def find_optimal_order(self, data: np.ndarray, p_range=(0, 5), d_range=(0, 2), q_range=(0, 5)) -> Tuple:
        """Find optimal (p,d,q) parameters using grid search"""
        if not STATSMODELS_AVAILABLE:
            logger.warning("Statsmodels not available - using default order")
            return (1, 1, 1)
        
        logger.info("🔍 Searching for optimal ARIMA parameters...")
        
        best_aic = np.inf
        best_order = None
        tested = 0
        
        try:
            for p in range(*p_range):
                for d in range(*d_range):
                    for q in range(*q_range):
                        try:
                            model = ARIMA(data, order=(p, d, q))
                            fitted = model.fit()
                            
                            if fitted.aic < best_aic:
                                best_aic = fitted.aic
                                best_order = (p, d, q)
                            
                            tested += 1
                        except:
                            continue
            
            logger.info(f"✅ Tested {tested} combinations")
            logger.info(f"   Best order: {best_order} (AIC: {best_aic:.2f})")
            
            self.best_order = best_order
            return best_order
            
        except Exception as e:
            logger.error(f"Error finding optimal order: {e}")
            return (1, 1, 1)
    
    def train(self, data: np.ndarray, auto_order: bool = True) -> Dict:
        """Train ARIMA model"""
        if not STATSMODELS_AVAILABLE:
            return {"status": "statsmodels_unavailable"}
        
        logger.info("📊 Training ARIMA model...")
        
        try:
            # Determine order
            if auto_order:
                order = self.find_optimal_order(data)
            else:
                order = (5, 1, 2)
            
            # Train
            self.model = ARIMA(data, order=order)
            self.fitted_model = self.model.fit()
            
            # Get summary stats
            logger.info(f"✅ ARIMA{order} trained")
            logger.info(f"   AIC: {self.fitted_model.aic:.2f}")
            logger.info(f"   BIC: {self.fitted_model.bic:.2f}")
            
            return {
                'status': 'success',
                'order': order,
                'aic': float(self.fitted_model.aic),
                'bic': float(self.fitted_model.bic)
            }
            
        except Exception as e:
            logger.error(f"Error training ARIMA: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def forecast(self, forecast_steps: int = 30, confidence_level: float = 0.95) -> Dict:
        """Generate ARIMA forecast"""
        if self.fitted_model is None:
            raise ValueError("Model not trained")
        
        logger.info(f"🔮 Generating ARIMA forecast...")
        
        try:
            forecast_obj = self.fitted_model.get_forecast(steps=forecast_steps)
            forecast_values = forecast_obj.predicted_mean.values
            
            alpha = 1 - confidence_level
            ci = forecast_obj.conf_int(alpha=alpha)
            
            return {
                'status': 'success',
                'forecast': forecast_values.tolist(),
                'lower_bound': ci.iloc[:, 0].tolist(),
                'upper_bound': ci.iloc[:, 1].tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in forecast: {e}")
            return {'status': 'error', 'message': str(e)}


class GBMForecaster:
    """Gradient Boosting Machine forecaster using HistGradientBoostingRegressor"""
    
    def __init__(self, lookback: int = 12):
        """Initialize GBM forecaster"""
        self.lookback = lookback
        self.scaler = MinMaxScaler()
        self.model = HistGradientBoostingRegressor(
            max_iter=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.metrics = {}
    
    def prepare_data(self, data: np.ndarray, test_size: float = 0.2) -> Tuple:
        """Prepare time series data for GBM"""
        X, y = [], []
        scaled_data = self.scaler.fit_transform(data.reshape(-1, 1)).flatten()
        
        for i in range(len(scaled_data) - self.lookback):
            X.append(scaled_data[i:i+self.lookback])
            y.append(scaled_data[i+self.lookback])
            
        X, y = np.array(X), np.array(y)
        
        split_idx = int(len(X) * (1 - test_size))
        return X[:split_idx], X[split_idx:], y[:split_idx], y[split_idx:]
    
    def train(self, data: np.ndarray) -> Dict:
        """Train GBM model"""
        logger.info("🌲 Training GBM model...")
        try:
            X_train, X_test, y_train, y_test = self.prepare_data(data)
            self.model.fit(X_train, y_train)
            
            # Evaluate
            predictions = self.model.predict(X_test)
            self.metrics = {
                'test_mae': mean_absolute_error(y_test, predictions),
                'test_rmse': np.sqrt(mean_squared_error(y_test, predictions)),
                'test_r2': r2_score(y_test, predictions)
            }
            
            logger.info(f"✅ GBM trained: R²={self.metrics['test_r2']:.4f}")
            return {'status': 'success', 'metrics': self.metrics}
        except Exception as e:
            logger.error(f"❌ GBM training failed: {e}")
            return {'status': 'error', 'message': str(e)}
            
    def forecast(self, data: np.ndarray, horizon: int = 7) -> np.ndarray:
        """Generate GBM forecast"""
        current_batch = self.scaler.transform(data[-self.lookback:].reshape(-1, 1)).flatten()
        forecast = []
        
        for _ in range(horizon):
            pred = self.model.predict(current_batch.reshape(1, -1))[0]
            forecast.append(pred)
            current_batch = np.append(current_batch[1:], pred)
            
        return self.scaler.inverse_transform(np.array(forecast).reshape(-1, 1)).flatten()


class ModelComparator:
    """Compare different forecasting models"""
    
    def __init__(self, data: np.ndarray):
        """Initialize comparator"""
        self.data = data
        self.results = {}
    
    def compare_models(self) -> Dict:
        """Compare LSTM and ARIMA models"""
        logger.info("\n🏆 Comparing forecasting models...\n")
        
        results = {}
        
        # LSTM Models
        if TENSORFLOW_AVAILABLE:
            for model_type in ['standard', 'bidirectional', 'deep']:
                logger.info(f"\n📊 Training LSTM ({model_type})...")
                
                lstm = AdvancedLSTMForecaster()
                X_train, X_test, y_train, y_test = lstm.prepare_data(self.data)
                
                result = lstm.train(X_train, X_test, y_train, y_test, 
                                    model_type=model_type, epochs=30)
                
                if result['status'] == 'success':
                    results[f'lstm_{model_type}'] = {
                        'type': 'lstm',
                        'variant': model_type,
                        'metrics': result['metrics']
                    }
        
        # ARIMA
        if STATSMODELS_AVAILABLE:
            logger.info(f"\n📊 Training ARIMA...")
            
            arima = OptimizedARIMAForecaster()
            arima_result = arima.train(self.data, auto_order=True)
            
            if arima_result['status'] == 'success':
                results['arima'] = {
                    'type': 'arima',
                    'order': arima_result['order'],
                    'aic': arima_result['aic']
                }
        
        # GBM
        logger.info(f"\n🌲 Training GBM...")
        gbm = GBMForecaster(lookback=12)
        gbm_result = gbm.train(self.data)
        
        if gbm_result['status'] == 'success':
            results['gbm'] = {
                'type': 'gbm',
                'metrics': gbm_result['metrics']
            }
        
        # Compare and rank
        self._rank_models(results)
        
        return results
    
    def _rank_models(self, results: Dict):
        """Rank models by performance"""
        logger.info("\n🏆 MODEL RANKING:")
        logger.info("-" * 60)
        
        # Extract R² scores for ranking
        scores = {}
        for name, info in results.items():
            if 'metrics' in info:
                r2 = info['metrics'].get('test_r2', -1)
                scores[name] = r2
        
        # Sort and display
        sorted_models = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for rank, (model_name, r2_score) in enumerate(sorted_models, 1):
            logger.info(f"{rank}. {model_name}: R² = {r2_score:.3f}")


# Test advanced models
if __name__ == "__main__":
    from forecasting.historical_analysis import HistoricalDemandAnalyzer
    
    print("\n" + "="*60)
    print("🚀 ADVANCED ML DEMAND MODELS - WEEK 4 TASK 2")
    print("="*60)
    
    # Load data
    analyzer = HistoricalDemandAnalyzer()
    data = analyzer.df['cargo_tons'].values
    
    print(f"\n📊 Dataset: {len(data)} records")
    print(f"   Mean: {np.mean(data):.2f}")
    print(f"   Std: {np.std(data):.2f}")
    
    # Compare models
    comparator = ModelComparator(data)
    results = comparator.compare_models()
    
    print(f"\n✅ Phase 2 Week 4 Task 2 - Advanced ML Models Complete!")
    print(f"   Models trained: {len(results)}")
