"""CI tests for model training, evaluation, and artifact validation.

Usage:
    pytest test_models.py -v
"""
import json
from pathlib import Path
import pytest
import pandas as pd


class TestDataPipeline:
    """Test data loading and feature engineering."""
    
    def test_processed_csv_exists(self):
        """Verify processed demand CSV exists with data."""
        path = Path("data/simulated/cargo_demand.csv")
        assert path.exists(), f"Processed CSV not found: {path}"
        
        df = pd.read_csv(path, parse_dates=["date"])
        assert len(df) > 0, "Processed CSV is empty"
        assert "cargo_tons" in df.columns, "Missing cargo_tons column"
    
    def test_features_csv_exists(self):
        """Verify features CSV exists with expected columns."""
        path = Path("data/processed/features.csv")
        assert path.exists(), f"Features CSV not found: {path}"
        
        df = pd.read_csv(path, parse_dates=["date"])
        assert len(df) > 50, "Features CSV has too few rows"
        
        expected_cols = ["cargo_tons", "lag_1", "lag_7", "roll_mean_7", "dayofweek", "month"]
        for col in expected_cols:
            assert col in df.columns, f"Missing expected column: {col}"


class TestModelTraining:
    """Test model training artifacts."""
    
    def test_lstm_model_exists(self):
        """Verify LSTM model was saved."""
        path = Path("models/lstm_model.keras")
        assert path.exists(), f"LSTM model not found: {path}"
        assert path.stat().st_size > 10000, "LSTM model file is too small"
    
    def test_training_metrics_exist(self):
        """Verify training metrics JSON exists and is valid."""
        path = Path("metrics/training_metrics.json")
        assert path.exists(), f"Training metrics file not found: {path}"
        
        with open(path) as f:
            metrics = json.load(f)
        
        assert "lstm" in metrics, "LSTM metrics missing"
        assert "timestamp" in metrics, "Timestamp missing"
    
    def test_lstm_metrics_reasonable(self):
        """Verify LSTM metrics are in reasonable ranges."""
        path = Path("metrics/training_metrics.json")
        with open(path) as f:
            metrics = json.load(f)
        
        lstm_metrics = metrics.get("lstm", {})
        if "error" not in lstm_metrics:
            assert 0 <= lstm_metrics.get("rmse", 0) < 10, "RMSE out of expected range"
            assert 0 <= lstm_metrics.get("mae", 0) < 10, "MAE out of expected range"
            assert -1 <= lstm_metrics.get("r2", 0) <= 1, "R² out of expected range"


class TestModelRegistry:
    """Test model versioning and registry."""
    
    def test_registry_can_be_created(self):
        """Verify model registry can be synced from metrics."""
        from forecasting.model_registry import sync_from_metrics, load_registry
        
        sync_from_metrics()
        registry = load_registry()
        
        assert "models" in registry, "Registry missing models key"
        # At least LSTM should be registered
        assert "lstm" in registry["models"], "LSTM not registered"
    
    def test_registry_has_model_versions(self):
        """Verify registry tracks model versions."""
        from forecasting.model_registry import load_registry
        
        registry = load_registry()
        if "lstm" in registry.get("models", {}):
            lstm_info = registry["models"]["lstm"]
            assert "versions" in lstm_info, "Versions missing from registry"
            assert len(lstm_info["versions"]) > 0, "No versions recorded"


class TestOutputDirectories:
    """Test output directory structure."""
    
    def test_models_dir_exists(self):
        """Verify models directory exists."""
        path = Path("models")
        assert path.exists(), "models directory does not exist"
        assert path.is_dir(), "models is not a directory"
    
    def test_metrics_dir_exists(self):
        """Verify metrics directory exists."""
        path = Path("metrics")
        assert path.exists(), "metrics directory does not exist"
        assert path.is_dir(), "metrics is not a directory"
    
    def test_outputs_dir_exists(self):
        """Verify forecasting outputs directory exists."""
        path = Path("forecasting/outputs")
        assert path.exists(), "forecasting/outputs directory does not exist"
        assert path.is_dir(), "forecasting/outputs is not a directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
