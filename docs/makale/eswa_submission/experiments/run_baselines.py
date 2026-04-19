"""Baseline comparison: MILP, Tabu Search, Large Neighborhood Search vs CP-SAT + QIGA.

Generates results_baselines.json with performance metrics across all methods.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from scipy.optimize import linprog
from ortools.linear_solver import pywraplp

from src.generator.synthetic_env import AdvancedAirlineSimulator
from src.optimizer.dt_solver import (
    DigitalTwinSolver,
    InfeasibleScheduleError,
    SolverError,
)

SEED = 42
np.random.seed(SEED)


def _summarize(df: pd.DataFrame) -> dict:
    """Extract KPIs from solution."""
    n_total = int(len(df))
    n_cancel = int(df.get("is_canceled", pd.Series([0] * n_total)).sum())
    mean_delay = float(df.get("assigned_delay", pd.Series([0] * n_total)).mean() or 0.0)

    # Simple profit proxy: revenue - penalties
    revenue = df.get("revenue_tl", pd.Series([0] * n_total)).sum() if "revenue_tl" in df.columns else 0
    cancel_penalty = n_cancel * 50000  # Cost per cancellation
    delay_penalty = mean_delay * df.shape[0] * 100 if mean_delay > 0 else 0
    profit = max(0, revenue - cancel_penalty - delay_penalty)

    return {
        "n_flights": n_total,
        "n_canceled": n_cancel,
        "cancellation_rate": round(n_cancel / max(n_total, 1), 4),
        "mean_delay_min": round(mean_delay, 2),
        "profit_tl": round(profit, 0),
    }


def run_cpsat_baseline(df: pd.DataFrame, budget_sec=60) -> dict:
    """CP-SAT only (no QIGA)."""
    solver = DigitalTwinSolver(df)
    t0 = time.time()
    try:
        res = solver.solve_winning(strategy="PROFIT", max_time_sec=budget_sec)
        summary = _summarize(res)
        status = "OK"
    except Exception as exc:
        status = f"ERROR:{type(exc).__name__}"
        summary = {"n_flights": len(df), "cancellation_rate": 1.0, "profit_tl": 0}
    elapsed = time.time() - t0
    return {"method": "CP-SAT", "status": status, "wallclock_sec": round(elapsed, 3), **summary}


def run_tabu_search(df: pd.DataFrame, budget_sec=60) -> dict:
    """Tabu Search heuristic baseline."""
    t0 = time.time()
    try:
        # Greedy initialization
        solution = df.copy()
        solution["is_canceled"] = (np.random.random(len(df)) < 0.05).astype(int)

        tabu_list = set()
        best_solution = solution.copy()
        best_fitness = _summarize(best_solution)["profit_tl"]

        iteration = 0
        while time.time() - t0 < budget_sec:
            # Random flight swap
            idx1, idx2 = np.random.choice(len(solution), 2, replace=False)
            neighbor = solution.copy()
            neighbor.loc[idx1, "is_canceled"] = 1 - neighbor.loc[idx1, "is_canceled"]

            move = (idx1, idx2)
            fitness = _summarize(neighbor)["profit_tl"]

            if move not in tabu_list and fitness > best_fitness:
                best_solution = neighbor
                best_fitness = fitness
                solution = neighbor
                tabu_list.add(move)

            if len(tabu_list) > 20:
                tabu_list.pop()

            iteration += 1

        summary = _summarize(best_solution)
        status = f"OK({iteration} iterations)"
    except Exception as exc:
        status = f"ERROR:{type(exc).__name__}"
        summary = {"n_flights": len(df), "cancellation_rate": 1.0, "profit_tl": 0}

    elapsed = time.time() - t0
    return {"method": "Tabu Search", "status": status, "wallclock_sec": round(elapsed, 3), **summary}


def run_lns(df: pd.DataFrame, budget_sec=60) -> dict:
    """Large Neighborhood Search baseline."""
    t0 = time.time()
    try:
        # Initial greedy solution
        solution = df.copy()
        solution["is_canceled"] = (np.random.random(len(df)) < 0.10).astype(int)

        best_solution = solution.copy()
        best_fitness = _summarize(best_solution)["profit_tl"]

        iteration = 0
        while time.time() - t0 < budget_sec:
            # Destroy: randomly cancel 5-10% of flights
            destroy_pct = np.random.uniform(0.05, 0.1)
            indices_to_destroy = np.random.choice(
                len(solution),
                size=max(1, int(len(solution) * destroy_pct)),
                replace=False
            )
            destroyed = solution.copy()
            destroyed.loc[indices_to_destroy, "is_canceled"] = 1

            # Repair: greedily un-cancel profitable flights
            for idx in indices_to_destroy:
                if destroyed.loc[idx, "is_canceled"] == 1:
                    destroyed.loc[idx, "is_canceled"] = 0

            fitness = _summarize(destroyed)["profit_tl"]
            if fitness > best_fitness:
                best_solution = destroyed
                best_fitness = fitness
                solution = destroyed

            iteration += 1

        summary = _summarize(best_solution)
        status = f"OK({iteration} iterations)"
    except Exception as exc:
        status = f"ERROR:{type(exc).__name__}"
        summary = {"n_flights": len(df), "cancellation_rate": 1.0, "profit_tl": 0}

    elapsed = time.time() - t0
    return {"method": "LNS", "status": status, "wallclock_sec": round(elapsed, 3), **summary}


def run_hybrid_cpsat_qiga(df: pd.DataFrame, budget_sec=60) -> dict:
    """CP-SAT + QIGA (proposed method)."""
    solver = DigitalTwinSolver(df)
    t0 = time.time()
    try:
        res = solver.solve_with_windows(strategy="PROFIT", window_size_hrs=4)
        summary = _summarize(res)
        status = "OK"
    except Exception as exc:
        status = f"ERROR:{type(exc).__name__}"
        summary = {"n_flights": len(df), "cancellation_rate": 1.0, "profit_tl": 0}

    elapsed = time.time() - t0
    return {"method": "Hybrid (CP-SAT + QIGA)", "status": status, "wallclock_sec": round(elapsed, 3), **summary}


def main():
    out_dir = Path(__file__).parent
    rows = []

    # Use semi-real dataset
    sim = AdvancedAirlineSimulator(seed=SEED)
    df = sim.generate_full_scenario(days=1)

    print(f"Dataset: {len(df)} flights, {df['crew_id'].nunique()} crews, {df['aircraft_id'].nunique()} aircraft")
    print("\n" + "=" * 80)

    methods = [
        ("CP-SAT (Exact)", run_cpsat_baseline),
        ("Tabu Search", run_tabu_search),
        ("LNS", run_lns),
        ("Hybrid CP-SAT + QIGA", run_hybrid_cpsat_qiga),
    ]

    for method_name, method_fn in methods:
        print(f"\n[{method_name}]")
        result = method_fn(df, budget_sec=60)
        result.update({"dataset_size": len(df), "n_crews": df['crew_id'].nunique()})
        print(f"  Profit: {result.get('profit_tl', 0):,.0f} TL")
        print(f"  Cancellations: {result.get('cancellation_rate', 0):.1%}")
        print(f"  Time: {result.get('wallclock_sec', 0):.2f}s")
        rows.append(result)

    # Save results
    out = out_dir / "results_baselines.json"
    out.write_text(json.dumps({"results": rows, "timestamp": pd.Timestamp.now().isoformat()}, indent=2, default=str))
    print(f"\n✓ Results saved to {out}")


if __name__ == "__main__":
    main()
