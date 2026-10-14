# GridSentinel Technical Documentation

**Project:** GridSentinel — Trustworthy AI for a Smart-Metered Neighborhood  
**Challenge context:** TSYP14 EnergyMind Tunisia — *Architects of the Energy Noosphere: A Human-AI Collective Intelligence Network for Energy Resilience*  
**Document status:** Technical documentation for the current Phase 1 research prototype  
**Implementation:** Python, pandas, NumPy, scikit-learn

---

## 1. Purpose

GridSentinel is a research prototype for monitoring the quality and unusual behavior of data produced by smart meters in a simulated residential neighborhood. It combines a synthetic telemetry generator, an unsupervised anomaly-detection baseline, transparent consistency and temporal checks, and a structured output intended to support human review.

The central design principle is **detect and explain unusual evidence without claiming to know intent or root cause**. A high household load can be legitimate. A data inconsistency can arise from a sensor problem, communication problem, modeling limitation, or manipulated data. The prototype therefore flags observations for review instead of declaring a household fraudulent or taking an operational action.

## 2. Scope and boundaries

### Included

- Simulated residential smart meters reporting at one-minute intervals.
- Household, building, and feeder identifiers.
- Synthetic voltage, current, active power, power factor, frequency, and cumulative energy measurements.
- Eight labelled synthetic event scenarios.
- A model fitted on normal-only training records.
- Rule evidence, anomaly scores, conservative verdicts, and recommended review actions.
- CSV outputs and a basic automated test suite.

### Not included

- Connection to STEG, production smart meters, SCADA, or a live distribution network.
- A validated load-flow or electrical-network simulator.
- Direct control, switching, disconnection, or protection commands.
- A definitive electricity-theft or malicious-intent classifier.
- Production-grade federated learning, cryptographic identity, or privacy guarantees.
- Calibrated probabilistic confidence estimates.

The feeder aggregate in the generated data is calculated from the simulated household records. It is not an independent physical feeder-meter measurement and should not be treated as independent ground truth.

## 3. High-level architecture

```text
Synthetic household profiles
          |
          v
Smart-meter telemetry generator
  - timestamps and identifiers
  - electrical measurements
  - cumulative energy
  - labelled injected scenarios
          |
          +------------------------------+
          |                              |
          v                              v
Normal-only training data       Scenario-labelled test data
          |                              |
          v                              v
Feature engineering             Feature engineering
          |                              |
          v                              v
Isolation Forest fitting        Hybrid scoring
                                 - Isolation Forest score
                                 - missingness checks
                                 - power/energy consistency
                                 - recent-load change checks
                                 - repeated-reading checks
                                          |
                                          v
                              Structured alert record
                              - anomaly score
                              - evidence codes
                              - verdict and explanation
                              - recommended review action
                                          |
                                          v
                                CSV export / human review
```

The current implementation is an offline batch prototype. The diagram describes the current pipeline; it does not imply a deployed streaming service or multi-node network.

## 4. Neighborhood and data model

### 4.1 Simulated hierarchy

- **Meter:** an individual household's smart meter, identified as `meter_NNN`.
- **Household type:** one of `small_flat`, `family_home`, or `high_usage_home`.
- **Building:** assigned using the meter index; each group of five meters is assigned to one building.
- **Feeder:** assigned using the meter index; each group of ten meters is assigned to one feeder.
- **Timestamp:** UTC timestamps beginning at `2026-01-01T00:00:00Z`, spaced one minute apart.

These grouping rules are organizational abstractions for experiments, not a geographic or electrical topology model.

### 4.2 Input and ground-truth fields

| Field | Meaning | Notes |
|---|---|---|
| `timestamp` | Time of the sample | UTC, one-minute interval |
| `meter_id` | Unique simulated meter | Main temporal grouping key |
| `household_type` | Synthetic household profile | Illustrative categories, not learned from real households |
| `building_id` | Simulated building group | Five-meter grouping convention |
| `feeder_id` | Simulated feeder group | Ten-meter grouping convention |
| `voltage_v` | Voltage in volts | Simplified nominal value near 230 V |
| `current_a` | Current in amperes | Derived from active power, voltage, and power factor in baseline data |
| `active_power_kw` | Active power in kW | Synthetic household load |
| `power_factor` | Power factor | Synthetic value close to 0.96 in baseline data |
| `frequency_hz` | Frequency in Hz | Synthetic value close to 50 Hz |
| `energy_kwh` | Cumulative energy in kWh | Baseline increment approximates power divided by 60 each minute |
| `event_type` | Scenario label | `normal` or one of the injected scenario names |
| `anomaly_flag` | Ground-truth row label | 0 for baseline rows, 1 for injected scenario rows |
| `affected_channel` | Channel(s) modified by injection | Descriptive label, not a detector prediction |
| `event_id` | Injected event reference | Empty for normal rows |
| `neighborhood_feeder_power_kw` | Derived feeder aggregate | Sum of simulated active power by timestamp and feeder; not independent measurement |
| `active_meter_count` | Number of distinct meter IDs in aggregate | Derived from simulated records |

