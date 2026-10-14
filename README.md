# GridSentinel — Smart-Metered Neighborhood Prototype

GridSentinel is a research prototype for a **simulated smart-metered residential neighborhood**. It generates household-level measurements, injects labelled consumption and meter-data anomalies, applies an Isolation Forest baseline plus transparent checks, and emits evidence, a conservative trust verdict, and a recommended review action.

> **Scope and safety:** this is not connected to STEG or real smart meters. It is not a validated power-flow simulator, protection relay, SCADA controller, or fraud detector. An unusual consumption pattern is not proof of theft or malicious behavior. The current confidence field is a heuristic indicator, not a calibrated probability. No real control commands are issued.

## Documentation

- [`docs/technical_documentation.md`](docs/technical_documentation.md) — architecture, data dictionary, scenarios, detection logic, commands, pilot results, limitations, and roadmap.
- [`docs/phase1_proposal.md`](docs/phase1_proposal.md) — Phase 1 proposal.
- [`docs/pilot_run.md`](docs/pilot_run.md) — documented pilot experiment.

## Challenge alignment

The prototype is designed around the TSYP14 EnergyMind Tunisia challenge themes:
1. Anomaly and bias detection.
2. Confidence indicators, plain-language explanations, and auditable decisions.
3. Human–AI escalation and governance.
4. Shared learning across nodes with privacy considerations.

## Quick start

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Run the smart-metered neighborhood simulation:

```bash
# macOS/Linux
PYTHONPATH=src python -m gridsentinel.cli --steps 1440 --meters 30 --seed 42

# Windows PowerShell
$env:PYTHONPATH = "src"
python -m gridsentinel.cli --steps 1440 --meters 30 --seed 42

pytest -q
```

`--steps` is the number of one-minute samples per meter; `--meters` is the number of simulated household meters. The legacy `--zones` argument remains as an alias for `--meters` only for compatibility with earlier commands.

Outputs are written to `data/generated/`:
- `normal_training.csv` — normal-only household meter records.
- `scored_demo.csv` — test records with anomaly score, verdict, evidence, and recommended action.
- `summary.csv` — ground-truth scenario counts by verdict.

## Data model

Each row includes timestamp, meter/household/building/feeder identifiers, voltage, current, active power, power factor, frequency, cumulative energy, scenario label, and simulated feeder aggregate. The feeder aggregate is computed from household records and is not an independent physical measurement.

## Simulated scenarios

`consumption_spike`, `meter_drift`, `constant_bias`, `false_data_injection`, `replay_like`, `frozen_meter`, `missing_data`, and `energy_power_mismatch`.

## Current limitations

- Household demand profiles and anomalies are synthetic.
- The detector is a baseline and thresholds are illustrative.
- Scores measured on this simulator do not establish real-world performance.
- The model can identify unusual data, but it cannot infer root cause or intent by itself.
- Privacy-aware collective sharing is documented as a design; production-grade federation is not implemented yet.

## Repository layout

```text
src/gridsentinel/simulator.py  # household smart-meter simulation + labelled scenarios
src/gridsentinel/detector.py   # Isolation Forest + interpretable meter checks
src/gridsentinel/cli.py        # reproducible CLI run and metrics
 tests/test_prototype.py       # baseline smoke tests
docs/phase1_proposal.md        # revised Phase 1 proposal
docs/pilot_run.md              # pilot run notes and caveats
```
