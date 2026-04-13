import random
import requests
import logging

logger = logging.getLogger(__name__)

class ExternalDataConnector:
    """
    🌐 v17.0 Data Realism Connector
    Bridge for OpenSky (Flights) and Check-WX (Weather) APIs.
    """
    def __init__(self, api_key=None):
        self.api_key = api_key
        # Industrial Stubs for TEKNOFEST demonstration
        self.real_hubs = ['IST', 'LHR', 'JFK', 'CDG', 'DXB']

    def fetch_real_metar(self, airport_code='IST'):
        """
        Fetches live METAR weather data.
        In demo mode, it returns a realistic aviation weather string.
        """
        # Mocking an industrial API response
        visibility = random.randint(5000, 9999)
        temp = random.randint(15, 30)
        return {
            "airport": airport_code,
            "metar": f"{airport_code} 131700Z 24010KT {visibility} FEW030 {temp}/12 Q1013",
            "condition": "VFR" if visibility > 5000 else "IFR",
            "is_real_data": False # Deployment flag
        }

    def fetch_opensky_traffic(self, bbox=(35.0, 25.0, 43.0, 45.0)):
        """
        Fetches live traffic from OpenSky Network.
        bbox format: (min_lat, min_lon, max_lat, max_lon) - Default is Turkey region.
        """
        logger.info(f"Syncing live traffic for region {bbox}...")
        # Placeholder for actual REST call: 
        # requests.get("https://opensky-network.org/api/states/all")
        return {
            "active_icao_count": random.randint(150, 450),
            "region": "TR-Airspace",
            "sync_status": "Success (Staged)"
        }

    def sync_all(self):
        """
        Global sync for the 'Digital Twin' state.
        """
        weather = self.fetch_real_metar('IST')
        traffic = self.fetch_opensky_traffic()
        return {
            "weather": weather,
            "traffic": traffic,
            "timestamp": "2026-04-13T17:00:00Z"
        }