### 4.3 Simplified electrical relationships

The baseline uses the single-phase approximation:

\[
P_{kW} \approx \frac{V I PF}{1000}
\]

where voltage is in volts, current in amperes, and power factor is dimensionless. This relationship is used for synthetic consistency, not as a validated model of all household loads or meter measurement behavior.

The baseline cumulative energy update is approximately:

\[
\Delta E_{kWh} \approx \frac{P_{kW}}{60}
\]

for a one-minute interval. Synthetic injections may deliberately break this relationship to create test cases.

## 5. Scenario catalogue

| Scenario | Simulation behavior | Intended test question |
|---|---|---|
| `consumption_spike` | Increases active power and corresponding current, and adjusts cumulative energy for the extra consumption | Can the system identify a sharp but potentially legitimate demand change without assuming malicious intent? |
| `meter_drift` | Adds a gradual offset to reported active power without matching changes to current and energy | Can gradual measurement inconsistency be detected? |
| `constant_bias` | Adds a persistent offset to active power | Can a biased measurement channel be flagged? |
| `false_data_injection` | Multiplies reported active power while leaving companion current unchanged | Can cross-channel inconsistency reveal altered telemetry? |
| `replay_like` | Repeats a previous sequence of measurement values in a later window | Can temporal repetition or replay-like behavior be recognized? |
| `frozen_meter` | Holds all measurement channels constant for an event window | Can repeated readings reveal a possibly frozen meter? |
| `missing_data` | Replaces active-power values with missing values | Can unavailable measurements be detected and escalated? |
| `energy_power_mismatch` | Adds an inconsistent offset to cumulative energy | Can the energy increment be checked against reported power? |

All scenario labels are generated by the simulator. They are experimental labels, not evidence that the same pattern in real data has a particular cause. In particular, the `replay_like` scenario is only a simplified replay pattern and the current detector has known weaknesses on this scenario.

## 6. Detection pipeline

### 6.1 Feature engineering

`add_features()` derives temporal and consistency features per meter:

- `power_consistency_residual`: reported active power minus the value implied by voltage, current, and power factor.
- `missing_measurement`: indicator that one or more required measurement fields are missing.
- `power_delta`: change in active power from the preceding row for the same meter.
- `relative_power_change`: absolute power change relative to the preceding power, with a small denominator floor.
- `power_vs_recent_baseline`: current active power divided by a rolling median of previous readings, using up to 30 samples and requiring at least five earlier observations.
- `voltage_delta`: change in voltage from the preceding row.
- `energy_step_kwh`: cumulative-energy difference from the preceding row.
- `energy_expected_kwh`: active power divided by 60, reflecting a one-minute interval.
- `energy_consistency_residual`: observed energy increment minus expected increment.
- `repeated_reading_run`: count of consecutive rows with identical values across the listed measurement channels.

Rows must be grouped and ordered by meter and timestamp before production-quality temporal evaluation. The simulator currently returns records sorted by meter and timestamp.

### 6.2 Machine-learning baseline

The model is a scikit-learn pipeline:

1. Median imputation of missing feature values.
2. Standardization of features.
3. Isolation Forest with 160 trees, a default contamination parameter of 0.03, and fixed random state 42.

The detector is fitted only on normal-only synthetic rows. A score threshold is derived from the fitted training decision scores using the configured contamination quantile. A row is considered a model anomaly when its decision score is below this threshold.

### 6.3 Transparent checks

The current rule layer records evidence when any of the following occurs:

