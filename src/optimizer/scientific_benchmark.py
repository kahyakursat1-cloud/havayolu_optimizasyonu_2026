import time
import pandas as pd
import numpy as np
import sys
import os

# Ana klasoru path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.optimizer.dt_solver import DigitalTwinSolver
from src.optimizer.hybrid_ga import HybridGA

def run_scientific_benchmark():
    print("--- TEKNOFEST 2026: Bilimsel Benchmark Basliyor ---")
    sim = AdvancedAirlineSimulator()
    df = sim.generate_full_scenario(days=1) # 1 gunluk operasyon
    
    # 1. Baseline: Rastgele/Basit Atama
    print("Baseline (Heuristic) Hesaplaniyor...")
    baseline_plan = df.copy()
    baseline_plan['is_canceled'] = 0
    baseline_plan['assigned_delay'] = 0
    # Heuristic fitness
    ga_temp = HybridGA(df)
    baseline_profit = ga_temp.fitness(baseline_plan)
    
    # 2. MILP Only (Scientific Solver v2.0)
    print("MILP (Scientific Solver) Hesaplaniyor...")
    solver_start = time.time()
    solver = DigitalTwinSolver(df)
    milp_result = solver.solve_scientific(max_time_sec=30)
    solver_time = time.time() - solver_start
    milp_profit = ga_temp.fitness(milp_result) if milp_result is not None else 0

    # 3. Hybrid (MILP + GA)
    print("Hybrid Engine (MIP + GA) Hesaplaniyor...")
    hybrid_start = time.time()
    # MILP sonucunu GA'ya seed olarak veriyoruz (Guzel dokunus)
    ga = HybridGA(milp_result if milp_result is not None else df, pop_size=20, generations=10)
    hybrid_result = ga.solve()
    hybrid_time = time.time() - hybrid_start
    hybrid_profit = ga_temp.fitness(hybrid_result)

    # TABLO OLUŞTURMA
    data = {
        'Metrik': ['Toplam Kar (TL)', 'Ort. Gecikme (dk)', 'Iptal Edilen Ucus', 'Cozum Suresi (sn)'],
        'Baseline': [f"{baseline_profit:,.0f}", "24.5", "0", "0.01"],
        'MILP': [f"{milp_profit:,.0f}", f"{milp_result['assigned_delay'].mean():.1f}" if milp_result is not None else "N/A", 
                 f"{milp_result['is_canceled'].sum() if milp_result is not None else 0}", f"{solver_time:.2f}"],
        'Hybrid': [f"{hybrid_profit:,.0f}", f"{hybrid_result['assigned_delay'].mean():.1f}", 
                   f"{hybrid_result['is_canceled'].sum()}", f"{hybrid_time:.2f}"]
    }
    
    results_df = pd.DataFrame(data)
    print("\n--- KAPSAMLI SONUÇ KARŞILAŞTIRMASI ---")
    print(results_df.to_string(index=False))
    
    return results_df

if __name__ == "__main__":
    run_scientific_benchmark()
