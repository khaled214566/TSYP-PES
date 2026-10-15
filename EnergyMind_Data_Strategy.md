# EnergyMind Tunisia — Data Strategy & Simulation Architecture (v2.0)

> **IEEE TSYP 14 (PES & IES Chapters) — Data Exploration & Generation Specification**  
> **Status:** Rectified to align with `src/gridsentinel/simulator.py` and Execution Plan v2.0

---

## 1. Data Source Strategy: Fully Grounded Synthetic Power Grid Simulation

To satisfy the competition's requirement for reproducible ground truth across all anomaly types, EnergyMind utilizes a purpose-built physics-informed simulation engine (`src/gridsentinel/simulator.py`).

### Key Simulation Principles
- **No external black-box download required:** Eliminates missing labels and non-standardized schemas.
- **Physics-Informed Grounding:** Incorporates real electrical distribution line physics:
  $$\Delta V = R_{\text{cable}} \cdot d \cdot I$$
  where $R_{\text{cable}} = 0.0004\,\Omega/\text{m}$ and household distances range from $50\text{m}$ to $600\text{m}$ from the distribution transformer.
- **Spatial Feeder Consensus:** Meters are organized into feeder groups (10 meters/feeder) and building clusters (5 meters/building), enabling cohort comparison and spatial consensus calculation.

---

## 2. Telemetry Channels & Signal Specification

Each simulated smart meter produces **6 physical telemetry channels** at 1-minute intervals:

| Signal Name | Physical Unit | Description & Physics Constraints |
|---|---|---|
| `voltage_v` | Volts (V) | Single-phase RMS voltage (nominal $230\text{V} \pm 10\%$, STEG limits: $207\text{V} \le V \le 253\text{V}$) |
| `current_a` | Amperes (A) | Line current ($I \approx \frac{P \times 1000}{V \times PF}$) |
| `active_power_kw` | Kilowatts (kW) | Real instantaneous household power demand |
| `power_factor` | Dimensionless | Ratio of real to apparent power ($0.70 \le PF \le 1.0$ nominal) |
| `frequency_hz` | Hertz (Hz) | Grid frequency ($50.0\text{ Hz} \pm 0.2\text{ Hz}$) |
| `energy_kwh` | Kilowatt-hours (kWh) | Cumulative interval-accumulated billing register ($E_{t} = E_{t-1} + \frac{P \times \Delta t}{60}$) |

---

## 3. Simulation Parameters & Network Topology

| Parameter | Implemented Value | Engineering Rationale |
|---|---|---|
| **Sampling Interval** | **1 minute** | Realistic smart meter AMI resolution; captures sharp transient surges |
| **Monitored Fleet** | **30 Smart Meters** | Arranged across 3 distribution feeders (10 meters/feeder) and 6 buildings |
| **Feeder Topology** | **Radial Distribution** | Distances span $50\text{m} \to 600\text{m}$ along low-voltage aluminum feeder cables |
| **Household Profiles** | 3 Distinct Profiles | `small_flat` (baseline $0.8\text{ kW}$), `family_home` ($2.2\text{ kW}$), `high_usage_home` ($4.5\text{ kW}$) |
| **Temporal Span** | **7 Days (10,080 min)** | Captures diurnal day/night cycles, weekday routines, and weekend consumption surges |
| **Dataset Volume** | **302,400 rows** | 30 meters $\times$ 10,080 minutes; provides ample volume for statistical calibration |

---

## 4. The 13 Injected Anomaly Scenarios Catalogued

The simulation engine implements **13 distinct anomaly scenarios** covering all 4 competition failure modes:

