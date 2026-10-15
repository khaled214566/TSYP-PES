# EnergyMind Tunisia — AI Trust Layer for Smart Energy Systems

> **IEEE TSYP 14 (PES & IES Chapters) — Technical Challenge Prototype**  
> **Repository:** GridSentinel — Physics-Informed Trust Layer, Two-Speed Remediation Swarm, and Federated Noosphere.

---

## ⚡ Overview

**EnergyMind Tunisia (GridSentinel)** is an explainable AI trust layer positioned between smart grid telemetry and operational control rooms. It evaluates data reliability in real time before incoming measurements can trigger automated switching or mislead grid dispatchers. 

The system differentiates **genuine distribution grid events** (such as feeder-wide voltage sags and transformer overloads) from **sensor calibration drift, hardware failures, communications packet corruption, and stealth electricity theft falsification attacks**.

```text
RAW SMART METER TELEMETRY (30 meters, radial feeder)
                      ↓
┌───────────────────────────────────────────────────────────────┐
│                 ENERGYMIND AI TRUST LAYER                     │
│                                                               │
│  ⚡ Fast-Path Engine (< 50ms):                                │
│     Physics Residuals (ΔV = R·d·I) + Feeder Consensus         │
│     5-Class Classifier + Calibrated Composite Confidence      │
│     SHAP Attributions + Rule-Backed Operational Templates     │
│     3-Tier Governance Router with Anti-Bias Safeguards        │
│                                                               │
│  🧠 Slow-Path Engine (Advisory ~ 2–4s):                       │
│     Multi-Agent RAG Swarm (LiteLLM + ChromaDB)                │
│     Grid Code Retrieval (IEEE 1547, IEC 61850, STEG Code)     │
│     Remediation Planning + Automated Safety Policy Auditor    │
└───────────────────────────────────────────────────────────────┘
                      ↓
┌───────────────────────────────────────────────────────────────┐
│     UNIFIED SINGLE-PANE OPERATOR COCKPIT (React 18)           │
│  Zone 1: Feeder Topology & Dynamic Line Drop Waterfall        │
│  Zone 2: Incident Drill-Down Drawer (SHAP + RAG Plan)         │
│  Zone 3: Noosphere Multi-Node Federated Pattern Sync          │
└───────────────────────────────────────────────────────────────┘
```

---

## 🎯 Alignment with TSYP 14 Cahier des Charges

| Challenge Pillar | Implementation in GridSentinel | Primary Documentation |
|---|---|---|
| **1. Anomaly & Bias Detection** | Physics line drop ($\Delta V = R \cdot d \cdot I$) + Feeder consensus (`feeder_sag_ratio`) + 13 injected scenarios covering all 4 failure categories | [`docs/technical_documentation.md`](docs/technical_documentation.md) |
| **2. Confidence & Explainability** | Multi-evidence composite confidence formula ($C = \sum w_i S_i$) + Dual-layer SHAP attributions and Jinja2 natural-language templates | [`EnergyMind_Execution_Plan.md`](EnergyMind_Execution_Plan.md) |
| **3. Escalation & Governance** | 3-tier routing (`AUTO_ACTION`, `OPERATOR_APPROVAL`, `HUMAN_INVESTIGATION`) + Anti-Automation Bias 5% spot-checks + Cognitive friction for high-impact actions | [`docs/phase1_proposal.md`](docs/phase1_proposal.md) |
| **4. Shared Learning (Noosphere)** | Local 2-node testbed (`Node-Tunis-Nord` :8000 and `Node-Sfax-Sud` :8001) sharing privacy-preserving dimensionless JSON signatures | [`data/generated/pattern_registry.json`](data/generated/pattern_registry.json) |
| **Evaluation Metrics** | Dedicated Module 14 Benchmark Suite measuring Precision, Recall, FPR, Fast-Path (<50ms) vs Slow-Path (<4s) Latency, and SHAP faithfulness | [`EnergyMind_Execution_Plan.md`](EnergyMind_Execution_Plan.md) |
| **Business Scope (1 Bonus Pt)** | 3-Year CapEx/OpEx for 100k smart meters with STEG Tunisia, demonstrating 13.1-month ROI via 15% theft reduction | [`EnergyMind_Execution_Plan.md`](EnergyMind_Execution_Plan.md) |

---

## 🚀 Quick Start

### 1. Environment Setup

Python 3.10+ is recommended.

```bash
# Clone and prepare virtual environment
python -m venv .venv

# Activate environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Simulation & Anomaly Generation

Generate multi-day 1-minute smart meter telemetry for 30 households across 13 distinct anomaly scenarios:

```bash
# Windows PowerShell
$env:PYTHONPATH = "src"
python -m gridsentinel.cli --steps 1440 --meters 30 --seed 42

