import pandas as pd
import numpy as np

class AviationKPIEngine:
    @staticmethod
    def calculate_fleet_kpis(df):
        """
        🚀 v16.0 Digital Airline Analyst: 
        Calculates ASK, RPK, and PLF metrics based on TEKNOFEST 2026 standards.
        """
        if df.empty:
            return {"ask": 0, "rpk": 0, "plf": 0, "cqi": 0}

        active_flights = df[df['is_canceled'] == 0] if 'is_canceled' in df.columns else df
        
        # 1. ASK (Available Seat Kilometers)
        ask = (active_flights['ac_capacity'] * active_flights['dist_km']).sum()
        
        # 2. RPK (Revenue Passenger Kilometers)
        rpk = (active_flights['passenger_count'] * active_flights['dist_km']).sum()
        
        # 3. PLF (Passenger Load Factor)
        plf = (rpk / ask) if ask > 0 else 0
        
        # 4. CQI (Connection Quality Index)
        # Weighted average of pax connections vs expected delays
        cqi = 0
        if 'pax_connection_count' in active_flights.columns:
            total_conn = active_flights['pax_connection_count'].sum()
            avg_delay = active_flights['assigned_delay'].mean() if 'assigned_delay' in active_flights.columns else 0
            # Higher connections + Lower delay = Higher CQI
            cqi = min(100, (total_conn / (len(active_flights) * 20)) * 100 * (1 - avg_delay/120))
            
        return {
            "ask": round(ask, 2),
            "rpk": round(rpk, 2),
            "plf": round(plf * 100, 1), # Percentage
            "cqi": round(cqi, 1)
        }

    @staticmethod
    def analyze_disruption_impact(df_old, df_new):
        """
        Measures the quality of recovery after a stress test.
        """
        kpi_old = AviationKPIEngine.calculate_fleet_kpis(df_old)
        kpi_new = AviationKPIEngine.calculate_fleet_kpis(df_new)
        
        return {
            "recovery_efficiency": round((kpi_new['rpk'] / kpi_old['rpk']) * 100, 1),
            "plf_delta": round(kpi_new['plf'] - kpi_old['plf'], 2)
        }
