# EnergyMind Tunisia — Project Proposal Plan (v2.0)
### IEEE TSYP 14 Challenge Submission — PES & IES Chapters

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Project Objectives & Scope](#3-project-objectives--scope)
4. [System Architecture Overview: The Two-Speed Engine](#4-system-architecture-overview-the-two-speed-engine)
5. [Four Mandatory Pillars](#5-four-mandatory-pillars)
6. [Technology Stack](#6-technology-stack)
7. [Development Phases & 8-Week Agile Roadmap](#7-development-phases--8-week-agile-roadmap)
8. [Dataset & 13-Scenario Simulation Strategy](#8-dataset--13-scenario-simulation-strategy)
9. [Evaluation Metrics & Automated Benchmarking Suite](#9-evaluation-metrics--automated-benchmarking-suite)
10. [Human-AI Governance Model: Addressing Over-Trust & Under-Trust](#10-human-ai-governance-model-addressing-over-trust--under-trust)
11. [Multi-Node / Noosphere Federated Collective Defense](#11-multi-node--noosphere-federated-collective-defense)
12. [Single-Pane Operator Cockpit Design](#12-single-pane-operator-cockpit-design)
13. [Business Scope & Techno-Economic Model (STEG Context)](#13-business-scope--techno-economic-model-steg-context)
14. [Team Workload & Pair-Programming Execution Flow](#14-team-workload--pair-programming-execution-flow)
15. [Risk Analysis & Mitigation Matrix](#15-risk-analysis--mitigation-matrix)
16. [References & Standards](#16-references--standards)

---

## 1. Executive Summary

A concise, high-impact overview of EnergyMind Tunisia: an AI-driven trust layer for power distribution grids that evaluates telemetry credibility before automated switching can act or operators are alerted. Highlights the core technical breakthroughs:
- Physics-informed residuals coupling line drop ($\Delta V = R \cdot d \cdot I$) with spatial consensus (`feeder_sag_ratio`) to decisively distinguish genuine grid events from sensor degradation or falsification.
- Two-Speed architecture eliminating LLM latency traps by separating deterministic sub-50ms Fast-Path triage from asynchronous 2–4s Slow-Path RAG remediation planning.
- Rigorous human-trust governance addressing both automation complacency (over-trust) and alarm fatigue (under-trust).

---

## 2. Problem Statement

Details the vulnerability of modern smart grid automation to untrusted sensor inputs:
- Data quality problems (calibration drift, frozen registers, packet drops) trigger false operator dispatches.
- Stealth cyber-physical falsification (e.g. coordinated power/current scaling for electricity theft) evades simple threshold checks.
- Lack of explainability in black-box neural networks erodes operator trust.
- Conflation of real grid sags with sensor faults creates catastrophic delays in grid voltage regulation.

---

## 3. Project Objectives & Scope

- **In Scope (Prototype Deliverables):**
  - Working single-node prototype monitoring 30 smart meters on a radial distribution feeder ($50\text{m} \to 600\text{m}$).
  - 13 injected anomaly scenarios catalogued with ground-truth labels.
  - Multi-evidence composite confidence engine ($C \in [0.0, 1.0]$) and dual-layer explainability (SHAP + Jinja2 templates).
  - Asynchronous Multi-Agent RAG Remediation Swarm grounded in IEEE 1547, IEC 61850, and STEG grid code.
  - Live 2-node networked Noosphere testbed across local ports exchanging dimensionless disturbance signatures.
  - Single-Pane Operator Cockpit (React 18 + Tailwind) optimized for a 3-minute pitch.
- **Out of Scope:** Direct live physical connection to STEG high-voltage substations or non-simulated utility billing networks.

---

## 4. System Architecture Overview: The Two-Speed Engine

Presents the end-to-end data pipeline and block diagram:
1. **⚡ Fast-Path (Sub-50ms):** Telemetry Streaming $\to$ Modules 1–5 Physics Residuals & Spatial Consensus $\to$ Module 6 5-Class Classifier $\to$ Module 7 Composite Confidence $\to$ Module 8 SHAP $\to$ Module 9 3-Tier Governance $\to$ Emergency Trip / Rapid Regulation.
2. **🧠 Slow-Path (Asynchronous 2–4s):** Module 10 Audit Log Event Trigger $\to$ Agent 1 Diagnostic Synthesizer $\to$ Agent 2 RAG Retrieval (ChromaDB) $\to$ Agent 3 Remediation Planner $\to$ Agent 4 Safety Auditor $\to$ Cockpit Advisory Drawer $\to$ Agent 5 Feedback Learner $\to$ Module 16 Noosphere Registry.

---

## 5. Four Mandatory Pillars

### 5.1 Pillar 1 — Anomaly & Bias Detection
Detailed breakdown of the 5 parallel evidence engines:
- Module 1: Rolling Z-score, EWMA, CUSUM, Page-Hinkley drift tracking.
- Module 2: Unsupervised Isolation Forest (160 estimators, contamination $\approx 0.03$).
- Module 3: Line Impedance drop residuals ($|V_{\text{measured}} - V_{\text{expected}}|$) and sensor health indices ($0\text{–}100$).
- Module 4: Zero-variance run length, physical boundaries, and replay hash checks.
- Module 5: Feeder sag consensus ratio (`feeder_sag_ratio`) and household cohort ratios.

### 5.2 Pillar 2 — Confidence Scores & Explainability
- Composite confidence formula: $C = 0.35 P(\text{class}) + 0.25 (\text{Consensus}) + 0.20 (\text{Agreement}) + 0.10 (\text{Health}) + 0.10 (1 - \text{Residual})$.
- Dual explainability: Local SHAP `TreeExplainer` feature attributions for engineers + deterministic Jinja2 natural language templates for grid operators.

### 5.3 Pillar 3 — Human-AI Escalation & Governance
- 3 operational tiers: `AUTO_ACTION` ($C \ge 0.95$), `OPERATOR_APPROVAL` ($0.70 \le C < 0.95$), `HUMAN_INVESTIGATION` ($C < 0.70$).
- Concrete safeguards fighting automation complacency and alert fatigue.

### 5.4 Pillar 4 — Shared Learning Across the Noosphere
- Privacy-preserving collective defense: only dimensionless mathematical descriptors ($PF < 0.65$, consensus ratios) leave the node. Raw load profiles stay local.
- Working multi-node local testbed demonstrating cross-node signature exchange.

---

## 6. Technology Stack

- **Core & ML:** Python 3.11, NumPy, SciPy, pandas, scikit-learn, XGBoost, SHAP.
- **RAG & Agents:** LiteLLM (Gemini / OpenAI / local Ollama Llama-3), ChromaDB (embedded in-memory vector store).
- **Backend & Streaming:** FastAPI, Uvicorn, WebSockets, Pydantic v2, SQLAlchemy, SQLite/PostgreSQL.
- **Frontend & Cockpit:** React 18, TypeScript, TailwindCSS, Recharts, Plotly.js, Lucide Icons.
- **Validation & DevOps:** Pytest, Docker, Docker Compose, Nginx.

---

## 7. Development Phases & 8-Week Agile Roadmap

Structured around 4 two-week agile sprints with full-team pair programming in strict dependency order:
- **Sprint 1 (Weeks 1–2):** ML Trust Core & Evidence Engines (Modules 2, 3, 4, 5).
- **Sprint 2 (Weeks 3–4):** Classifier, Composite Confidence, SHAP & Asynchronous RAG Swarm (Modules 6, 7, 8, 11).
- **Sprint 3 (Weeks 5–6):** FastAPI Streaming Backend & Single-Pane Cockpit UI (Modules 9, 10, 12, 13).
- **Sprint 4 (Weeks 7–8):** Automated Evaluation Suite, 2-Node Docker Demo & Pitch Rehearsal (Modules 14, 15, 16, Business Model).

---

## 8. Dataset & 13-Scenario Simulation Strategy

- Generates 30 households along a 600m radial feeder at 1-minute intervals.
- Ground truth coverage across all 4 challenge categories:
  - Demand Events: `consumption_spike`
  - Data Quality: `meter_drift`, `constant_bias`, `energy_power_mismatch`
  - Data Integrity & Comms: `frozen_meter`, `random_corruption`, `missing_data`, `dropout`
  - Falsification & Cyber-Physical Attacks: `false_data_injection`, `replay_like`, `bias_injection` (stealth theft)
  - Real Electrical Events: `equipment_fault`, `grid_event` (feeder-wide 18V sag)

---

## 9. Evaluation Metrics & Automated Benchmarking Suite

Detailed specifications for Module 14:
- **Detection Precision & Recall:** Precision $\ge 96.5\%$, Recall $\ge 98.0\%$, False Positive Rate $< 1.2\%$.
- **Latency Benchmarks:** Fast-Path Latency $< 50\text{ ms}$ (p99); Slow-Path Latency $< 3.5\text{ s}$ (p95).
- **Explanation Quality:** SHAP Faithfulness $> 92\%$ alignment with injected physics; Readability Flesch-Kincaid $\le 9$.

---

## 10. Human-AI Governance Model: Addressing Over-Trust & Under-Trust

- **Over-Trust Mitigation:**
  - *Spot-Check Audit Policy:* Configurable daemon randomly demotes **5% of `AUTO_ACTION` decisions** to `OPERATOR_APPROVAL`.
  - *Cognitive Friction:* High-impact actions require clicking and acknowledging the primary SHAP driver before execution.
- **Under-Trust Mitigation:**
  - *Consensus Noise-Gate:* Uncorroborated low-severity blips clustered into maintenance batches, reducing sirens by $>90\%$.
  - *Physics Proof Cards:* Visual representation of voltage consistency residual verifying that sensor failure was ruled out.

---

## 11. Multi-Node / Noosphere Federated Collective Defense

- Mathematical pattern schema (`pattern_registry.json`).
- Live 2-node simulation (`Node-Tunis-Nord` and `Node-Sfax-Sud`).
- Federated consensus threshold ($\ge 2$ nodes) to promote local patterns to global defense rules.

---

## 12. Single-Pane Operator Cockpit Design

Unified React interface designed for a 3-minute pitch:
- **Zone 1:** Live Feeder Topology & Impedance Drop Curves ($V_{\text{measured}}$ vs $V_{\text{expected}}$).
- **Zone 2:** Incident Drill-Down Drawer with SHAP Waterfall and RAG Remediation Plan.
- **Zone 3:** Noosphere Collective Defense Strip.

---

## 13. Business Scope & Techno-Economic Model (STEG Context) — 1 Bonus Point

- **Target Pilot:** 100,000 smart meters in District Tunis-Nord.
- **Financial Projections:** 3-Year Total Cost of $229,000 ($145k CapEx Year 1 + $42k/yr OpEx).
- **Theft Recovery Payback:** Recovers 15% of distribution theft losses ($\approx \$210,000\text{/year}$), achieving full payback in **13.1 months** (<14 mo.) and net savings of **$401,000** over 3 years.

---

## 14. Team Workload & Pair-Programming Execution Flow

- 5-person agile team working in sequential dependency pairs rather than isolated silos.
- Continuous integration and automated regression testing on every module.

---

## 15. Risk Analysis & Mitigation Matrix

Addresses data leakage, real-time latency traps, multi-agent hallucination risks, demo timing limits, and utility adoption hurdles.

---

## 16. References & Standards

- IEEE 1547-2018, IEC 61850, IEC 62351, STEG Low-Voltage Distribution Code, DLMS/COSEM Green Book.
