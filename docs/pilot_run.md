# Smart-Metered Neighborhood Pilot Run

## Experiment setup

- Data source: synthetic household smart-meter measurements generated locally.
- Sampling interval: one minute.
- Neighborhood size: 10 simulated meters grouped into buildings and feeder groups.
- Window length: 360 samples per meter (six simulated hours).
- Training set: 3,600 normal-only rows, seed 42.
- Evaluation set: 3,600 rows, seed 43, with eight labelled synthetic event classes.
- Detector: Isolation Forest fitted only on normal training rows, with transparent meter-consistency and recent-consumption checks.
- Tests: `PYTHONPATH=src pytest -q` — **2 passed**.

## Row-level results

| Metric | Result |
|---|---:|
| Precision | 0.464 |
| Recall | 0.761 |
| F1 | 0.576 |
| False-positive rate on normal rows | 0.045 |

These are preliminary measurements from the current prototype and its own synthetic data. They are not validated real-world performance claims. The moderate precision/F1 and missed replay-like cases show that the baseline still needs work; do not present it as a finished detector.

## Event-level interpretation

- All injected `constant_bias`, `energy_power_mismatch`, and `missing_data` rows were flagged in this run.
- Most `false_data_injection` and `frozen_meter` rows were flagged.
- `consumption_spike` rows were generally escalated as `UNCERTAIN`, which is appropriate for a potential physical load change whose cause is unknown.
- Meter-drift detection was partial.
- Replay-like sequences were mostly missed. Detecting sequence replay requires stronger temporal/pattern logic than the current row-level baseline.
- 155 normal rows were flagged (3 as `SUSPICIOUS`, 152 as `UNCERTAIN`), corresponding to a 4.5% false-positive rate in this run.

## Reproduction

From the repository root:

```bash
PYTHONPATH=src python -m gridsentinel.cli --steps 360 --meters 10 --seed 42 --out data/generated
PYTHONPATH=src pytest -q
```

## Limitations and next experiment

All labels are injected by the same simplified simulator, so metrics only measure internal agreement with those labels. Household profiles, event amplitudes, and thresholds are illustrative. The derived feeder total is not an independent physical measurement. Next steps are scenario-held-out tests, temporal replay detection, per-meter baselines, calibration analysis, and aggregate feeder-level event scenarios.
