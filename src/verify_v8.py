import pandas as pd
import sys
import os
import numpy as np
sys.path.append(os.getcwd())

from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.optimizer.dt_solver import DigitalTwinSolver
from src.optimizer.hybrid_ga import HybridGA

print("--- v8.0 Scientific Integration Test ---")
sim = AdvancedAirlineSimulator(seed=42)
df = sim.generate_full_scenario(days=1).head(40) # 40 flights
print(f"Generated {len(df)} flights.")
print(f"Business Pax Total: {df['business_pax'].sum()}")

solver = DigitalTwinSolver(df)
print("Solving with Scientific Constraints (Contrail Weight: 1000)...")
results = solver.solve_winning(max_time_sec=15, contrail_penalty_weight=1000)

if results is not None:
    print("✅ MILP Solution Found!")
    print(f"Avg Contrail Risk: {results['contrail_risk'].mean():.2f}")
    
    print("\nTesting Hybrid GA with GARSRev...")
    ga = HybridGA(df, generations=5)
    ga_results = ga.solve()
    print(f"✅ GA Solution Found! Best Score: {ga.stats[-1]['best'] if ga.stats else 'N/A'}")
    print(f"GA Standard Deviation: {ga.stats[-1]['std'] if ga.stats else 'N/A'}")
else:
    print("❌ Failed to find MILP solution.")
