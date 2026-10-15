# Smart-Metered Neighborhood Pilot Run & Benchmark Report (v2.0)

> **IEEE TSYP 14 (PES & IES Chapters) — Pilot Experiment Documentation**  
> **Status:** Updated to reflect the 30-meter, 13-scenario prototype evaluation and Module 1 statistical drift validation.

---

## 1. Experiment Overview & Setup

The GridSentinel prototype was evaluated across two distinct benchmarking regimes:
1. **Initial Baseline Pilot (Legacy):** 10 meters, 360 minutes, 8 legacy anomaly scenarios.
2. **Phase 1 Full-Feeder Benchmark (Current v2.0):** 30 smart meters across a 600m radial distribution feeder, 1,440 minutes (24 hours) to 10,080 minutes (7 days), evaluating all **13 injected anomaly scenarios** with line impedance physics ($\Delta V = R \cdot d \cdot I$) and Module 1 statistical drift tracking.

### Configuration Parameters
- **Sampling Interval:** 1 minute.
- **Topology:** 30 households across 3 feeder groups (10 meters/feeder) and 6 buildings (50m to 600m from transformer).
- **Physical Wire Drop:** $R_{\text{cable}} = 0.0004\,\Omega/\text{m}$, dynamic drop $\Delta V = R \cdot d \cdot I$.
- **Training Baseline:** 43,200 rows of clean diurnal telemetry (`data/generated/normal_training.csv`).
- **Evaluation Dataset:** 43,200 rows of multi-signal telemetry containing all 13 injected scenarios (`data/generated/scored_demo.csv`).

---

## 2. Benchmark Results & Metric Progression

| Metric | Initial 8-Scenario Baseline | Current v2.0 Full-Feeder Benchmark | Target Production Spec (Module 14) |
|---|---:|---:|---:|
| **Precision** | 0.464 | **0.942** | $\ge 0.965$ |
| **Recall** | 0.761 | **0.978** | $\ge 0.980$ |
| **F1-Score** | 0.576 | **0.960** | $\ge 0.972$ |
| **False-Positive Rate (Normal)**| 0.045 | **0.011** | $< 0.012$ |
| **Fast-Path Latency (p99)** | ~ 12 ms | **< 35 ms** | $< 50\text{ ms}$ |
| **Slow-Path Latency (p95)** | N/A (Manual) | **~ 2.8 s** | $< 3.5\text{ s}$ |

---

## 3. Scenario-by-Scenario Validation Analysis

| # | Scenario | Injected Condition | AI Verdict & Detection Status | Evidence & Physical Mechanism |
|---|---|---|---|---|
| 1 | `consumption_spike` | $2.0\times\text{–}3.2\times$ power surge | `TRUSTED` / `UNCERTAIN` | Physics drop $\Delta V = R \cdot d \cdot I$ holds; line impedance residual $< 1.5\text{V}$, correctly ruling out sensor fault |
| 2 | `meter_drift` | Linear drift $+0.6\text{ to }+1.2\text{ kW}$ | `DATA_QUALITY_ISSUE` (100% caught) | Module 1 CUSUM & Page-Hinkley cumulative score crosses drift threshold |
| 3 | `constant_bias` | Static $+0.8\text{ to }+1.5\text{ kW}$ offset | `DATA_QUALITY_ISSUE` (100% caught) | Persistent non-zero power residual $|P - \frac{VI\cdot PF}{1000}| > 0.25\text{ kW}$ |
| 4 | `false_data_injection`| Active power scaled by $0.45\times$ or $1.85\times$ | `FALSIFICATION_ATTACK` (100% caught) | Sharp discrepancy between active power and companion line current |
| 5 | `replay_like` | 4-point vector temporal replay | `FALSIFICATION_ATTACK` (94% caught) | Sliding-window autocorrelation and entropy sequence hash collision |
| 6 | `frozen_meter` | Memory lockup ($\sigma^2 = 0$) | `DATA_INTEGRITY_ISSUE` (100% caught) | Zero-variance run length $\ge 5$ consecutive minutes |
| 7 | `missing_data` | Active power telemetry = `NaN` | `DATA_INTEGRITY_ISSUE` (100% caught) | Missing measurement schema check |
| 8 | `energy_power_mismatch`| Accumulator mismatch | `DATA_QUALITY_ISSUE` (100% caught) | $|\Delta E_{\text{kwh}} - \frac{P \times \Delta t}{60}| > 0.08\text{ kWh}$ |
| 9 | `random_corruption` | ADC out-of-bounds ($999\text{V}$, $-15\text{V}$) | `DATA_INTEGRITY_ISSUE` (100% caught) | Strict physical boundary assertions violated |
| 10 | `dropout` | Total link collapse ($V=0, I=0, P=0$) | `COMMUNICATIONS_LOSS` (100% caught) | Simultaneous zero-reading across all electrical channels |
| 11 | `bias_injection` | Stealth electricity theft ($0.65\times$) | `FALSIFICATION_ATTACK` (96% caught) | Cohort consumption divergence Z-score $<-2.5$ with zero feeder consensus |
| 12 | `equipment_fault` | Inductive appliance surge ($PF=0.55$) | `EQUIPMENT_FAULT` (98% caught) | Sudden current surge coupled with severe reactive power factor collapse |
| 13 | `grid_event` | Simultaneous $18\text{V}$ sag across feeder | `ACTIONABLE_GRID_EVENT` (100% caught)| Feeder sag consensus ratio $= 1.0$ ($10/10$ meters affected simultaneously) |

---

## 4. Key Takeaways & Milestones Achieved

1. **Resolution of Replay & Drift Weaknesses:** By introducing Module 1's CUSUM/EWMA drift tracking and Module 4's sliding-window sequence hashing, stealth drift and replay attacks are now flagged reliably.
2. **Physics Residual Eliminates Spike False Alarms:** In the legacy baseline, legitimate demand spikes caused voltage dips that triggered false alarms. Coupling dynamic wire resistance ($\Delta V = R \cdot d \cdot I$) allows the system to verify that voltage dips are physically justified by current draw.
3. **Decisive Feeder Consensus:** Scenario 13 proves that feeder-wide voltage sags achieve 100% spatial consensus, cleanly differentiating broad grid crises from local meter defects.

---

## 5. Reproduction Instructions

To reproduce the full 30-meter, 13-scenario benchmark run:

```bash
# Windows PowerShell
$env:PYTHONPATH = "src"
python -m gridsentinel.cli --steps 1440 --meters 30 --seed 42 --out data/generated

# Run validation tests
pytest -v
```
