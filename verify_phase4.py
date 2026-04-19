from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_observability_endpoints():
    print("Verifying Observability Endpoints...")
    
    # Test /healthz (Liveness)
    resp = client.get("/healthz")
    print(f"/healthz status: {resp.status_code}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    
    # Test /readyz (Readiness)
    # Note: This might return 503 if DB is not connected in this test env
    resp = client.get("/readyz")
    print(f"/readyz status: {resp.status_code}")
    # In this test environment, it's okay if it fails as long as it's a known endpoint
    assert resp.status_code in [200, 503]
    
    # Test /metrics (Prometheus)
    resp = client.get("/metrics")
    print(f"/metrics status: {resp.status_code}")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text
    
    print("✅ Observability Endpoints Verified.")

if __name__ == "__main__":
    test_observability_endpoints()
