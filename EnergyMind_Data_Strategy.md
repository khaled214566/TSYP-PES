# EnergyMind Tunisia — Data Strategy & Structure

*Decided: October 2026*

---

## 1. Data Source Strategy

**Fully Synthetic.**
All data is generated from scratch by a purpose-built simulator.
No external dataset download is required. This is acceptable for the competition because the challenge explicitly permits synthetic faults, sensor drift, biased readings, and falsified readings.

---

## 2. Signal Types

The simulator generates **5 signal types** per sensor per timestamp:

| Signal | Unit | Notes |
|---|---|---|
| `voltage` | V | Primary grid measurement |
| `current` | A | Derived from power & voltage |
| `active_power` | kW | Real power consumption |
| `power_factor` | — | Range 0–1 |
| `energy_consumption` | kWh | Interval-accumulated smart meter reading |

---

## 3. Simulation Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Sampling interval | **1 minute** | Realistic smart meter interval; manageable dataset size |
| Number of sensors | **5–10** | Enough to demonstrate cross-sensor consistency checks |
| Time span | **30 days** | Captures daily + weekly patterns; provides enough anomaly windows |
| Total rows (approx.) | ~432 000 – 864 000 | 10 sensors × 43 200 min/month |

---

## 4. Anomaly Types

The injector supports **all 10 anomaly types**, each mapping to a challenge requirement:

| # | Anomaly Type | Category | Challenge Pillar |
|---|---|---|---|
| 1 | Sensor bias (persistent offset) | Data quality | Pillar 1 |
| 2 | Sensor drift (gradual change) | Data quality | Pillar 1 |
| 3 | Spike / impulse noise | Data quality | Pillar 1 |
| 4 | Dropout / missing data | Data quality | Pillar 1 |
| 5 | Constant-value freeze (stuck sensor) | Data integrity | Pillar 1 |
| 6 | Replay attack (repeated old values) | Falsification | Pillar 1 |
| 7 | Bias injection (falsified offset) | Falsification | Pillar 1 |
| 8 | Random corruption | Falsification | Pillar 1 |
| 9 | Genuine grid event (multi-sensor surge/dip) | Real event | Pillar 1 + 2 |
| 10 | Equipment fault (abnormal operating pattern) | Real event | Pillar 1 + 2 |

Every injected anomaly must be recorded with full metadata (see Section 6).

---

## 5. Folder Structure

```
data/
│
├── raw/                    # Pure clean baseline (no anomalies)
│   └── baseline_30d.csv
│
├── generated/              # Output of anomaly injector
│   ├── full_dataset.csv          # Master: all sensors, all time, all signals
│   └── labels.csv                # Anomaly metadata / ground-truth labels
│
├── processed/              # After feature engineering & normalization
│   └── features.csv
│
├── train/
│   ├── X_train.csv
│   └── y_train.csv
│
├── val/
│   ├── X_val.csv
│   └── y_val.csv
│
└── test/
    ├── X_test.csv
    └── y_test.csv
```

---

## 6. File Schemas

### 6.1 `generated/full_dataset.csv` — Master readings file

| Column | Type | Description |
|---|---|---|
| `timestamp` | datetime | ISO 8601, minute-resolution |
| `sensor_id` | string | e.g. `S-01` … `S-10` |
| `voltage` | float | Volts |
| `current` | float | Amperes |
| `active_power` | float | kW |
| `power_factor` | float | 0–1 |
| `energy_consumption` | float | kWh |
| `is_anomaly` | bool | Whether this row has an injected anomaly |
| `anomaly_type` | string | One of the 10 types, or `null` |

### 6.2 `generated/labels.csv` — Anomaly event metadata

