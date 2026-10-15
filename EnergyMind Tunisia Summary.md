# EnergyMind Tunisia: Executive Summary (v2.0)

> **IEEE TSYP 14 (PES & IES Chapters) — Technical Challenge Deliverable**  
> **Status:** Rectified Master Summary aligned with Execution Plan v2.0

---

## 1. Core Objective

**EnergyMind Tunisia** is an AI **trust layer for smart energy systems**. It sits directly between raw smart meter telemetry streams and utility control-room decisions, continuously evaluating data credibility before abnormal readings can trigger automated switching or mislead dispatchers.

It solves the fundamental grid dilemma: **Is an abnormal reading a genuine physical grid event, a degraded or drifting sensor, corrupted telemetry, or a cyber-physical falsification attack?**

---

## 2. Four Mandatory Pillars (Challenge Mapping)

1. **Anomaly & Bias Detection:** Physics-informed residuals ($\Delta V = R \cdot d \cdot I$) coupled with spatial feeder consensus (`feeder_sag_ratio`) across 13 injected scenarios covering demand events, data quality problems, falsification attacks, and real equipment faults.
2. **Confidence Scores & Explainability:** Multi-evidence composite confidence calculation ($C = \sum w_i S_i \in [0.0, 1.0]$) rejecting uncalibrated black-box softmax, combined with dual-layer explainability (local SHAP waterfall attributions for engineers + deterministic Jinja2 natural-language templates for operators).
3. **Human-AI Escalation & Governance:** 3-tier escalation (`AUTO_ACTION`, `OPERATOR_APPROVAL`, `HUMAN_INVESTIGATION`) reinforced with concrete psychological safeguards:
   - **Anti-Over-Trust (Automation Bias):** 5% random spot-check demotion of `AUTO_ACTION` to mandatory operator review + cognitive friction requiring SHAP acknowledgment before high-impact switching.
   - **Anti-Under-Trust (Alert Fatigue):** Spatial consensus noise filtering slashing false sirens by $>90\%$ + explicit Physics Verification Proof Cards.
4. **Shared Learning Across the Noosphere:** Multi-node collective defense sharing privacy-preserving dimensionless mathematical signatures ($PF < 0.65$, consensus ratios) between distribution districts without leaking raw customer load profiles.

---

## 3. Two-Speed Engine Architecture

To eliminate the **3–15 second LLM latency bottleneck** while preserving deep domain intelligence, the architecture decouples into two concurrent operational lanes:

1. **⚡ Fast-Path (Sub-50ms Reaction):**
   - Real-time tick ingestion for 30 meters.
   - Modules 1–5 feature pipeline (rolling Z-scores, Isolation Forest, impedance drop residuals, replay hash checks, and feeder sag ratios).
   - Module 6 supervised 5-class XGBoost classifier.
   - Module 7 composite confidence engine & Module 8 SHAP/rule explanations.
   - Immediate emergency triage, voltage regulation, or safety trip dispatch.

2. **🧠 Slow-Path (Asynchronous 2–4s Multi-Agent Swarm):**
   - Dispatched asynchronously without delaying grid protection.
   - **Agent 1 (Diagnostic Synthesizer):** Translates physical telemetry into root-cause hypotheses.
   - **Agent 2 (RAG Retriever):** Queries local ChromaDB vector store containing IEEE 1547, IEC 61850, STEG Low-Voltage Grid Code, and DLMS/COSEM manuals.
   - **Agent 3 (Remediation Planner):** Formulates step-by-step mitigation playbooks.
   - **Agent 4 (Safety Policy Auditor):** Validates constraints (e.g. protects critical public hospitals from automated disconnection).
   - **Agent 5 (Feedback Learner):** Ingests human operator sign-offs into the retraining buffer and Noosphere registry.

---

## 4. Key Differentiating Features

| Feature | Operational Mechanism |
|---|---|
| **Distinguishing Grid Event vs Data Problem** | Radial feeder voltage drop ($\Delta V = R \cdot d \cdot I$) ensures line sag is expected at far meters. When sag is simultaneous across $\ge 70\%$ of feeder meters, it is flagged as a **Genuine Grid Event**. When isolated to one meter, it is flagged as **Data Quality** or **Tampering**. |
| **Composite Confidence Engine** | Five-factor fusion: $C = 0.35 P(\text{class}) + 0.25 (\text{Consensus}) + 0.20 (\text{Agreement}) + 0.10 (\text{Health}) + 0.10 (1 - \text{Residual})$. |
| **Unified Single-Pane Cockpit** | Replaced fragmented 7-screen UI with a single responsive React 18 cockpit tailored for a 3-minute pitch: Zone 1 (Live Feeder Map & Impedance Curves), Zone 2 (Incident Drill-Down Drawer with SHAP & RAG Plan), Zone 3 (Noosphere Sync Strip). |
| **Noosphere Local Testbed** | 2-node networked testbed (`Node-Tunis-Nord` on port 8000 and `Node-Sfax-Sud` on port 8001) demonstrating real-time pattern exchange via JSON Schema. |

---

## 5. Demonstration Scenarios (Validation Suite)

| Scenario | Injected Condition | Expected AI Verdict & Speed | Prescribed Action |
|---|---|---|---|
| **Scenario A: Genuine Grid Event** | Simultaneous $18\text{V}$ sag across all 10 meters on Feeder 1 | `ACTIONABLE_GRID_EVENT` (Fast-Path: $<50\text{ ms}$, $C \ge 0.95$) | Immediate automated voltage regulation command |
| **Scenario B: Sensor Bias** | Single meter `meter_004` exhibits persistent $+9.5\text{V}$ bias while peers stay nominal | `DATA_QUALITY_ISSUE` (Fast-Path: $<50\text{ ms}$, $C > 0.85$) | Dispatches calibration inspection ticket |
| **Scenario C: Falsified Theft Attack** | Single meter `meter_001` performs stealth $35\%$ theft ($P \times 0.65$, $I \times 0.65$) | `FALSIFICATION_ATTACK` (Fast-Path: $<50\text{ ms}$, $C > 0.85$) | Dispatches tamper inspection ticket & quarantines data |

---

## 6. Business Scope & STEG Economic Model (1 Bonus Point)

- **Pilot Deployment Target:** 100,000 smart meters in District Tunis-Nord.
- **3-Year Total Investment:** **$229,000** ($145k Year 1 CapEx/setup + $42k/yr OpEx for edge gateways, self-hosted LLM inference, SCADA integration, and MLOps).
- **Economic Return:** Recovers an estimated **15% of non-technical distribution losses (theft)**, saving $\approx \$210,000\text{/year}$.
- **Payback Period:** Achieved in **13.1 months** ($< 14$ months), yielding a net 3-year savings of **$401,000**.

---

## 7. 8-Week Agile Roadmap (Oct 15 to Dec 12)

- **Sprint 1 (Weeks 1–2):** Feature extraction, line drop physics, and Module 1–5 evidence engines.
- **Sprint 2 (Weeks 3–4):** XGBoost 5-class classifier, composite confidence, SHAP explainability, and Fast/Slow Multi-Agent Swarm.
- **Sprint 3 (Weeks 5–6):** FastAPI streaming backend, Single-Pane Operator Cockpit, and anti-bias friction UI.
- **Sprint 4 (Weeks 7–8):** Module 14 automated benchmark suite, 2-node Docker demo, and 3-minute pitch rehearsal.