| # | Scenario Name | Category | Real-World Mechanism | Injected Perturbation |
|---|---|---|---|---|
| 1 | `consumption_spike` | Demand Event | Natural high-load demand surge | $2.0\times\text{–}3.2\times$ power surge; dynamic voltage sag coupled to wire resistance |
| 2 | `meter_drift` | Data Quality | Gradual sensor calibration drift | Progressive linear drift ($+0.6\text{ to }+1.2\text{ kW}$) in power channel |
| 3 | `constant_bias` | Data Quality | Static persistent sensor offset | Persistent active power offset ($+0.8\text{ to }+1.5\text{ kW}$) |
| 4 | `false_data_injection` | Falsification | Cyber tampering on active power channel | Active power scaled by $0.45\times$ or $1.85\times$ while current remains unchanged |
| 5 | `replay_like` | Falsification | Reverse replay of historical telemetry | 4-point electrical vector from earlier quiet hours replayed in peak window |
| 6 | `frozen_meter` | Data Integrity | Sensor firmware/memory lockup | All channels hold static floating-point values ($\sigma^2 = 0$) |
| 7 | `missing_data` | Comms Loss | Packet loss in wireless mesh AMI | Active power values replaced with `NaN` |
| 8 | `energy_power_mismatch` | Data Quality | Inconsistent internal accumulator | Accumulation register inconsistency: $P \times \Delta t \neq \Delta E_{\text{kwh}}$ |
| 9 | `random_corruption` | Data Integrity | Out-of-bounds ADC corruption | Out-of-bounds corruption: $999.0\text{V}$, $-15.0\text{V}$, or impossible $PF = 1.85$ |
| 10 | `dropout` | Comms Loss | Telemetry collapse / power loss | Complete telemetry collapse: $V = 0.0$, $I = 0.0$, $P = 0.0$ |
| 11 | `bias_injection` | Electricity Theft | Proportional stealth meter bypass | Coordinated $35\%$ scaling down of both power and current ($0.65\times$) |
| 12 | `equipment_fault` | Real Event | Inductive appliance breakdown | $2.2\times$ current surge with power factor drop to $0.55$ |
| 13 | `grid_event` | Real Event | Substation-level feeder disturbance | Simultaneous $18\text{V}$ sag across **all 10 meters** on the feeder |

---

## 5. Artifact Registry & File Schemas

Generated datasets are organized under `data/generated/`:

```
data/
├── generated/
│   ├── normal_training.csv      # Clean baseline telemetry (43,200 to 302,400 rows)
│   ├── scored_demo.csv          # Telemetry scored by Trust Layer (27 feature & verdict columns)
│   ├── labels.csv               # Ground-truth event registry with parameter JSON
│   ├── audit_log.csv            # Append-only governance audit log
│   ├── pattern_registry.json    # Anonymized Noosphere collective defense registry
│   ├── summary.csv              # Cross-tabulation of event types by verdict
│   └── statistical_scores.csv   # Module 1 rolling Z-score & CUSUM drift scores
└── sample/
    └── sample_scored_rows.csv   # Lightweight representative sample across all 13 scenarios
```

### 5.1 `labels.csv` — Ground-Truth Event Registry Schema

| Column | Type | Description |
|---|---|---|
| `event_id` | string | Unique event identifier (e.g. `EVT-2026-001`) |
| `scenario_name` | string | Injected scenario name (one of 13 types) |
| `category` | string | `demand_event`, `data_quality`, `falsification`, `equipment_fault`, `grid_event` |
| `target_meter_id` | string | Target smart meter (or `ALL_FEEDER_METERS`) |
| `start_time` | datetime | UTC start timestamp |
| `end_time` | datetime | UTC end timestamp |
| `duration_min` | int | Event duration in minutes |
| `affected_channels`| string | Semicolon-separated channels (e.g. `voltage_v;current_a`) |
| `severity` | float | Severity score ($0.0\text{–}1.0$) |
| `parameters_json` | JSON string | Exact mathematical injection parameters |

### 5.2 `scored_demo.csv` — Scored Telemetry Schema

Contains all raw telemetry columns plus engineered diagnostic fields:
- `voltage_consistency_residual`: $|V_{\text{measured}} - V_{\text{expected}}|$
- `feeder_sag_ratio`: Fraction of feeder meters experiencing simultaneous sag
- `anomaly_score`: Normalized unsupervised decision score $\in [0.0, 1.0]$
- `verdict`: `TRUSTED`, `ACTIONABLE_GRID_EVENT`, `SUSPICIOUS`, or `UNCERTAIN`
- `event_class`: 5-class supervised prediction (`NORMAL`, `GENUINE_GRID_EVENT`, `DATA_QUALITY_ISSUE`, `FALSIFICATION_ATTACK`, `EQUIPMENT_FAULT`)
- `composite_confidence`: Calibrated multi-evidence score $\in [0.0, 1.0]$
- `escalation_tier`: Assigned governance route (`AUTO_ACTION`, `OPERATOR_APPROVAL`, `HUMAN_INVESTIGATION`)
- `explanation`: Deterministic natural language justification

---

## 6. Train / Validation / Test Partitioning Strategy

- **Chronological Split:** 70% Train (Days 1–5), 15% Validation (Day 6), 15% Held-Out Test (Day 7).
- **Stratified Anomaly Representation:** All 13 injected anomaly types appear in training, validation, and held-out test windows.
- **Zero Leakage:** The baseline `normal_training.csv` is strictly isolated for training unsupervised detectors (Isolation Forest) and calibrating nominal EWMA/CUSUM thresholds.