- one or more required measurement fields are missing;
- voltage falls outside the illustrative range 207–253 V;
- frequency falls outside the illustrative range 49.5–50.5 Hz;
- the power-consistency residual exceeds 0.25 kW in absolute value;
- the energy-consistency residual exceeds 0.08 kWh in absolute value;
- absolute power change exceeds 1.5 kW, relative change exceeds 1.0, or power is outside 0.35–1.8 times its recent baseline;
- five or more consecutive identical measurement rows are observed.

These values are prototype thresholds. They are not represented as official Tunisian operating limits or validated meter tolerances; they must be justified and tested before any operational use.

### 6.4 Flag and verdict logic

A row is flagged when the model marks it anomalous **or** at least one rule produces evidence. The first matching condition below determines the current verdict and recommended action:

| Condition | Verdict | Current interpretation | Recommended action |
|---|---|---|---|
| Missing measurement | `SUSPICIOUS` | Meter data unavailable | Review the event and check communications |
| Power or energy consistency failure | `SUSPICIOUS` | Measurement inconsistency; cause unconfirmed | Retain sample and check meter-data quality |
| Repeated readings | `SUSPICIOUS` | Possible frozen or replayed readings | Review event and check meter health |
| Unusual recent consumption change | `UNCERTAIN` | Physical cause unknown | Compare with household baseline and review |
| Model-only anomaly or other flagged evidence | `UNCERTAIN` | Statistical anomaly; cause unconfirmed | Request operator review |
| No model or rule flag | `TRUSTED` | No anomaly detected by current checks | Continue monitoring |

`COMPROMISED` is not assigned automatically by the current detector. A `TRUSTED` result means only that these current checks did not flag the row; it is not a guarantee that the data is correct.

### 6.5 Score and confidence semantics

- `anomaly_score` is a transformed, relative score derived from the model's decision function and training threshold.
- `ml_anomaly` indicates the model-only decision.
- `flagged` combines the model decision and rule evidence.
- `confidence` is a heuristic value derived from the anomaly score's distance from 0.5.
- `confidence_note` explicitly states that this is not a calibrated probability.

The score should not be interpreted as the probability that a meter is compromised, a household is committing fraud, or an alert is correct. Calibration and user studies are future work.

## 7. Command-line workflow

### 7.1 Environment setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 7.2 Run the prototype

From the repository root:

```bash
# macOS/Linux
PYTHONPATH=src python -m gridsentinel.cli --steps 360 --meters 10 --seed 42 --out data/generated

# Windows PowerShell
$env:PYTHONPATH = "src"
python -m gridsentinel.cli --steps 360 --meters 10 --seed 42 --out data/generated
```

Arguments:

- `--steps`: number of one-minute samples generated per meter; minimum 120.
- `--meters`: number of household smart meters; default 30.
- `--seed`: random seed for reproducibility; default 42.
- `--out`: output directory; default `data/generated`.
- `--zones`: deprecated compatibility alias for `--meters`.

The CLI creates a normal-only training dataset using the supplied seed and a separate test dataset using `seed + 1` with injected anomalies. It fits the model, scores the test data, writes CSV outputs, and prints row-level metrics.

### 7.3 Outputs

- `normal_training.csv`: normal-only training rows.
- `scored_demo.csv`: test rows plus detector features/results.
- `summary.csv`: row counts grouped by ground-truth event type and verdict.

The summary is a count table; it is not a substitute for per-scenario precision/recall or event-level metrics.

### 7.4 Tests

```bash
PYTHONPATH=src pytest -q
```

The current tests check reproducibility, expected neighborhood identifiers and fields, scenario coverage, and required detector outputs. They are smoke tests, not a comprehensive correctness or security test suite.

## 8. Current pilot experiment

The documented pilot uses 10 simulated meters, 360 one-minute samples per meter, 3,600 normal-only training rows, and 3,600 evaluation rows with eight injected event classes. The training seed is 42 and the evaluation seed is 43.

| Metric | Pilot result |
|---|---:|
| Precision | 0.464 |
| Recall | 0.761 |
| F1 | 0.576 |
| False-positive rate on normal rows | 0.045 |

These figures are reproducible only for the documented code and settings. They measure row-level agreement with labels injected by the same simplified simulator. They are not evidence of performance on real smart meters or real neighborhoods. The current pilot notes report that replay-like events are mostly missed and that drift detection is partial. Improving these cases is a priority before using performance claims in a pitch.

## 9. Test and evaluation recommendations

The next evaluation iteration should:

