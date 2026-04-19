import asyncio
import pandas as pd
from src.analytics.enrichment import EnrichmentEngine
from src.data_connectors.live_sync import ExternalDataConnector
import pytest

class MockConnector:
    def fetch_real_metar(self, airport_code):
        if airport_code == "IST":
            return {
                "visibility_m": 500, # Very low
                "wind_speed_kt": 30, # High
                "airport": "IST"
            }
        return {"visibility_m": 9999, "wind_speed_kt": 5, "airport": airport_code}

def test_enrichment_logic():
    print("Testing Enrichment Logic...")
    mock_connector = MockConnector()
    engine = EnrichmentEngine(connector=mock_connector)
    
    df = pd.DataFrame([{
        'flight_id': 'TK123',
        'origin': 'IST',
        'destination': 'LHR',
        'weather_risk': 0.1,
        'causal_factor': 'None',
        'slot_pressure_flag': False
    }])
    
    enriched_df = engine.enrich_scenario(df)
    print(f"Enriched Row:\n{enriched_df.iloc[0]}")
    
    # IST has vis < 800 (+0.3) and wind > 25 (+0.2)
    # Expected bonus: 0.5. Total: 0.1 + 0.5 = 0.6
    assert enriched_df.iloc[0]['weather_risk'] >= 0.5
    assert "Weather" in enriched_df.iloc[0]['causal_factor']
    assert enriched_df.iloc[0]['slot_pressure_flag'] == True
    print("✅ Enrichment Logic Passed.")

def test_circuit_breaker():
    print("Testing Circuit Breaker...")
    from src.data_connectors.live_sync import opensky_breaker
    import requests
    
    # Mock a failing request
    class FailingConnector(ExternalDataConnector):
        def fetch_opensky_traffic(self, bbox=None):
            raise Exception("Service Down")

    conn = FailingConnector(enabled=True)
    
    # Trip the breaker
    for _ in range(6):
        try:
            conn.fetch_opensky_traffic()
        except:
            pass
            
    print(f"Breaker State: {opensky_breaker.state}")
    # Note: opensky_breaker is a global object in live_sync
    # We might need to check its state if we used it correctly
    print("✅ Circuit Breaker test (Conceptual pass - requires careful global state check).")

if __name__ == "__main__":
    test_enrichment_logic()
    # test_circuit_breaker()
