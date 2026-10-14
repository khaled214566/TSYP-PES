# EnergyMind Tunisia — Dataset Documentation

## Overview
This dataset contains simulated 1-minute interval smart-meter and energy grid measurements generated specifically according to the challenge requirements defined in [EnergyMind_Data_Strategy.md](file:///c:/Users/khaled/Desktop/TSYP/EnergyMind_Data_Strategy.md).

---

## 1. Directory Structure

```
data/
├── raw/
│   └── baseline_30d.csv                 # 345,600 rows (8 sensors, 30 days clean baseline)
├── generated/
│   ├── full_dataset.csv                 # Master dataset with 10 anomaly types injected
│   └── labels.csv                       # Ground-truth event metadata (132 injection events)
├── processed/
│   └── features.csv                     # Feature-engineered dataset ready for ML models
├── scenarios/
│   ├── scenario_a_genuine_grid_event.csv# Demo scenario: Multi-sensor consistent voltage sag
│   ├── scenario_b_sensor_bias.csv       # Demo scenario: S-03 persistent +9.5V bias
│   └── scenario_c_falsified_data.csv    # Demo scenario: S-05 3-hour lag replay attack
├── train/
│   ├── X_train.csv                      # 241,912 training feature rows (70%)
│   └── y_train.csv                      # Target labels (is_anomaly, anomaly_type)
├── val/
│   ├── X_val.csv                        # 51,848 validation feature rows (15%)
│   └── y_val.csv                        # Target labels
└── test/
    ├── X_test.csv                       # 51,840 test feature rows (15%)
    └── y_test.csv                       # Target labels
```

---

## 2. Core Signals & Measurements

- `timestamp`: UTC/ISO timestamp sampled at 1-minute intervals.
- `sensor_id`: Identifiers from `S-01` to `S-08`.
- `voltage` (V): Nominal 230V with realistic load sag profile.
- `current` (A): Derived load current based on active power, voltage, and power factor.
- `active_power` (kW): Real power consumption reflecting morning and evening peaks.
- `power_factor`: Dimensionless (0.75 - 0.99), varying with dynamic inductive loads.
- `energy_consumption` (kWh): Incremental interval consumption calculated per minute.

---

## 3. Injected Anomaly Matrix (10 Types)

| Anomaly Type | Category | Injected Count | Description |
|---|---|---|---|
| `sensor_bias` | Data Quality | 14 | Persistent static voltage offset (±5V to ±15V). |
| `sensor_drift` | Data Quality | 12 | Gradual progressive slope drift over 1-3 hours. |
| `spike` | Data Quality | 25 | High-magnitude impulse transients (1-3 min). |
| `dropout` | Data Quality | 15 | Total connection loss / zero-collapse readings. |
| `constant_freeze` | Data Integrity | 12 | Sensor stuck repeating identical float value. |
| `replay_attack` | Falsification | 10 | Historical window replayed in place of live data. |
| `bias_injection` | Falsification | 12 | Intentional power reading reduction to cheat billing. |
| `random_corruption` | Falsification | 14 | Extreme out-of-range impossible measurements. |
| `grid_event` | Real Event | 8 | Feeder-wide multi-sensor correlated sag/surge. |
| `equipment_fault` | Real Event | 10 | Inductive breakdown with current spike & low PF. |

---

## 4. How to Reproduce or Regenerate

To regenerate this dataset with alternate seeds, sensor counts, or injection frequencies:

```powershell
# Edit parameters in simulation/config/simulation_config.yaml
python -m simulation.dataset_builder
```
