import time
import pandas as pd
from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.optimizer.dt_solver import DigitalTwinSolver

def run_performance_audit():
    print("🔥 INITIATING v18.5 GLOBAL STRESS TEST (1000+ FLIGHTS) 🔥")
    print("-" * 50)
    
    sim = AdvancedAirlineSimulator(seed=2026)
    
    # Generate a massive load (approx 3 days of heavy operation)
    start_time = time.time()
    df = sim.generate_full_scenario(days=4) 
    gen_time = time.time() - start_time
    
    flight_count = len(df)
    print(f"📦 Scenario Generated: {flight_count} flights")
    print(f"⏱️ Generation Time: {gen_time:.2f}s")
    print("-" * 50)
    
    # Run Optimization
    print("⚡ Engaging Digital Twin Solver (Rolling Windows)...")
    solver = DigitalTwinSolver(df)
    opt_start = time.time()
    result = solver.solve_with_windows(window_size_hrs=8, max_time_per_window=10)
    opt_time = time.time() - opt_start
    
    print("-" * 50)
    print(f"✅ STRESS TEST COMPLETE")
    print(f"🚀 Total Flights Optimized: {len(result)}")
    print(f"⏱️ Optimization Time: {opt_time:.2f}s")
    print(f"📉 Average Time per Window: {opt_time / (len(result)/10 or 1):.4f}s")
    print("-" * 50)
    
    # Summary Audit
    p_canceled = (result['is_canceled'].sum() / len(result)) * 100
    avg_delay = result['assigned_delay'].mean()
    print(f"📊 Cancellation Rate: %{p_canceled:.2f}")
    print(f"📊 Average Reactive Delay: {avg_delay:.2f} mins")
    print("-" * 50)

if __name__ == "__main__":
    run_performance_audit()