1. Report precision, recall, F1, and false-positive rate separately for every scenario.
2. Split by complete event windows or scenario variants so closely related samples do not leak between training and evaluation.
3. Compare the hybrid detector with simple baselines such as rolling-median deviation and fixed consistency rules.
4. Evaluate multiple random seeds, household profiles, event magnitudes, event durations, and noise levels.
5. Measure detection delay and event-level detection, not only row-level classification.
6. Test replay-like behavior with explicit temporal sequence fingerprints or similarity features.
7. Add aggregate feeder-demand events and distinguish them from individual-meter anomalies.
8. Assess whether explanations are understandable and whether the recommended action is appropriate to each evidence type.
9. Calibrate confidence only against a representative labelled validation set; otherwise retain the current heuristic disclaimer.

## 10. Collective intelligence and privacy roadmap

Collective intelligence is a design direction, not an implemented feature in this code version. A future neighborhood node may share a compact, versioned event summary containing:

- event reference and coarse timestamp bucket;
- abstracted event category and feature ranges;
- detector/model version;
- validation status and provenance;
- optional reviewer disposition.

Raw household-level time series should remain local by default. Receiving nodes should validate message schemas, versions, provenance, and consistency. This approach can reduce unnecessary data exchange, but it does not automatically guarantee anonymity or formal privacy. Future work must test re-identification risk, malicious or poisoned summaries, access control, retention, and audit integrity.

## 11. Safety, governance, and operational posture

- Treat detections as review prompts, not accusations.
- Keep the reason for each alert visible through evidence codes and a plain-language interpretation.
- Preserve the distinction between physical demand changes and measurement-quality issues.
- Require a human reviewer before any consequential decision.
- Record reviewer decision, timestamp, model version, evidence, and override reason in a future audit workflow.
- Do not connect the prototype to real meters or control systems without appropriate authorization, engineering validation, cybersecurity review, and operational safeguards.

## 12. Known limitations

1. Synthetic profiles are simplified and may not represent Tunisian household demand, weather, occupancy, appliances, tariffs, or meter behavior.
2. The simulator does not model a real feeder's impedance, voltage drops, phase imbalance, topology, or physical constraints.
3. The feeder aggregate is derived from the same simulated household records, so it is not independent corroboration.
4. Several rule thresholds are illustrative and may generate false alarms or miss relevant events.
5. The detector's row-level temporal features depend on correctly ordered per-meter records.
6. Isolation Forest can learn artifacts specific to this simulator.
7. The current detector is weak on replay-like events and only partially detects gradual drift in the pilot.
8. Confidence is not calibrated; verdicts are not probabilities.
9. No production audit store, API, dashboard, federated training, or secure inter-node exchange is implemented in this prototype.
10. No real-world performance, privacy, or cybersecurity claim has been validated.

## 13. Suggested Phase 2 milestones

- **M1 — Evaluation:** scenario-held-out testing, per-scenario metrics, multi-seed analysis, and baseline comparisons.
- **M2 — Neighborhood context:** feeder-level peak and aggregate anomaly features, with careful treatment of missing readings.
- **M3 — Temporal integrity:** improve frozen-meter and replay-like detection; quantify detection delay.
- **M4 — Explainability and review:** human-readable alerts, reviewer outcomes, and an append-only audit record.
- **M5 — Collective intelligence:** exchange schema-versioned summaries between simulated nodes; test validation and poisoning defenses.
- **M6 — Demonstration:** a reproducible walkthrough with normal behavior, a physical load spike, a meter-quality issue, and a reviewer decision.

## 14. Module reference

| Path | Responsibility |
|---|---|
| `src/gridsentinel/simulator.py` | Generate baseline household telemetry, inject labelled scenarios, derive feeder aggregates, save CSV files |
| `src/gridsentinel/detector.py` | Engineer features, fit the Isolation Forest pipeline, apply transparent checks, emit verdicts and evidence |
| `src/gridsentinel/cli.py` | Run training/evaluation, export CSV files, print summary counts and aggregate metrics |
| `tests/test_prototype.py` | Smoke tests for reproducibility, schema, scenario coverage, and detector output fields |
| `docs/phase1_proposal.md` | Phase 1 proposal and challenge alignment |
| `docs/pilot_run.md` | Reproduction settings, pilot metrics, and interpretation |

---

**Document-control note:** Update the pilot metrics, threshold descriptions, and implemented-feature statements whenever the simulator or detector changes. Clearly label all synthetic results and avoid presenting planned collective-intelligence features as already implemented.
