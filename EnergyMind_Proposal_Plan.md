# EnergyMind Tunisia — Project Proposal Plan
### TSYP / IEEE Challenge Submission

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Project Objectives & Scope](#3-project-objectives--scope)
4. [System Architecture Overview](#4-system-architecture-overview)
5. [Four Mandatory Pillars](#5-four-mandatory-pillars)
6. [Technology Stack](#6-technology-stack)
7. [Development Phases & Timeline](#7-development-phases--timeline)
8. [Dataset & Simulation Strategy](#8-dataset--simulation-strategy)
9. [Evaluation Metrics](#9-evaluation-metrics)
10. [Human-AI Governance Model](#10-human-ai-governance-model)
11. [Multi-Node / Noosphere Design](#11-multi-node--noosphere-design)
12. [Team Roles & Responsibilities](#12-team-roles--responsibilities)
13. [Risk & Mitigation](#13-risk--mitigation)
14. [References / Bibliography](#14-references--bibliography)

---

## 1. Executive Summary

> **One-page pitch for the judges.**

A concise, high-impact overview of EnergyMind Tunisia: what it is, the core problem it solves, why a *trust layer* approach is novel and necessary, and the key differentiator (hybrid AI + explainability + governance in a single pipeline). Ends with a statement of readiness and team commitment.

---

## 2. Problem Statement

> **Why does this problem matter?**

Describes the gap between raw energy sensor data and trustworthy automated decisions: sensors can drift, be biased, be falsified, or fail — yet current systems treat all data as equally reliable. Explains the real-world consequences (wrong automated actions, missed faults, eroded operator trust) and frames the challenge's four pillars as a direct response to this gap.

---

## 3. Project Objectives & Scope

> **What will EnergyMind do, and what is out of scope?**

Lists the concrete, measurable goals of the project aligned with the four mandatory pillars. Defines the boundary of the single-node prototype (in scope) vs. full multi-node deployment (designed but not implemented). States the three demonstration scenarios (genuine grid event, sensor bias, falsified data) as the acceptance criteria.

---

## 4. System Architecture Overview

> **How does the system fit together end-to-end?**

Presents the full pipeline: Data Ingestion → Validation → Feature Engineering → Parallel Detectors (Anomaly / Bias-Drift / Fault) → Evidence Fusion → Event Classification → Confidence Engine → Explainability Layer → Governance Engine → Dashboard & Audit Log. Includes a high-level block diagram and explains the data flow in plain language.

### 4.1 Data Ingestion Layer
### 4.2 Feature Engineering Layer
### 4.3 Detection Engine (three parallel tracks)
### 4.4 Evidence Fusion & Event Classification
### 4.5 Confidence & Explainability Layer
### 4.6 Governance Engine
### 4.7 Operator Dashboard & Audit Log

---

## 5. Four Mandatory Pillars

> **Deep-dive into each challenge requirement.**

Each sub-section explains the design choice, the algorithm(s) selected, and how it contributes to the overall trust layer.

### 5.1 Pillar 1 — Anomaly & Bias Detection
Covers the hybrid statistical + unsupervised ML approach: rolling z-score, Isolation Forest, EWMA/CUSUM for drift, and residual analysis for persistent sensor bias. Explains why a single model is insufficient.

### 5.2 Pillar 2 — Confidence Scores & Explainability
Describes the composite confidence score (combining anomaly score, bias score, model probability, rule evidence, and sensor health) and the dual explainability engine (SHAP for tree models + rule-backed human-readable reasoning).

### 5.3 Pillar 3 — Human-AI Escalation & Governance
Outlines the three-tier confidence thresholds (≥95 % auto-action / 70–95 % operator approval / <70 % human investigation) and the operator override interface (approve, reject, comment, mark FP/TP).

### 5.4 Pillar 4 — Shared Learning Across the Noosphere
Explains the federated/knowledge-sharing design: only anomaly patterns, model updates, and aggregate statistics cross node boundaries; raw data remains local. Describes how human feedback drives continuous model improvement.

---

## 6. Technology Stack

> **What we build with and why.**

Presents the chosen stack in a layered table (Language / ML / Deep Learning / Explainability / Backend / Real-time / Database / Frontend / Charts / Simulation / Containerization / Testing) and provides a one-sentence justification for each major choice. Highlights why certain technologies (Kafka, Redis, MQTT) were intentionally deferred to avoid over-engineering.

---

## 7. Development Phases & Timeline

> **How we go from zero to a working prototype.**

Breaks the project into seven sequential phases with estimated duration and deliverables for each.

### Phase 1 — Dataset & Anomaly Injection
Build synthetic baselines and the anomaly generator (bias, drift, spikes, dropouts, falsification, faults) with full metadata for evaluation.

### Phase 2 — Detection Engine
Implement all detector tracks: statistical baseline, Isolation Forest, bias/drift detectors, data-integrity checks.

### Phase 3 — Event Classification
Train and validate the event classifier (genuine grid event vs. data problem vs. sensor failure vs. falsification) using XGBoost / Random Forest.

### Phase 4 — Trust Layer (Confidence + Explainability)
Build the composite confidence score and the SHAP + rule-backed explanation engine; wire into the audit log.

### Phase 5 — Governance Engine
Implement threshold routing (auto / approval / escalation), human override interface, and feedback collection.

### Phase 6 — Operator Dashboard
Develop the React frontend: Command Center, Live Monitoring, Event Investigation, Sensor Health, AI Decision Center, Audit Center, and Simulation Center.

### Phase 7 — Integration, Testing & Demo Scenarios
End-to-end integration, Dockerization, Pytest coverage, and preparation of the three judging scenarios.

---

## 8. Dataset & Simulation Strategy

> **How we generate and manage labeled data.**

Explains the synthetic anomaly generator design (clean baseline → injection → labeled dataset with anomaly metadata). Describes the dataset directory structure (`/raw`, `/clean`, `/anomalies`, `/processed`, `/train`, `/val`, `/test`) and the metadata schema (source, sampling rate, features, units, anomaly generation parameters, train/test split). Addresses why synthetic data is acceptable and how it is evaluated.

---

## 9. Evaluation Metrics

> **How we prove the system works.**

Lists the metrics used across four domains:
- **Classification**: Precision, Recall, F1-score, ROC-AUC, PR-AUC
- **Detection**: Detection rate, False alarm rate, Detection delay
- **Explainability**: Human-rated explanation quality, rule coverage
- **Operational**: Inference latency, throughput, CPU/RAM usage

Describes how the three demonstration scenarios act as qualitative acceptance tests for the judges.

---

## 10. Human-AI Governance Model

> **Defining the boundary between AI autonomy and human authority.**

Details the configurable threshold system (not hard-coded), the governance rule engine (YAML-based configuration), the three escalation paths, and the complete audit log schema (Event ID, timestamp, sensor, detection, confidence, reasons, model version, rules triggered, recommendation, human decision, final outcome). Emphasizes the principle: *critical events always go to a human*.

---

## 11. Multi-Node / Noosphere Design

> **Architecture for cross-node learning (documented, not fully implemented in prototype).**

Describes the three sharing options (centralized aggregation, federated learning, knowledge pattern registry) and the privacy boundary: raw measurements and customer data never leave the node. Presents the Pattern Registry schema (pattern ID, type, signature, observed count, confidence, recommendation). Marks clearly what is implemented vs. what is a documented design.

---

## 12. Team Roles & Responsibilities

> **Who does what on a 4–6 person team.**

Maps each team member to a primary role and secondary contributions:

| Role | Responsibilities |
|---|---|
| ML / Data Lead | Anomaly detection, bias/drift models, model evaluation, SHAP |
| Backend Lead | FastAPI, WebSockets, governance engine, audit log, database |
| Frontend Lead | React dashboard, real-time charts, decision center UI |
| Data / Simulation Engineer | Synthetic generator, dataset pipeline, feature engineering |
| DevOps / Integration | Docker, CI, end-to-end wiring, test coverage |
| *(if 6th member)* Research / Docs | Architecture docs, Noosphere design, proposal writing |

---

## 13. Risk & Mitigation

> **What could go wrong and how we handle it.**

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Insufficient labeled data | High | High | Synthetic generator is the primary data source |
| Model over-fits synthetic anomalies | Medium | High | Hold-out test set; diverse injection parameters |
| Real-time latency too high | Medium | Medium | Profile early; optimize feature engineering |
| Dashboard not ready for demo | Medium | High | Replay/simulation mode as fallback |
| Scope creep (too many optional features) | High | Medium | Strict "Must Have" lock; defer to Phase 7 |
| Team member unavailability | Low | High | Cross-training; shared documentation |

---

## 14. References / Bibliography

> **Sources, datasets, tools, and standards cited in the proposal.**

Includes references to:
- IEEE challenge specification documents
- Key papers: Isolation Forest (Liu et al.), SHAP (Lundberg & Lee), CUSUM, Federated Learning (McMahan et al.)
- Open datasets used for baseline generation (e.g., EPFL Smart Meter, UKPN, synthetic utilities)
- Technology documentation: FastAPI, scikit-learn, XGBoost, React, Docker
- Relevant energy-sector standards (IEC 61850, IEC 62351 if applicable)

---

*Document version 0.1 — EnergyMind Tunisia Team — October 2026*
