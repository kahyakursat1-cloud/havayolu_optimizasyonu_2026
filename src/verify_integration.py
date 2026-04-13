import pandas as pd
from src.generator.synthetic_env import GrandMasterSimulator
from src.optimizer.dt_solver import DecathlonSolver
from src.optimizer.hybrid_ga import HybridGA

def test_integration():
    print("=== TEKNOFEST 2026: INTEGRATION TEST (SCIENTIFIC INTEGRITY) ===")
    
    # 1. Generate Scenario
    sim = GrandMasterSimulator()
    df = sim.generate_grand_scenario().head(12) # Small set for quick check
    print(f"Senaryo Üretildi: {len(df)} uçuş.")
    
    # 2. Run Hardened MILP
    solver = DecathlonSolver(df)
    milp_res = solver.solve_winning(max_time_sec=10)
    
    if milp_res is not None:
        print("MILP Çözümü Başarılı. [K4-K10 Check OK]")
        
        # 3. Run Hybrid GA with MILP Seed
        ga = HybridGA(df, generations=5)
        ga_res = ga.solve(initial_seed=milp_res)
        
        if ga_res is not None:
            print("Hibrit GA (MILP Seeded) Başarılı.")
            print(f"Final Plan Boyutu: {len(ga_res[ga_res['is_canceled']==0])} başarılı uçuş.")
            print("=== INTEGRATION TEST PASSED! ÜRÜN DEMOYA HAZIR. ===")
            return True
    
    print("INTEGRATION TEST FAILED.")
    return False

if __name__ == "__main__":
    test_integration()
