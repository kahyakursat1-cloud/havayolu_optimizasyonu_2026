import pandas as pd
import sys
import os
import numpy as np
from pathlib import Path

# Add src to path
sys.path.append(str(Path(os.getcwd())))

from src.optimizer.dt_solver import DigitalTwinSolver

def run_systematic_validation():
    # Load Real Data
    csv_path = "docs/makale/eswa_submission/experiments/real_flights.csv"
    df_raw = pd.read_csv(csv_path)
    df_raw['departure_time'] = pd.to_datetime(df_raw['departure_time'])
    df_raw['arrival_time'] = pd.to_datetime(df_raw['arrival_time'])
    if 'market_qsi_weight' not in df_raw.columns:
        df_raw['market_qsi_weight'] = 1.0
    if 'departure_hour' not in df_raw.columns:
        df_raw['departure_hour'] = df_raw['departure_time'].dt.hour

    scenarios = {
        "S1: Hub Closure (IST 3h)": {
            "type": "closure",
            "hub_closures": {('IST', 8): 0, ('IST', 9): 0, ('IST', 10): 0}
        },
        "S2: Crew Shortage (20%)": {
            "type": "crew_strike",
            "strike_ratio": 0.2
        },
        "S3: Fleet Grounding (5 AC)": {
            "type": "mro",
            "ground_count": 5
        },
        "S4: JFK/LHR Slot Limit": {
            "type": "slot_limit",
            "hub_closures": {('JFK', h): 1 for h in range(24)} | {('LHR', h): 1 for h in range(24)}
        }
    }

    results = []

    for name, config in scenarios.items():
        print(f"\n>>> Running {name}...")
        df = df_raw.copy()
        hub_closures = config.get("hub_closures", {})
        
        if config["type"] == "crew_strike":
            crews = df['crew_id'].unique()
            struck_crews = np.random.choice(crews, int(len(crews) * config["strike_ratio"]), replace=False)
            # Remove struck crews from availability
            # In our solver, we can just remove the flights or make them impossible
            # Better: remove the crew from the data so compute_eligible_crews finds nothing
            df = df[~df['crew_id'].isin(struck_crews)]
            
        if config["type"] == "mro":
            acs = df['aircraft_id'].unique()
            grounded_acs = np.random.choice(acs, config["ground_count"], replace=False)
            df = df[~df['aircraft_id'].isin(grounded_acs)]

        solver = DigitalTwinSolver(df)
        # Use Hybrid RH for validation as it's the proposed method
        res = solver.solve_with_windows(num_workers=4, window_size_hrs=4, hub_closures=hub_closures)
        
        n_canceled = (res['is_canceled'] == 1).sum()
        # Flights completely removed (strike/mro) also count as cancellations in the final report
        missing = len(df_raw) - len(res)
        total_canceled = n_canceled + missing
        avg_delay = res['assigned_delay'].mean()
        
        results.append({
            "Scenario": name,
            "Canceled": total_canceled,
            "Canceled_Pct": (total_canceled / len(df_raw)) * 100,
            "Avg_Delay": avg_delay
        })

    # Print Summary Table
    val_df = pd.DataFrame(results)
    print("\n=== SYSTEMATIC REAL-WORLD VALIDATION ===")
    print(val_df.to_string(index=False))
    val_df.to_json("docs/makale/eswa_submission/experiments/real_validation_results.json", orient='records')

if __name__ == "__main__":
    run_systematic_validation()
