# GridSentinel Technical Documentation (v2.0)

**Project:** GridSentinel — Trustworthy AI for a Smart-Metered Neighborhood  
**Challenge Context:** TSYP14 EnergyMind Tunisia — *Architects of the Energy Noosphere: A Human-AI Collective Intelligence Network for Energy Resilience*  
**Document Status:** Comprehensive System Architecture & Algorithmic Specification (v2.0)  
**Implementation:** Python 3.11, pandas, NumPy, SciPy, scikit-learn, XGBoost, SHAP, FastAPI, React 18

---

## 1. System Mission & Core Purpose

GridSentinel is an explainable AI **Trust Layer** deployed on electrical distribution networks. It operates between smart meter telemetry streams and control-room automated actuators, resolving the fundamental power systems challenge: **distinguishing genuine physical grid events from sensor degradation, calibration drift, packet corruption, and cyber-physical falsification attacks (theft)**.

The system enforces a **Two-Speed Architecture**:
1. **⚡ Fast-Path Engine (< 50ms):** Executes sub-second deterministic safety triage, physics-informed line impedance validation, supervised event classification, composite confidence scoring, and local SHAP feature attributions.
2. **🧠 Slow-Path Engine (Advisory ~ 2–4s):** An asynchronous multi-agent RAG swarm (LiteLLM + ChromaDB) that queries international standards (IEEE 1547, IEC 61850, STEG Code) to synthesize safety-audited remediation playbooks without impeding fast grid protection.

---

## 2. Electrical Topology & Physical Modeling

### 2.1 Radial Feeder Topology
GridSentinel models a 230V/400V radial distribution feeder serving 30 household smart meters:
- **Feeder Organization:** 3 Feeder Cohorts (10 meters/feeder) across 6 residential buildings (5 meters/building).
- **Distance Gradient:** Buildings are distributed along the feeder from the substation transformer:
  $$d \in [50.0\text{m}, 120.0\text{m}, 220.0\text{m}, 350.0\text{m}, 480.0\text{m}, 600.0\text{m}]$$
- **Physical Cable Parameters:** Low-voltage aluminum distribution cable with linear resistance $R_{\text{cable}} = 0.0004\,\Omega/\text{m}$.

### 2.2 Physics-Informed Voltage Drop Formulation
The expected terminal voltage at any meter $i$ depends dynamically on distance and current draw:
$$V_{\text{expected}, i} = V_{\text{substation}} - (R_{\text{cable}} \cdot d_i \cdot I_i)$$

The **Voltage Consistency Residual** is computed continuously:
$$\text{residual}_i = |V_{\text{measured}, i} - V_{\text{expected}, i}|$$

If a high load causes voltage to sag at a 600m terminal meter while $\text{residual}_i \approx 0$, the system recognizes this as physically expected line drop, eliminating false alarms.

---

## 3. High-Level Two-Speed Architecture

```text
                           RAW SMART METER TELEMETRY (30 meters/min)
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
     ⚡ FAST-PATH ENGINE (< 50ms)                      🧠 SLOW-PATH ASYNC SWARM (2–4s)
     (Deterministic Safety & Triage)                  (Knowledge-Grounded Playbooks)
                     │                                                 │
  ┌──────────────────┴──────────────────┐             ┌────────────────┴────────────────┐
  │ 1. Feature & Physics Line Drop      │             │ Agent 1: Diagnostic Synthesizer │
  │    Residuals (ΔV = R·d·I)           │             │ (Root-cause hypothesis query)   │
  │ 2. Feeder Consensus Ratio           │             │               ↓                 │
  │ 3. 5-Class Classifier (XGBoost)     │             │ Agent 2: RAG Retriever          │
  │ 4. Composite Confidence Formula     │             │ (IEEE 1547, IEC 61850, STEG)    │
  │ 5. SHAP Attributions & Rules        │             │               ↓                 │
  │ 6. 3-Tier Governance Router         │             │ Agent 3: Remediation Planner    │
  │    - 5% Spot-Check Anti-Bias        │             │ (Step-by-step mitigation plan)  │
  │    - Cognitive Friction Confirmation│             │               ↓                 │
  └──────────────────┬──────────────────┘             │ Agent 4: Safety Policy Auditor  │
                     │                                │ (Hospital check, tap limits)    │
                     ▼                                └────────────────┬────────────────┘
        Emergency Grid Protection /                                    │
           Instant Tripping Action                                     ▼
                     │                                    Audited Remediation Plan
                     └────────────────────────┬────────────────────────┘
                                              ▼
                    ┌──────────────────────────────────────────────────┐
                    │     UNIFIED SINGLE-PANE OPERATOR COCKPIT         │
                    │  Zone 1: Feeder Topology & Dynamic Drop Curves   │
                    │  Zone 2: Incident Drill-Down Drawer (SHAP + Plan)│
                    │  Zone 3: Noosphere Collective Defense Strip      │
                    └─────────────────────────┬────────────────────────┘
                                              ▼
                    ┌──────────────────────────────────────────────────┐
                    │     AGENT 5: CONTINUOUS FEEDBACK & NOOSPHERE     │
                    │  - Retraining Buffer Queue                       │
                    │  - Privacy-Preserving JSON Disturbance Signatures│
                    └──────────────────────────────────────────────────┘
```

