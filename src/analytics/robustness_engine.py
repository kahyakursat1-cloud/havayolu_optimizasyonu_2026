import pandas as pd
import numpy as np
import copy
import logging

logger = logging.getLogger("AviationSingularity.Robustness")

class RobustnessSimulator:
    """
    v20.0 Digital Twin Resilience Layer.
    Stress-tests optimized schedules against stochastic operational disruptions.
    """
    def __init__(self, n_simulations=1000):
        self.n_simulations = n_simulations

    def evaluate_schedule(self, df: pd.DataFrame) -> dict:
        """
        Runs Monte Carlo simulations on the provided schedule.
        Injects primary delays (weather/tech) and measures secondary propagation.
        """
        results = []
        
        # Ensure data is sorted for propagation analysis
        schedule = df.sort_values(['assigned_aircraft', 'departure_time']).copy()
        
        for i in range(self.n_simulations):
            sim_df = schedule.copy()
            total_secondary_delay = 0
            
            # Group by aircraft to track tails
            for ac_id, group in sim_df.groupby('assigned_aircraft'):
                if ac_id == "None": continue
                
                prev_arrival_limit = None
                
                for idx, flight in group.iterrows():
                    # 1. Primary Disruption Risk (Random Sample)
                    # We use the weather_risk as a probability and tech_failure_prob as severity
                    is_disrupted = np.random.random() < flight['weather_risk']
                    primary_delay = np.random.exponential(20.0) if is_disrupted else 0
                    
                    # 2. Propagation Logic
                    # Arrival time = Planned Arrival + Assigned Delay (Solver) + Primary Delay
                    actual_dep = flight['departure_time'] + pd.Timedelta(minutes=primary_delay)
                    
                    # If this is not the first leg, check the turn-around constraint
                    if prev_arrival_limit and actual_dep < prev_arrival_limit:
                        secondary_delay = (prev_arrival_limit - actual_dep).total_seconds() / 60
                        total_secondary_delay += secondary_delay
                        actual_dep = prev_arrival_limit
                    
                    # Actual Arrival including both primary and propagated delays
                    actual_arr = actual_dep + pd.Timedelta(minutes=flight['block_time'])
                    
                    # Set the limit for the next leg (Minimum Turnaround of 45 mins)
                    prev_arrival_limit = actual_arr + pd.Timedelta(minutes=45)
            
            results.append(total_secondary_delay)
            
        avg_secondary = np.mean(results)
        max_secondary = np.max(results)
        
        # Stability Score: Higher is better. 100 = 0 propagated delays.
        # We scale it relative to the total number of flights.
        stability_score = max(0, 100 - (avg_secondary / len(df)) * 5)
        
        return {
            "stability_score": round(stability_score, 2),
            "avg_propagation_mins": round(avg_secondary, 2),
            "worst_case_propagation": round(max_secondary, 2),
            "simulations_run": self.n_simulations
        }
