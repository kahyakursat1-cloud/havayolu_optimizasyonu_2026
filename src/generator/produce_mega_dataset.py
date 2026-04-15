import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.generator.synthetic_env import AdvancedAirlineSimulator

REQUIRED_COLUMNS = [
    "flight_id",
    "origin",
    "destination",
    "departure_time",
    "arrival_time",
    "block_time",
    "aircraft_id",
    "crew_id",
    "lat",
    "lon",
]


def _default_output_path(days: int) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("data/raw") / f"aviation_scenario_{days}d_{stamp}.csv"


def produce_mega_benchmark(days: int = 15, output_path: str | Path | None = None, seed: int = 1903) -> Path:
    target_path = Path(output_path) if output_path else _default_output_path(days)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"--- Mega Dataset Uretimi Baslatildi: {days} gunluk senaryo ---")
    sim = AdvancedAirlineSimulator(seed=seed)
    df = sim.generate_full_scenario(days=days)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Eksik sutun(lar) tespit edildi: {', '.join(missing_cols)}")

    df.to_csv(target_path, index=False)
    print(f"Uretim tamamlandi. Toplam ucus: {len(df)} | Sutun: {len(df.columns)}")
    print(f"Veri seti kaydedildi: {target_path}")
    return target_path


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic aviation scenarios under data/raw.")
    parser.add_argument("--days", type=int, default=15, help="Number of simulated days.")
    parser.add_argument("--seed", type=int, default=1903, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=str, default=None, help="Optional output CSV path.")
    args = parser.parse_args()
    produce_mega_benchmark(days=args.days, output_path=args.output, seed=args.seed)


if __name__ == "__main__":
    main()
