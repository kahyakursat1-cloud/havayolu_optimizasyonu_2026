"""Scalability experiment: single-solve CP-SAT vs rolling-horizon decomposition.

Generates synthetic schedules at 4 scales (roughly 1, 4, 8, 12 operational days
≈ 135, 540, 1080, 1620 flights) and benchmarks two solver modes:

  (i)  solve_winning           — monolithic CP-SAT solve with 60 s budget.
  (ii) solve_with_windows      — rolling horizon decomposition (4-hour windows,
                                 5 s budget each, QIGA local-search fallback).

For each (scale, mode) cell we log wall-clock time, cancellation rate, FTL
violation count, and CP-SAT exit status. Results are written to
``scalability_results.json`` in this folder and later consumed by the plotting
script ``plot_scalability.py`` and the article's Experiments section.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.generator.synthetic_env import AdvancedAirlineSimulator  # noqa: E402
from src.optimizer.dt_solver import (  # noqa: E402
    DigitalTwinSolver,
    InfeasibleScheduleError,
    MAX_CREW_DUTY_MINS,
    SolverError,
    SolverTimeoutError,
)

SCALES = [
    {"name": "1d", "days": 1, "label": "≈135 flights (1 day)"},
    {"name": "4d", "days": 4, "label": "≈540 flights (4 days)"},
    {"name": "8d", "days": 8, "label": "≈1080 flights (8 days)"},
    {"name": "12d", "days": 12, "label": "≈1620 flights (12 days)"},
]

SINGLE_BUDGET_SEC = 60
WINDOW_HOURS = 4


def _summarize(df: pd.DataFrame) -> dict:
    """Extract KPIs from an annotated solution dataframe."""
    n_total = int(len(df))
    n_cancel = int(df.get("is_canceled", pd.Series([0] * n_total)).sum())
    duty = (
        df.groupby("crew_id")["block_time"].sum()
        if "crew_id" in df.columns and "block_time" in df.columns
        else pd.Series(dtype=float)
    )
    ftl_viol = int((duty > MAX_CREW_DUTY_MINS).sum())
    mean_delay = float(df.get("assigned_delay", pd.Series([0] * n_total)).mean() or 0.0)
    return {
        "n_flights": n_total,
        "n_canceled": n_cancel,
        "cancellation_rate": round(n_cancel / max(n_total, 1), 4),
        "ftl_violations": ftl_viol,
        "mean_delay_min": round(mean_delay, 2),
    }


def _run_single(df: pd.DataFrame, num_workers=None) -> dict:
    solver = DigitalTwinSolver(df)
    t0 = time.time()
    status = "OK"
    summary: dict = {}
    try:
        res = solver.solve_winning(strategy="PROFIT", max_time_sec=SINGLE_BUDGET_SEC, num_workers=num_workers)
        summary = _summarize(res)
    except SolverTimeoutError as exc:
        status = f"TIMEOUT:{exc}"
    except InfeasibleScheduleError as exc:
        status = f"INFEASIBLE:{exc}"
    except SolverError as exc:
        status = f"SOLVER_ERROR:{type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001
        status = f"UNHANDLED:{type(exc).__name__}:{exc}"
    elapsed = time.time() - t0
    return {"mode": "single", "status": status, "wallclock_sec": round(elapsed, 3), **summary}


def _run_rolling(df: pd.DataFrame, num_workers=None) -> dict:
    solver = DigitalTwinSolver(df)
    t0 = time.time()
    status = "OK"
    summary: dict = {}
    hybrid_recoveries: list = []
    try:
        res = solver.solve_with_windows(strategy="PROFIT", window_size_hrs=WINDOW_HOURS, num_workers=num_workers)
        summary = _summarize(res)
        hybrid_recoveries = list(res.attrs.get("hybrid_recoveries", []))
    except InfeasibleScheduleError as exc:
        status = f"INFEASIBLE:{exc}"
    except SolverError as exc:
        status = f"SOLVER_ERROR:{type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001
        status = f"UNHANDLED:{type(exc).__name__}:{exc}"
    elapsed = time.time() - t0
    return {
        "mode": "rolling",
        "status": status,
        "wallclock_sec": round(elapsed, 3),
        "hybrid_fallback_count": len(hybrid_recoveries),
        **summary,
    }


def main():
    rows = []
    num_workers = 4 # Safety limit to prevent overheating
    for scale in SCALES:
        sim = AdvancedAirlineSimulator(seed=42)
        df = sim.generate_full_scenario(days=scale["days"])
        # Single Solve: Skip for 8d and 12d to prevent OOM/Overheating
        if len(df) < 1000:
            single = _run_single(df, num_workers=num_workers)
            single.update({"scale": scale["name"], "label": scale["label"], "days": scale["days"]})
            print(f"  single : {single}", flush=True)
            rows.append(single)
        else:
            print(f"  single : SKIPPED (Scale too large for Monolithic CP-SAT)", flush=True)

        # Rolling Solve: Always run as it is memory-efficient
        rolling = _run_rolling(df, num_workers=num_workers)
        rolling.update({"scale": scale["name"], "label": scale["label"], "days": scale["days"]})
        print(f"  rolling: {rolling}", flush=True)
        rows.append(rolling)
        
        # Save results incrementally
        out = Path(__file__).parent / "scalability_results.json"
        out.write_text(json.dumps({"results": rows}, indent=2))
        print(f"Incremental results saved to {out}", flush=True)
        
        print(f"Coalescing CPU for 10s after {scale['name']} scale...", flush=True)
        time.sleep(10)

    print(f"\nFinal run complete. Results at {out}", flush=True)


if __name__ == "__main__":
    main()