| Column | Type | Description |
|---|---|---|
| `anomaly_id` | string | Unique ID per injection event |
| `anomaly_type` | string | e.g. `sensor_bias`, `replay_attack` |
| `sensor_id` | string | Affected sensor(s) |
| `start_time` | datetime | Injection start |
| `end_time` | datetime | Injection end |
| `severity` | float | 0–1 scale |
| `affected_signals` | list[str] | Which signals were modified |
| `injection_parameters` | JSON | Type-specific params (e.g. offset=+8V, duration=12min) |
| `category` | string | `data_quality` / `falsification` / `real_event` |

---

## 7. Train / Val / Test Split

**70 % train / 15 % val / 15 % test — stratified by anomaly type.**

- Stratification ensures every anomaly type appears in all three splits.
- Split is done **chronologically** within each anomaly class to avoid data leakage.
- The held-out test set is never touched during model development.

---

## 8. Simulator Implementation

**Python module / class, configurable via YAML.**

```
simulation/
│
├── config/
│   └── simulation_config.yaml     # All parameters in one place
│
├── generators/
│   ├── baseline_generator.py      # Clean signal with daily/weekly patterns + noise
│   └── anomaly_injector.py        # Injects any of the 10 anomaly types
│
├── scenarios/
│   ├── scenario_a_grid_event.py   # Genuine multi-sensor grid event
│   ├── scenario_b_sensor_bias.py  # Single-sensor persistent bias
│   └── scenario_c_falsified.py    # Temporal/cross-sensor consistency violation
│
├── dataset_builder.py             # Orchestrates generation → injection → split → save
└── README.md
```

### `simulation_config.yaml` skeleton

```yaml
simulation:
  num_sensors: 8
  sampling_interval_minutes: 1
  duration_days: 30
  seed: 42

signals:
  voltage:
    nominal: 230        # V
    noise_std: 1.5
  current:
    nominal: 15         # A
    noise_std: 0.5
  active_power:
    nominal: 3.5        # kW
    noise_std: 0.2
  power_factor:
    nominal: 0.92
    noise_std: 0.01
  energy_consumption:
    interval_kwh: 0.058 # kWh per minute

anomaly_injection:
  target_anomaly_ratio: 0.10    # 10% of timestamps contain an anomaly
  types:
    sensor_bias:       { enabled: true, offset_range: [5, 15], duration_min: [5, 30] }
    sensor_drift:      { enabled: true, rate_per_min: [0.01, 0.05], duration_min: [30, 120] }
    spike:             { enabled: true, magnitude_range: [3, 10] }
    dropout:           { enabled: true, duration_min: [1, 20] }
    constant_freeze:   { enabled: true, duration_min: [5, 60] }
    replay_attack:     { enabled: true, replay_window_min: [10, 60] }
    bias_injection:    { enabled: true, offset_range: [8, 20], duration_min: [10, 45] }
    random_corruption: { enabled: true, corruption_prob: 0.02 }
    grid_event:        { enabled: true, affected_sensors: all, magnitude: [0.05, 0.2] }
    equipment_fault:   { enabled: true, fault_types: [overload, harmonic, intermittent] }

split:
  train: 0.70
  val:   0.15
  test:  0.15
  stratify_by: anomaly_type
```

---

## 9. Demonstration Scenarios

Three pre-built scenarios that feed directly into the judging demo:

| Scenario | What the simulator does | Expected system output |
|---|---|---|
| **A — Genuine grid event** | Injects a simultaneous surge across all sensors | Real event · High confidence · Appropriate auto-response |
| **B — Sensor bias** | Injects a persistent +8 V offset on one sensor only | Data-quality problem · Inspect sensor recommendation |
| **C — Falsified data** | Injects a replay attack violating temporal consistency | Data integrity warning · Human review required |

---

## 10. Dataset Metadata Document

A `data/README.md` must document:

- Generation date & seed
- Number of sensors, signals, timestamps
- Sampling interval
- Anomaly injection rationale
- Anomaly type distribution (count per type)
- Train / val / test row counts
- Column descriptions for every file

---

*EnergyMind Tunisia — Data Strategy v0.1 — October 2026*
