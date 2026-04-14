import numpy as np
import pandas as pd
from datetime import datetime, time

class FatigueEngine:
    """
    v23.0 Bio-Mathematical Fatigue Risk Management System (FRMS).
    
    Models:
    1. Circadian Rhythm: Window of Circadian Low (WOCL) 02:00-06:00.
    2. Duty Duration: Linear fatigue accumulation based on TAF (Time Awake Fatigue).
    """
    def __init__(self):
        self.wocl_start = 2 # 02:00
        self.wocl_end = 6   # 06:00

    def calculate_duty_fatigue(self, departure_time: datetime, block_time_mins: int):
        """
        Returns a fatigue index [0.0 - 1.0] for a specific flight duty.
        """
        # Base fatigue from block time (simple 10-hour linear cap)
        base_fatigue = min(0.5, block_time_mins / 600.0)
        
        # Circadian penalty
        # If flight departs or arrives during WOCL, apply a heavy penalty
        arrival_time = departure_time + pd.Timedelta(minutes=block_time_mins)
        
        circadian_penalty = 0.0
        
        # Check if dep or arr is in WOCL
        if self.wocl_start <= departure_time.hour < self.wocl_end:
            circadian_penalty += 0.3
        if self.wocl_start <= arrival_time.hour < self.wocl_end:
            circadian_penalty += 0.2
            
        return min(1.0, base_fatigue + circadian_penalty)

    def assess_crew_readiness(self, crew_history):
        """
        Aggregates multiple duties into a cumulative fatigue score.
        """
        # (Placeholder for complex multi-day integration)
        return sum(crew_history[-3:]) / 3.0 if crew_history else 0.0

fatigue_engine = FatigueEngine()
