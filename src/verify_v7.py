import pandas as pd
import sys
import os
sys.path.append(os.getcwd())

from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.optimizer.dt_solver import DigitalTwinSolver

print("--- v7.0 Integration Test (Lightweight) ---")
sim = AdvancedAirlineSimulator(seed=42)
df = sim.generate_full_scenario(days=1).head(30) # Only 30 flights for quick test
print(f"Generated {len(df)} flights.")

solver = DigitalTwinSolver(df)
print("Solving with advanced constraints...")
results = solver.solve_winning(max_time_sec=10)

if results is not None:
    print("✅ Solution Found!")
    print(f"Avg SAF Usage: {results['saf_usage'].mean():.2f}%")
    print(f"Total Flights: {len(results)}")
else:
    print("❌ Failed to find solution.")
