import pandas as pd
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(os.getcwd())))

from src.optimizer.dt_solver import DigitalTwinSolver

def run_case_study():
    # 1. Load Real Data
    csv_path = "docs/makale/eswa_submission/experiments/real_flights.csv"
    df = pd.read_csv(csv_path)
    df['departure_time'] = pd.to_datetime(df['departure_time'])
    df['arrival_time'] = pd.to_datetime(df['arrival_time'])
    
    # Add missing columns expected by solver
    if 'market_qsi_weight' not in df.columns:
        df['market_qsi_weight'] = 1.0
    if 'departure_hour' not in df.columns:
        df['departure_hour'] = df['departure_time'].dt.hour
    
    print(f"Loaded {len(df)} real flights.")
    
    # 2. Inject Disruption: IST Closure between 08:00 and 11:00
    # Hub closure: IST capacity is 0 for hours 8, 9, 10
    hub_closures = {
        ('IST', 8): 0,
        ('IST', 9): 0,
        ('IST', 10): 0
    }
    
    # 3. Run Solver
    solver = DigitalTwinSolver(df)
    
    print("\n--- Running Monolithic CP-SAT (Baseline) ---")
    res_cp = solver.solve_with_windows(num_workers=4, window_size_hrs=24, hub_closures=hub_closures) 
    
    print("\n--- Running Hybrid Rolling Horizon (Proposed) ---")
    res_hybrid = solver.solve_with_windows(num_workers=4, window_size_hrs=4, hub_closures=hub_closures)
    
    # 4. Report Results
    print("\n=== CASE STUDY RESULTS ===")
    for mode, r in {"Monolithic": res_cp, "Hybrid": res_hybrid}.items():
        n_flights = len(r)
        n_canceled = (r['is_canceled'] == 1).sum()
        avg_delay = r['assigned_delay'].mean()
        
        print(f"Mode: {mode}")
        print(f"  Total Flights: {n_flights}")
        print(f"  Canceled: {n_canceled}")
        print(f"  Avg Delay: {avg_delay:.2f} min")
        print("-" * 30)

if __name__ == "__main__":
    run_case_study()