---

## 4. Telemetry Schema & Mathematical Consistency

Each record contains 6 physical measurements sampled at 1-minute intervals:

| Field | Physical Dimension | Mathematical Consistency Check |
|---|---|---|
| `voltage_v` | Volts (V) | $V \in [180.0, 270.0]$, nominal $230\text{V} \pm 10\%$ |
| `current_a` | Amperes (A) | $I \ge 0.0\text{ A}$, physical current magnitude |
| `active_power_kw` | Kilowatts (kW) | $P_{\text{calc}} \approx \frac{V \cdot I \cdot PF}{1000} \implies |P - P_{\text{calc}}| < 0.25\text{ kW}$ |
| `power_factor` | Dimensionless | $PF \in [0.70, 1.00]$ nominal (inductive load drop: $PF < 0.65$) |
| `frequency_hz` | Hertz (Hz) | $f \in [49.5, 50.5]\text{ Hz}$ |
| `energy_kwh` | Kilowatt-hours (kWh) | $\Delta E_{\text{kwh}} \approx \frac{P \times \Delta t}{60} \implies |\Delta E - \Delta E_{\text{expected}}| < 0.08\text{ kWh}$ |

---

## 5. The 13 Injected Anomaly Scenarios Catalogued

| # | Scenario Name | Category | Real-World Mechanism | Injected Perturbation & Signature |
|---|---|---|---|---|
| 1 | `consumption_spike` | Demand Event | Legitimate household load surge | $2.0\times\text{–}3.2\times$ power surge; dynamic voltage sag consistent with wire resistance |
| 2 | `meter_drift` | Data Quality | Sensor aging / calibration drift | Progressive linear drift ($+0.6\text{ to }+1.2\text{ kW}$) in power channel |
| 3 | `constant_bias` | Data Quality | Static persistent calibration offset | Persistent active power offset ($+0.8\text{ to }+1.5\text{ kW}$) |
| 4 | `false_data_injection`| Falsification | Cyber-tampering of active power | Active power scaled by $0.45\times$ or $1.85\times$ while current remains unchanged |
| 5 | `replay_like` | Falsification | Reverse replay attack | 4-point electrical vector from earlier quiet hours replayed during peak load |
| 6 | `frozen_meter` | Data Integrity | ADC / sensor memory crash | Telemetry holds static floating-point value ($\sigma^2 = 0$) across all channels |
| 7 | `missing_data` | Comms Loss | Packet loss in wireless AMI mesh | Active power readings replaced with `NaN` |
| 8 | `energy_power_mismatch`| Data Quality | Internal billing register corruption | Accumulation register inconsistency: $P \times \Delta t \neq \Delta E_{\text{kwh}}$ |
| 9 | `random_corruption` | Data Integrity | Extreme ADC hardware corruption | Out-of-bounds corruption: $999.0\text{V}$, $-15.0\text{V}$, or impossible $PF = 1.85$ |
| 10 | `dropout` | Comms Loss | Total telemetry link collapse | Complete telemetry collapse: $V = 0.0$, $I = 0.0$, $P = 0.0$ |
| 11 | `bias_injection` | Electricity Theft | Proportional stealth meter bypass | Coordinated $35\%$ scaling down of both power and current ($0.65\times$) |
| 12 | `equipment_fault` | Real Event | Inductive appliance breakdown | $2.2\times$ current surge with severe power factor degradation ($PF = 0.55$) |
| 13 | `grid_event` | Real Event | Feeder-wide grid disturbance | Simultaneous $18\text{V}$ sag across **all 10 meters** on the feeder |

---

## 6. Detection Engines & Evidence Pipeline (Modules 1–5)

1. **Module 1 (Statistical Drift Engine):**
   - Implements rolling Z-scores, Exponentially Weighted Moving Average (EWMA), Cumulative Sum (CUSUM), and Page-Hinkley test to detect subtle calibration offsets.
2. **Module 2 (Unsupervised Isolation Forest):**
   - 160 estimators, contamination $\approx 0.03$, trained on clean normal baseline to output continuous anomaly scores $\in [0.0, 1.0]$.
3. **Module 3 (Line Impedance & Sensor Health Tracker):**
   - Tracks $|V_{\text{measured}} - V_{\text{expected}}|$ and maintains a continuous rolling Sensor Health Index ($0\text{–}100$).
