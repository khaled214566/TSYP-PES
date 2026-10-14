from __future__ import annotations
import argparse
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score
from .simulator import generate_dataset, save_dataset
from .detector import GridSentinelDetector


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a smart-metered neighborhood and run GridSentinel")
    parser.add_argument("--steps", type=int, default=1440, help="one-minute samples per meter")
    parser.add_argument("--meters", type=int, default=30, help="number of household smart meters")
    parser.add_argument("--zones", type=int, default=None, help="deprecated alias for --meters")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="data/generated")
    args = parser.parse_args()
    meters = args.zones if args.zones is not None else args.meters
    out = Path(args.out)
    train = generate_dataset(steps=args.steps, meters=meters, seed=args.seed, inject_anomalies=False)
    test = generate_dataset(steps=args.steps, meters=meters, seed=args.seed + 1, inject_anomalies=True)
    detector = GridSentinelDetector().fit(train)
    scored = detector.predict(test)
    out.mkdir(parents=True, exist_ok=True)
    save_dataset(train, str(out / "normal_training.csv"))
    save_dataset(scored, str(out / "scored_demo.csv"))
    summary = scored.groupby(["event_type", "verdict"], dropna=False).size().rename("rows").reset_index()
    summary.to_csv(out / "summary.csv", index=False)
    metrics = {
        "precision": precision_score(scored.anomaly_flag, scored.flagged, zero_division=0),
        "recall": recall_score(scored.anomaly_flag, scored.flagged, zero_division=0),
        "f1": f1_score(scored.anomaly_flag, scored.flagged, zero_division=0),
    }
    normal = scored[scored.anomaly_flag == 0]
    metrics["false_positive_rate"] = float(normal.flagged.mean()) if len(normal) else 0.0
    print(f"Neighborhood simulation: {meters} meters, {args.steps} one-minute samples per meter")
    print(f"Saved {len(train)} normal training rows and {len(scored)} scored rows to {out.resolve()}")
    print("\nGround-truth event counts:")
    print(test.groupby("event_type").size().to_string())
    print("\nVerdict counts by ground-truth event:")
    print(summary.to_string(index=False))
    print("\nPrototype row-level metrics (synthetic data only; not real-world validation):")
    for name, value in metrics.items():
        print(f"{name}={value:.3f}")

if __name__ == "__main__":
    main()
