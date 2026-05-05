import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Import your FastAPI app
from api.main import app

client = TestClient(app)

def test_risk_analysis_endpoint():
    """Test the risk analysis endpoint"""
    test_data = {
        "schedule_id": "test_schedule_001",
        "route": "DAR_KAPIRI",
        "planned_departure": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "historical_issues": [
            {"date": (datetime.utcnow() - timedelta(days=10)).isoformat(), 
             "issue_type": "delay", 
             "duration_minutes": 45}
        ]
    }
    
    with patch('api.services.risk_analyzer.analyze_risk') as mock_analyze:
        mock_analyze.return_value = {
            "risk_score": 0.65,
            "bottlenecks": ["peak_hour_traffic", "maintenance_zone"],
            "recommendations": [
                "Consider departing 30 minutes earlier",
                "Add backup equipment on standby"
            ]
        }
        
        response = client.post(
            "/api/risk/analyze",
            json=test_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "bottlenecks" in data
        assert "recommendations" in data

def test_what_if_scenario():
    """Test what-if scenario analysis"""
    scenario = {
        "base_schedule_id": "test_schedule_001",
        "changes": {
            "departure_time_shift": "+1h",
            "alternative_route": "ALTERNATE_ROUTE_001",
            "equipment_changes": ["add_engine"]
        }
    }
    
    with patch('api.services.scenario_analyzer.evaluate_scenario') as mock_eval:
        mock_eval.return_value = {
            "impact_analysis": {
                "time_impact": 45,
                "cost_impact": 1250.50,
                "reliability_change": 0.15
            },
            "risk_changes": {
                "current_risk": 0.65,
                "projected_risk": 0.45,
                "risk_reduction": 0.20
            },
            "cost_implications": {
                "additional_fuel": 850.00,
                "labor_costs": 400.50,
                "total_cost_impact": 1250.50
            }
        }
        
        response = client.post(
            "/api/schedule/what-if",
            json=scenario
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "impact_analysis" in data
        assert "risk_changes" in data
        assert "cost_implications" in data

def test_risk_analysis_with_invalid_data():
    """Test risk analysis with invalid input data"""
    invalid_data = {"schedule_id": ""}  # Missing required fields
    response = client.post("/api/risk/analyze", json=invalid_data)
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main(["-v"])
