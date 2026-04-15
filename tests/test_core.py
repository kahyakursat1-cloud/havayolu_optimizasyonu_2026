import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.analytics.forecast_engine import forecaster
from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.generator.produce_mega_dataset import produce_mega_benchmark

client = TestClient(app)

def test_api_health():
    """Test if main dashboard and scenario endpoints are online."""
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


def test_optimizer_explanations_endpoint():
    """Explanation endpoint should expose both summary and flight-level reasons."""
    response = client.get("/api/optimizer/explanations")
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "flights" in payload


def test_decision_report_endpoint():
    """Decision report endpoint should return summary metadata and highlights."""
    response = client.get("/api/reports/decision-summary?filter=all")
    assert response.status_code == 200
    payload = response.json()
    assert "generated_at" in payload
    assert payload["filter"] == "all"
    assert "summary" in payload
    assert "highlights" in payload


def test_csv_export_endpoint():
    """CSV export should return attachment headers and CSV payload."""
    response = client.get("/api/export/scenario.csv?filter=all")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"aviation_scenario_all.csv\"" in response.headers["content-disposition"]
    assert "flight_id" in response.text


def test_produce_mega_benchmark_writes_raw_dataset(tmp_path):
    """Dataset generator should write a valid CSV to the requested path."""
    output_path = tmp_path / "scenario.csv"
    generated_path = produce_mega_benchmark(days=2, output_path=output_path, seed=42)
    assert generated_path == output_path
    assert generated_path.exists()

    content = generated_path.read_text(encoding="utf-8")
    assert "flight_id" in content
    assert "aircraft_id" in content


def test_model_benchmark_endpoint():
    """Benchmark endpoint should compare the three forecasting/classification baselines."""
    response = client.get("/api/analytics/model-benchmark")
    assert response.status_code == 200
    payload = response.json()
    assert "dataset" in payload
    assert "models" in payload
    names = {model["name"] for model in payload["models"]}
    assert {"LogisticRegression", "XGBoost", "LSTM"}.issubset(names)