4. **Module 4 (Data Integrity & Sequence Replay Engine):**
   - Zero-variance run length detection, sliding-window vector autocorrelation, and physical boundary limit assertions.
5. **Module 5 (Spatial Consensus & Cohort Feature Pipeline):**
   - Calculates `feeder_sag_ratio`: the proportion of feeder peers concurrently seeing sags $\ge 10\text{V}$.
   - Calculates `cohort_power_ratio`: divergence of consumption relative to peer households of the same demographic type.

---

## 7. Multi-Evidence Composite Confidence Engine (Module 7)

GridSentinel rejects raw softmax probabilities because deep learning models can be overconfident on out-of-distribution adversarial data. Instead, it computes an auditable **Composite Confidence Index**:

$$C = w_1 P(\text{class}) + w_2 (\text{Consensus Ratio}) + w_3 (\text{Detector Agreement}) + w_4 \left(\frac{\text{Health}}{100}\right) + w_5 (1.0 - \text{Normalized Residual})$$

where weights are calibrated to $w = [0.35, 0.25, 0.20, 0.10, 0.10]$.

---

## 8. Dual Explainability Engine (Module 8)

1. **Technical Layer (SHAP `TreeExplainer`):** Computes exact local Shapley feature contributions ($+0.42$ `feeder_sag_ratio`, $+0.28$ `voltage_consistency_residual`, etc.).
2. **Operational Layer (Deterministic Jinja2 Templates):** Translates numeric attributions into natural-language explanations:
   > *"Feeder-wide voltage sag detected (consensus: 100%, 10/10 meters affected). Terminal voltage dropped to 212.0V (-18.0V below nominal). Dynamic line impedance residual is 0.0V, confirming a physical upstream grid disturbance."*

---

## 9. Governance & Human Trust Dynamics (Module 9)

### 9.1 Three-Tier Escalation Thresholds
- `AUTO_ACTION` ($C \ge 0.95$ and low physical risk): Tap changer command or telemetry imputation.
- `OPERATOR_APPROVAL` ($0.70 \le C < 0.95$): Actionable advisory ticket with one-click approval.
- `HUMAN_INVESTIGATION` ($C < 0.70$ or novel anomaly): Urgent escalation to engineering dispatch.

### 9.2 Human Trust Safeguards
- **Anti-Over-Trust (Automation Bias):** 5% of `AUTO_ACTION` events are randomly demoted to mandatory operator sign-off with cognitive friction prompts requiring the operator to review the primary SHAP driver.
- **Anti-Under-Trust (Alert Fatigue):** Spatial consensus filtering suppresses uncorroborated single-meter noise, reducing alarms by $>90\%$, while Physics Proof Cards provide visible validation.

---

## 10. Rigorous Evaluation & Latency Benchmarks (Module 14)

- **Detection Precision:** $\ge 96.5\%$ across 43,200 test ticks.
- **Detection Recall:** $\ge 98.0\%$ across all 13 injected scenarios.
- **False-Positive Rate:** $< 1.2\%$ on normal multi-day baselines.
- **Fast-Path Latency:** $< 50\text{ ms}$ (p99).
- **Slow-Path Latency:** $< 3.5\text{ s}$ (p95).
- **Explanation Faithfulness:** $> 92\%$ alignment with ground-truth perturbations.

---

## 11. Noosphere Multi-Node Federated Testbed (Module 16)

- **Zero Raw Data Exchange:** No customer load profiles or raw waveforms ever leave the local node.
- **Exchanged Schema (`pattern_registry.json`):**
  ```json
  {
    "pattern_id": "NOO-TN-2026-004",
    "event_category": "FALSIFICATION_STEALTH_THEFT",
    "mathematical_signature": {
      "power_current_scale_ratio": 0.65,
      "impedance_residual_deviation": 0.0,
      "cohort_power_divergence_z": -2.85,
      "spatial_consensus_ratio": 0.0
    },
    "origin_node_hash": "sha256_e4b1c7...",
    "verification_score": 0.98
  }
  ```
- **Live Local Testbed:** Runs two independent nodes (`Node-Tunis-Nord` on port 8000 and `Node-Sfax-Sud` on port 8001) connected to a shared discovery broker to prove live federated pattern sharing in code.

---

## 12. Business Scope & STEG Economic Model (1 Bonus Point)

- **Deployment Target:** 100,000 smart meters in District Tunis-Nord.
- **3-Year Investment:** $229,000 ($145k Year 1 CapEx + $42k/yr OpEx).
- **Non-Technical Loss Savings:** Recovers 15% of distribution theft losses ($\approx \$210,000\text{/year}$).
- **Payback Period:** Achieved in **13.1 months** (<14 mo.) with net 3-year savings of **$401,000**.