# macOS/Linux
PYTHONPATH=src python -m gridsentinel.cli --steps 1440 --meters 30 --seed 42
```

Outputs are generated in `data/generated/`:
- `normal_training.csv`: Clean baseline telemetry (43,200 rows/feeder).
- `scored_demo.csv`: 43,200 rows with 27 electrical, diagnostic, verdict, and explanation columns.
- `labels.csv`: Timestamped ground-truth event registry.
- `audit_log.csv`: Append-only compliance decision trail.
- `pattern_registry.json`: Anonymized Noosphere collective defense registry.

### 3. Run Automated Validation Test Suite

```bash
pytest -v
```

---

## 🔬 The 13 Injected Anomaly Scenarios Catalogued

| # | Scenario Name | Category | Real-World Mechanism |
|---|---|---|---|
| 1 | `consumption_spike` | Demand Event | $2.0\times\text{–}3.2\times$ power surge; dynamic voltage sag coupled to wire resistance |
| 2 | `meter_drift` | Data Quality | Gradual progressive linear drift ($+0.6\text{ to }+1.2\text{ kW}$) in power channel |
| 3 | `constant_bias` | Data Quality | Static persistent active power offset ($+0.8\text{ to }+1.5\text{ kW}$) |
| 4 | `false_data_injection` | Falsification | Active power scaled by $0.45\times$ or $1.85\times$ while current remains unchanged |
| 5 | `replay_like` | Falsification | Temporal replay of 4-point historical measurement vector from earlier quiet hours |
| 6 | `frozen_meter` | Data Integrity | Sensor memory crash: all channels hold static floating-point value ($\sigma^2 = 0$) |
| 7 | `missing_data` | Comms Loss | Telemetry packet loss: active power values replaced with `NaN` |
| 8 | `energy_power_mismatch` | Data Quality | Accumulation register inconsistency: $P \times \Delta t \neq \Delta E_{\text{kwh}}$ |
| 9 | `random_corruption` | Data Integrity | Out-of-bounds corruption: $999.0\text{V}$, $-15.0\text{V}$, or impossible $PF = 1.85$ |
| 10 | `dropout` | Comms Loss | Complete telemetry collapse: $V = 0.0$, $I = 0.0$, $P = 0.0$ |
| 11 | `bias_injection` | Electricity Theft | Proportional stealth theft: $35\%$ scaling down of both power and current ($0.65\times$) |
| 12 | `equipment_fault` | Real Event | Inductive equipment breakdown: $2.2\times$ current surge with power factor drop to $0.55$ |
| 13 | `grid_event` | Real Event | Feeder-wide grid disturbance: simultaneous $18\text{V}$ sag across all meters on feeder |

---

## 🏛️ Two-Speed Engine Architecture

1. **⚡ Fast-Path (Sub-50ms Reaction):**
   - Ingests streaming telemetry ticks.
   - Computes physical line drops ($\Delta V = R \cdot d \cdot I$) and feeder consensus ratios.
   - Evaluates multi-class XGBoost classifier and calculates calibrated composite confidence $C \in [0.0, 1.0]$.
   - Generates local SHAP feature attributions and deterministic rule-backed explanations.
   - Executes immediate emergency voltage regulation or auto-quarantine for high-confidence events ($C \ge 0.95$).

2. **🧠 Slow-Path (Asynchronous 2–4s Multi-Agent Swarm):**
   - Triggered asynchronously without blocking the grid stream.
   - **Agent 1 (Diagnostic Synthesizer):** Formulates root-cause technical hypotheses.
   - **Agent 2 (RAG Retriever):** Queries local ChromaDB for utility standards (IEEE 1547, IEC 61850, STEG Code).
   - **Agent 3 (Remediation Planner):** Constructs actionable mitigation playbooks.
   - **Agent 4 (Safety Auditor):** Strictly verifies electrical limits and hospital protection constraints.
   - **Agent 5 (Feedback Learner):** Ingests human operator overrides into the retraining queue and Noosphere pattern registry.

---

## 📊 Core Documentation Index

- [`EnergyMind_Execution_Plan.md`](EnergyMind_Execution_Plan.md) — Master Execution Plan v2.0 with complete module dependency order, Two-Speed architecture, benchmarking suite, and STEG business model.
- [`docs/phase1_proposal.md`](docs/phase1_proposal.md) — Official Phase 1 Proposal document for TSYP 14 competition submission.
- [`docs/technical_documentation.md`](docs/technical_documentation.md) — Complete technical specification, physics formulations, data schemas, and mathematical proofs.
- [`docs/phase2_module1_statistical_engine.md`](docs/phase2_module1_statistical_engine.md) — Implemented Module 1 Statistical & Drift Engine documentation.
- [`data/README.md`](data/README.md) — Synthetic dataset documentation and generated artifact registry.

---

## ⚖️ Scope & Safety Notice

This prototype simulates a residential neighborhood distribution feeder. While grounded in realistic power system physics ($\Delta V = R \cdot d \cdot I$) and international utility standards (IEEE 1547, IEC 61850), it is an offline research and demonstration prototype for TSYP 14 and is not directly interfaced with live STEG utility SCADA networks.
