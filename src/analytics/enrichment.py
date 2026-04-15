"""Tactical Enrichment Engine.

Maps live environmental data (weather, traffic density) to
flight-level tactical risk factors.
"""
import pandas as pd
import logging
from typing import Dict, Any, Optional
from src.data_connectors.live_sync import ExternalDataConnector

logger = logging.getLogger(__name__)

class EnrichmentEngine:
    """Enriches flight scenarios with real-world environmental risks."""

    def __init__(self, connector: Optional[ExternalDataConnector] = None):
        from src.data_connectors.live_sync import market_intel
        self.connector = connector or market_intel

    def enrich_scenario(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies real-world weather impacts to the flight scenario.
        Modifies weather_risk and causal_factor based on airport METARs.
        """
        if df.empty:
            return df

        # Identify unique airports in the scenario
        airports = set(df['origin'].unique()) | set(df['destination'].unique())
        
        # Fetch weather for each airport
        weather_map = {}
        for ap in airports:
            try:
                weather_map[ap] = self.connector.fetch_real_metar(ap)
            except Exception as e:
                logger.warning(f"Could not fetch weather for {ap} during enrichment: {e}")

        # Update flight risks based on weather
        def apply_risks(row):
            origin_w = weather_map.get(row['origin'])
            dest_w = weather_map.get(row['destination'])
            
            risk_bonus = 0.0
            factors = []

            # Check Origin
            if origin_w:
                vis = origin_w.get('visibility_m', 9999)
                wind = origin_w.get('wind_speed_kt', 0)
                
                if vis < 800:
                    risk_bonus += 0.3
                    factors.append(f"Low Visibility at {row['origin']}")
                elif vis < 2000:
                    risk_bonus += 0.1
                
                if wind > 25:
                    risk_bonus += 0.2
                    factors.append(f"High Wind at {row['origin']}")

            # Check Destination
            if dest_w:
                vis = dest_w.get('visibility_m', 9999)
                if vis < 500:
                    risk_bonus += 0.4 # Severe risk of diversion
                    factors.append(f"Critical Fog at {row['destination']}")

            if risk_bonus > 0:
                row['weather_risk'] = min(1.0, row['weather_risk'] + risk_bonus)
                if factors:
                    row['causal_factor'] = "Weather: " + " & ".join(factors)
                    # Force a tactical pressure flag if weather is severe
                    if risk_bonus >= 0.3:
                        row['slot_pressure_flag'] = True

            return row

        return df.apply(apply_risks, axis=1)

enricher = EnrichmentEngine()
