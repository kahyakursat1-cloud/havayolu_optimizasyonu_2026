import logging
import random

logger = logging.getLogger("AviationSingularity.EnergyGrid")

class MicroGridOrchestrator:
    """
    v27.0 Airport Micro-Grid & V2G Optimization.
    
    Orchestrates EV chargers as energy buffers for aircraft recharging 
    to protect the grid and lower costs.
    """
    def __init__(self):
        self.ev_unit_capacity_kwh = 75 # Average EV battery
        self.ev_discharge_limit = 0.2  # Max 20% discharge for peak-shaving
        self.v2g_efficiency = 0.94

    def calculate_grid_buffer(self, flight_count):
        """
        v27.0 Dynamic Scaling (Point 1):
        EV Parking units scale with the daily flight load (estimated visitors).
        """
        # Dynamic Scaling Logic: 25 EVs per flight handled
        estimated_evs = int(flight_count * 25)
        
        # Calculate Total V2G Buffer (MWh)
        total_mwh = (estimated_evs * self.ev_unit_capacity_kwh * self.ev_discharge_limit * self.v2g_efficiency) / 1000.0
        
        # Peak Shaving Potential
        savings_percentage = 0.32 if total_mwh > 2.0 else 0.15
        
        return {
            "node": "IST_MicroGrid_Alpha",
            "active_ev_units": estimated_evs,
            "v2g_buffer_mwh": round(total_mwh, 2),
            "peak_shaving_potential": f"{savings_percentage:.0%}",
            "grid_stability": "STABLE" if total_mwh > 1.0 else "UNSTABLE"
        }

energy_grid = MicroGridOrchestrator()
