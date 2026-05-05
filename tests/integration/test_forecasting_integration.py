import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import your FastAPI app
from api.main import app

client = TestClient(app)

@pytest.fixture
def sample_historical_data():
    """Generate sample historical data for testing"""
    date_rng = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    return {
        "route": "DAR_KAPIRI",
        "data": [{
            "date": date.strftime('%Y-%m-%d'),
            "demand": int(np.random.normal(100, 20)),
            "weather": np.random.choice(["sunny", "cloudy", "rainy"]),
            "is_weekend": date.weekday() >= 5
        } for date in date_rng]
    }

def test_forecast_endpoint(sample_historical_data):
    """Test the forecast endpoint with valid data"""
    with patch('api.services.forecast_service.predict_demand') as mock_predict:
        # Mock the prediction response
        mock_predict.return_value = {
            "forecast": [{"date": "2026-01-01", "demand": 120, "confidence": 0.85}],
            "metrics": {"mae": 8.5, "rmse": 10.2}
        }
        
        response = client.post(
            "/api/forecast",
            json=sample_historical_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert "metrics" in data
        assert len(data["forecast"]) > 0

def test_forecast_validation():
    """Test forecast validation and metrics"""
    test_data = {
        "route": "test_route",
        "forecast": [{"date": "2026-01-01", "predicted": 100}],
        "actual": [{"date": "2026-01-01", "actual": 95}]
    }
    
    response = client.post(
        "/api/forecast/validate",
        json=test_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "mae" in data["metrics"]
    assert "rmse" in data["metrics"]

def test_forecast_with_invalid_data():
    """Test forecast endpoint with invalid data"""
    invalid_data = {"route": "INVALID", "data": []}
    response = client.post("/api/forecast", json=invalid_data)
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main(["-v"])
