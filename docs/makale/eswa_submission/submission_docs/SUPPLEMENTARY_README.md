# Supplementary Materials — ESWA Submission

**Manuscript:** Hybrid CP-SAT and Quantum-Inspired Optimization for Airline Disruption Recovery with Explainable Decision Support
**Target journal:** Expert Systems with Applications (Elsevier)

This package accompanies the manuscript and is intended to satisfy the journal's data and code availability policy.

## Contents

```
eswa_submission/
├── main.tex                          — LaTeX source of the manuscript
├── main.pdf                          — Compiled manuscript (37 pages)
├── figures/                          — All figures referenced from main.tex
│   ├── fig1_hybrid_architecture.png  — Two-stage architecture
│   ├── fig2_qiga_workflow.png        — QIGA workflow with warm-start
│   ├── fig3_convergence_chart.png    — CP-SAT convergence
│   ├── fig4_shap_importance.png      — SHAP feature importance
│   ├── fig5_performance_comparison.png
│   ├── fig6_cancellation_scenarios.png
│   ├── fig7_scalability.png          — Monolithic vs Rolling Horizon
│   ├── fig8_ftl_sensitivity.png      — FTL ceiling sensitivity
│   └── fig9_convergence_ablation.png — 20-run convergence ablation
├── experiments/                      — Reproduction scripts and data
│   ├── run_baselines.py              — Baseline-150 comparison runner
│   ├── run_qiga_ablation.py          — QIGA vs classical GA ablation
│   ├── run_ftl_sensitivity.py        — FTL threshold sweep
│   ├── run_scalability.py            — Multi-day scalability sweep
│   ├── run_all_methods_realdata.py   — RealCal-300 LNS/Tabu/CP-SAT/QIGA
│   ├── run_xai_quantitative.py       — SHAP fidelity/stability/robustness
│   ├── case_study_nov2023.py         — November 2023 TK reconstruction
│   ├── plot_scalability.py           — Scalability figure generator
│   ├── plot_sensitivity_convergence.py
│   ├── results_baselines.json        — Cached Baseline-150 results
│   ├── comprehensive_results_realdata.json — Cached RealCal-300 results
│   ├── ftl_sensitivity.json          — Cached FTL sweep results
│   ├── qiga_ablation_results.json
│   ├── scalability_results.json
│   ├── xai_metrics.json
│   ├── real_validation_results.json
│   ├── case_study_nov2023_results.json
│   ├── real_calibrated_tk_1day_300flights.csv — IATA-calibrated dataset
│   ├── real_calibrated_tk_7day_2100flights.csv
│   └── real_calibrated_metadata.json
└── submission_docs/
    ├── cover_letter.pdf
    ├── highlights.txt
    ├── conflict_of_interest.txt
    ├── credit_statement.txt
    └── SUPPLEMENTARY_README.md       — This file
```

## How to reproduce the numerical results

### Environment

- Python ≥ 3.9
- `ortools ≥ 9.11` (Google OR-Tools, CP-SAT solver)
- `numpy`, `pandas`, `xgboost`, `shap`, `matplotlib`, `seaborn`
- Hardware reference: Intel i7-12700 @ 4.9 GHz, 32 GB DDR5 RAM (RAM is binding for the Scale-8d and Scale-12d monolithic CP-SAT runs).

### Per-table reproduction

| Manuscript table              | Script                          | Output JSON                              |
|-------------------------------|---------------------------------|------------------------------------------|
| Tab 4 (Baseline-150)          | `run_baselines.py`              | `results_baselines.json`                 |
| Tab 6 (RealCal-300)           | `run_all_methods_realdata.py`   | `comprehensive_results_realdata.json`    |
| Tab 9 (Worst-case stress)     | `run_baselines.py --stress`     | embedded in `results_baselines.json`     |
| Tab 10 (Stochastic-50/100)    | `run_baselines.py --stochastic` | embedded                                 |
| Tab 11 (SysVal-140)           | `run_baselines.py --sysval`     | `real_validation_results.json`           |
| Tab 12 (Scale-1/4/8/12d)      | `run_scalability.py`            | `scalability_results.json`               |
| Tab 16 (XAI metrics)          | `run_xai_quantitative.py`       | `xai_metrics.json`                       |
| Tab 18 (FTL sensitivity)      | `run_ftl_sensitivity.py`        | `ftl_sensitivity.json`                   |
| Case Study (Sec. 7)           | `case_study_nov2023.py`         | `case_study_nov2023_results.json`        |

### Figure reproduction

| Figure  | Script                                   |
|---------|------------------------------------------|
| Fig 3   | embedded in `run_baselines.py`           |
| Fig 4   | embedded in `run_xai_quantitative.py`    |
| Fig 5   | `plot_sensitivity_convergence.py`        |
| Fig 6   | `plot_sensitivity_convergence.py`        |
| Fig 7   | `plot_scalability.py`                    |
| Fig 8   | `plot_sensitivity_convergence.py`        |
| Fig 9   | `plot_sensitivity_convergence.py`        |

## Data provenance and anonymisation

- **Synthetic datasets** (`real_calibrated_tk_*.csv`) are generated from publicly available Turkish Airlines route network data and IATA 2024 statistics; no proprietary airline data is included.
- **Author identifiers** in script headers and metadata files have been replaced with placeholders for the submission review process. Upon acceptance, the corresponding GitHub repository will be made public and the anonymisation reverted.
- **Real Turkish Airlines historical flight records** are subject to non-disclosure agreements and are not included; the calibration methodology described in Section 6.2 of the manuscript is fully transparent and can be applied by any researcher with comparable proprietary data.

## License (upon publication)

The code in `experiments/` will be released under the MIT licence. The synthetic datasets in `experiments/*.csv` will be released under CC BY 4.0. Upon acceptance, a permanent DOI snapshot will be created at Zenodo and linked from the published article.

## Contact

Please direct correspondence to the corresponding author (see manuscript). For pre-acceptance review queries, contact via the journal's editorial system.
