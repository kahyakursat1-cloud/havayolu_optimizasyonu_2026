import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.analytics.forecast_engine import forecaster
from src.generator.synthetic_env import AdvancedAirlineSimulator

client = TestClient(app)

def test_api_health():
    """Test if main dashboard and scenario endpoints are online."""
    response = client.get("/")
    assert response.status_code == 200
    
    response = client.get("/api/scenario")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_forecast_engine():
    """Ensure forecasting engine returns structured data."""
    mock_scenario = [{"load_factor": 0.8}, {"load_factor": 0.6}]
    res = forecaster.get_forecast(mock_scenario)
    assert len(res) == 7
    assert "predicted_plf" in res[0]
    assert "disruption_risk" in res[0]

def test_solver_load():
    """Verify synthetic env can generate valid tactical data."""
    env = AdvancedAirlineSimulator()
    df = env.generate_full_scenario(days=1)
    assert not df.empty
    assert 'origin' in df.columns
