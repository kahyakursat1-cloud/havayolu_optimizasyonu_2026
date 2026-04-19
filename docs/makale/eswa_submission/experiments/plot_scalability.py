"""Render the scalability comparison figure for the ESWA article.

Reads ``scalability_results.json`` and produces ``figures/fig5_scalability.png``
with three panels: (a) wall-clock time vs. fleet size, (b) cancellation rate,
(c) FTL violation count. Each panel has two series — monolithic CP-SAT vs
rolling-horizon decomposition — making the scalability argument visible at a
glance.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sns.set_theme(style="whitegrid", font_scale=1.05)
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

HERE = Path(__file__).parent
DATA = HERE / "scalability_results.json"
FIG_DIR = HERE.parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUT = FIG_DIR / "fig7_scalability.png"


def _extract(rows, mode, field):
    return [r.get(field) for r in rows if r["mode"] == mode]


def main():
    payload = json.loads(DATA.read_text())
    rows = payload["results"]
    scales = sorted({r["scale"] for r in rows}, key=lambda s: int(s.rstrip("d")))

    def ordered(mode, field):
        by_scale = {r["scale"]: r.get(field) for r in rows if r["mode"] == mode}
        return [by_scale.get(s) for s in scales]

    sizes = ordered("single", "n_flights")
    if any(s is None for s in sizes):
        sizes = ordered("rolling", "n_flights")
    labels = [f"{s}\n({n or '—'} fl.)" for s, n in zip(scales, sizes)]

    t_single = ordered("single", "wallclock_sec")
    t_roll = ordered("rolling", "wallclock_sec")
    c_single = ordered("single", "cancellation_rate")
    c_roll = ordered("rolling", "cancellation_rate")
    v_single = ordered("single", "ftl_violations")
    v_roll = ordered("rolling", "ftl_violations")

    def clean(series):
        return [v if v is not None else np.nan for v in series]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    x = np.arange(len(scales))
    w = 0.38

    ax = axes[0]
    ax.bar(x - w / 2, clean(t_single), w, label="Monolithic CP-SAT", color="#60A5FA", edgecolor="white")
    ax.bar(x + w / 2, clean(t_roll), w, label="Rolling horizon (4 h)", color="#10B981", edgecolor="white")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Wall-clock time (s)")
    ax.set_title("(a) Solver runtime", fontweight="bold", fontsize=11)
    ax.legend(fontsize=9, loc="upper left")

    ax = axes[1]
    ax.bar(x - w / 2, clean(c_single), w, color="#60A5FA", edgecolor="white", label="Monolithic")
    ax.bar(x + w / 2, clean(c_roll), w, color="#10B981", edgecolor="white", label="Rolling")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Cancellation rate")
    ax.set_title("(b) Solution quality", fontweight="bold", fontsize=11)
    ax.legend(fontsize=9, loc="upper left")

    ax = axes[2]
    ax.bar(x - w / 2, clean(v_single), w, color="#60A5FA", edgecolor="white", label="Monolithic")
    ax.bar(x + w / 2, clean(v_roll), w, color="#10B981", edgecolor="white", label="Rolling")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("EASA FTL violations (#)")
    ax.set_title("(c) Constraint feasibility", fontweight="bold", fontsize=11)
    ax.legend(fontsize=9, loc="upper left")

    sns.despine()
    fig.tight_layout()
    fig.savefig(OUT, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
