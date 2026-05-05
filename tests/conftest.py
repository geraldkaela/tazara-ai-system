import pytest
from fastapi.testclient import TestClient
from api.main import app
from database.db_manager import db_manager as db

@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI app"""
    with TestClient(app) as client:
        yield client

@pytest.fixture(autouse=True)
def run_around_tests():
    """Setup and teardown for each test"""
    # Setup: Clear test data if needed (handle missing tables gracefully)
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if tables exist before trying to delete
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'forecast_metrics'
                    );
                """)
                if cur.fetchone()[0]:
                    cur.execute("""
                        DELETE FROM forecast_metrics 
                        WHERE route LIKE 'test_%' OR route = 'INVALID' OR route = 'test_route'
                    """)
                
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'risk_assessments'
                    );
                """)
                if cur.fetchone()[0]:
                    cur.execute("""
                        DELETE FROM risk_assessments 
                        WHERE schedule_id LIKE 'test_%' OR schedule_id = ''
                    """)
    except Exception as e:
        # Log but don't fail if tables don't exist
        print(f"Warning: Could not clean test data: {e}")
    
    yield
    # Teardown: No need for explicit cleanup with autocommit

@pytest.fixture
def mock_forecast_service():
    """Mock the forecast service"""
    with patch('api.services.forecast_service.predict_demand') as mock:
        mock.return_value = {
            "forecast": [{"date": "2026-01-01", "demand": 120, "confidence": 0.85}],
            "metrics": {"mae": 8.5, "rmse": 10.2}
        }
        yield mock

@pytest.fixture
def mock_risk_analyzer():
    """Mock the risk analyzer service"""
    with patch('api.services.risk_analyzer.analyze_risk') as mock:
        mock.return_value = {
            "risk_score": 0.65,
            "bottlenecks": ["peak_hour_traffic"],
            "recommendations": ["Consider earlier departure"]
        }
        yield mock
