# EnergyMind Tunisia — Complete Feature & Architecture Specification

## 1. Project Objective

**EnergyMind Tunisia** is an AI-driven **trust layer for energy systems**.

Its position is:

```text
RAW ENERGY DATA
      ↓
┌─────────────────────────────┐
│      ENERGYMIND TRUST       │
│           LAYER             │
│                             │
│  Anomaly & Bias Detection   │
│  Confidence & Explainability│
│  Human-AI Governance        │
│  Shared Learning            │
└─────────────────────────────┘
      ↓
SAFE / TRUSTED DECISION
      ↓
AUTOMATED ACTION or HUMAN REVIEW
```

The challenge requires the system to determine whether incoming energy data represents:

- A genuine grid/equipment event
- A degraded or faulty sensor
- A biased reading
- Corrupted/falsified data
- Another anomaly

The system must also explain its decisions, provide confidence, maintain an audit trail, and define when AI can act independently versus when a human must approve an action.

---

# 2. Core Challenge Requirements

EnergyMind has four mandatory pillars:

1. **Anomaly & Bias Detection**
2. **Confidence Scores & Explainability**
3. **Human-AI Escalation & Governance**
4. **Shared Learning Across the Noosphere**

A working **single-node prototype is required**.

Multi-node sharing can remain a documented architecture/design if it is not implemented in the prototype.

---

# 3. Recommended System Architecture

## Recommended Overall Architecture

For a student competition prototype, the recommended architecture is:

```text
                  ┌──────────────────────┐
                  │ Energy Data Sources  │
                  │                      │
                  │ Smart Meters         │
                  │ Voltage / Current    │
                  │ Power Quality        │
                  │ IoT Sensors          │
                  │ Simulated Grid Data  │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Data Ingestion Layer │
                  │                      │
                  │ Validation            │
                  │ Timestamping          │
                  │ Normalization         │
                  │ Quality Checks        │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Feature Engineering  │
                  │                      │
                  │ Temporal Features    │
                  │ Statistical Features │
                  │ Correlations         │
                  │ Residuals            │
                  └──────────┬───────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │ Anomaly    │ │ Bias /     │ │ Equipment  │
       │ Detection  │ │ Sensor     │ │ Fault      │
       │ Engine     │ │ Health     │ │ Detection  │
       └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Event Classification │
                 │                      │
                 │ Genuine Grid Event   │
                 │ Data Quality Problem │
                 │ Sensor Failure       │
                 │ Falsified Data       │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Confidence Engine    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Explainability Layer │
                 │                      │
                 │ SHAP / LIME / Rules  │
                 │ Decision Explanation │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Governance Engine    │
                 │                      │
                 │ Auto-action          │
                 │ Human approval       │
                 │ Escalation           │
                 └───────┬───────┬──────┘
                         │       │
                   Auto  │       │ Human
                   Action│       │ Review
                         ▼       ▼
                 ┌──────────────────────┐
                 │ Operator Dashboard   │
                 │ Alerts / Override    │
                 │ Audit Log            │
                 └──────────────────────┘
```

---

# 4. FEATURE SET

# FEATURE 1 — Data Ingestion

## Purpose

Collect incoming energy-system measurements.

## Supported data

The challenge explicitly mentions:

- Voltage
- Current
- Power Quality
- Smart-meter readings
- Grid/equipment data

## Features

- CSV ingestion
- Streaming/simulated streaming
- Sensor ID
- Timestamp
- Location/node ID
- Measurement type
- Measurement value
- Optional equipment metadata

## Architecture options

### A. Batch architecture

```text
CSV → Python → Processing → ML
```

Best for:
- Phase 1
- Fast prototyping
- Kaggle notebooks

### B. Streaming architecture

```text
Sensor
  ↓
MQTT / WebSocket
  ↓
FastAPI
  ↓
Processing Pipeline
  ↓
ML
```

Best for:
- Final demo
- Real-time monitoring

### C. Message-broker architecture

```text
Sensors
   ↓
MQTT / Kafka
   ↓
Message Broker
   ↓
Detection Services
```

Best for:
- More realistic architecture
- Future multi-node deployment

---

# FEATURE 2 — Data Validation & Quality Checking

Before AI analyzes data, verify that the data itself is structurally valid.

## Checks

- Missing values
- Duplicate timestamps
- Impossible values
- Out-of-range measurements
- Invalid sensor IDs
- Timestamp inconsistencies
- Communication gaps
- Sudden data disappearance

## Architecture

```text
Raw Data
   ↓
Schema Validation
   ↓
Range Validation
   ↓
Missing Data Detection
   ↓
Timestamp Validation
   ↓
Clean / Suspicious
```

## Implementation options

- Python/Pandas
- Pydantic
- Great Expectations
- Custom rule engine

---

# FEATURE 3 — Anomaly Detection

## Objective

Detect measurements or patterns that differ significantly from expected behavior.

The challenge suggests:

- Isolation Forest
- Autoencoders
- One-Class SVM
- Statistical outlier methods

## Architecture A — Statistical

```text
Measurement
     ↓
Rolling Mean / Median
     ↓
Deviation
     ↓
Z-score
     ↓
Threshold
     ↓
Anomaly
```

Advantages:
- Easy to explain
- Fast
- Good baseline

## Architecture B — Isolation Forest

```text
Features
   ↓
Isolation Forest
   ↓
Anomaly Score
   ↓
Threshold
   ↓
Anomaly / Normal
```

Advantages:
- Good unsupervised baseline
- No anomaly labels required

## Architecture C — Autoencoder

```text
Input
  ↓
Encoder
  ↓
Latent Representation
  ↓
Decoder
  ↓
Reconstructed Signal
  ↓
Reconstruction Error
  ↓
Anomaly Score
```

Advantages:
- Good for complex temporal patterns
- Stronger deep-learning option

## Architecture D — One-Class SVM

```text
Normal Training Data
       ↓
One-Class SVM
       ↓
Decision Boundary
       ↓
Normal / Anomaly
```

---

# FEATURE 4 — BIAS DETECTION

## Objective

Detect sensors that systematically report measurements that are shifted away from expected/reference behavior.

Bias is different from a single abnormal reading.

Example:

```text
Expected: 230 V

Sensor:
238 V
237 V
239 V
238 V
238 V
```

The individual values may appear plausible, but the persistent offset indicates potential sensor bias.

## Recommended architecture

```text
Sensor Reading
      ↓
Expected Value Estimation
      ↓
Residual = Observed - Expected
      ↓
Rolling Bias Estimation
      ↓
Persistence Check
      ↓
Bias Score
      ↓
Bias Detected?
```

## Possible expected-value sources

### Option A — Historical baseline

```text
Current Value
     ↓
Historical Average
     ↓
Residual
```

### Option B — Neighboring sensors

```text
Sensor A ─┐
Sensor B ─┼→ Reference Estimate
Sensor C ─┘
              ↓
        Compare Target
```

### Option C — Physics/model-based reference

Use known electrical relationships to estimate expected measurements.

### Option D — ML prediction

```text
Historical Measurements
        ↓
Prediction Model
        ↓
Expected Value
        ↓
Observed - Expected
        ↓
Bias
```

## Useful methods

- Rolling mean
- Rolling median
- EWMA
- Z-score
- Residual analysis
- Sensor correlation
- Kalman filtering
- Regression
- Isolation Forest
- Change-point detection

---

# FEATURE 5 — Sensor Drift Detection

Sensor drift is a gradual change in sensor behavior.

Example:

```text
Normal
230 → 231 → 232 → 234 → 236 → 238
                          ↑
                       Drift
```

## Architecture

```text
Historical Signal
      ↓
Trend Estimation
      ↓
Drift Detection
      ↓
Persistence Check
      ↓
Sensor Health Score
```

## Algorithms

- Moving average
- EWMA
- CUSUM
- Page-Hinkley
- Change-point detection
- Kalman filter
- Regression trend analysis

---

# FEATURE 6 — Equipment Fault Detection

The system should detect actual equipment problems separately from data problems.

## Examples

- Equipment failure
- Electrical fault
- Abnormal operating condition
- Natural equipment failure

## Important distinction

```text
Abnormal Voltage
      │
      ├── Real grid event?
      │
      └── Sensor/data problem?
```

## Architecture

```text
Measurements
     ↓
Feature Extraction
     ↓
Fault Classifier
     ↓
Fault Type
     ↓
Confidence
```

## Model options

### Supervised

- Random Forest
- XGBoost
- LightGBM
- SVM
- Neural Network

### Time-series

- LSTM
- GRU
- 1D CNN
- Temporal CNN
- Transformer

---

# FEATURE 7 — Falsified / Corrupted Data Detection

The system should detect readings that may be intentionally manipulated or corrupted.

The challenge explicitly allows synthetic falsified readings for dataset generation.

## Examples

### Random corruption

```text
230
231
999
229
230
```

### Constant-value attack

```text
230
230
230
230
230
```

### Bias injection

```text
230
238
239
237
238
```

### Replay attack

Old measurements are repeatedly sent as if they were current.

## Detection architecture

```text
Incoming Data
      ↓
Integrity Checks
      ↓
Temporal Consistency
      ↓
Cross-Sensor Consistency
      ↓
Statistical Detection
      ↓
Anomaly Model
      ↓
Data Integrity Score
```

---

# FEATURE 8 — Genuine Grid Event vs Data-Quality Problem

This is one of the most important features.

The system must distinguish:

```text
            ABNORMAL READING
                  │
          ┌───────┴────────┐
          ↓                ↓
   REAL GRID EVENT    DATA PROBLEM
          │                │
    Real surge        Sensor bias
    Real outage       Sensor drift
    Real fault        Corrupted data
                       Falsified data
```

## Recommended architecture

Use a **multi-signal evidence engine**.

```text
Anomaly Detector ─────┐
Bias Detector ────────┤
Sensor Health ────────┤
Neighbor Correlation ─┤
Equipment Model ──────┤
Temporal Analysis ────┤
                      ▼
              Evidence Fusion
                      ↓
              Event Classifier
                      ↓
          ┌───────────┴───────────┐
          ↓                       ↓
   Genuine Grid Event      Data-Quality Problem
```

## Architecture options

### Rule-based

Best for explainability.

### ML classifier

Use:

- Random Forest
- XGBoost
- Logistic Regression

### Hybrid

Recommended:

```text
ML Scores + Rules + Sensor Health
             ↓
        Evidence Fusion
             ↓
         Final Verdict
```

---

# FEATURE 9 — Confidence Score

Every important detection should have a confidence score.

Example:

```text
VERDICT
Sensor Bias Detected

Confidence
██████████████████░░ 91%

Reasons:
+ Persistent offset
+ Neighbor sensors disagree
+ No corresponding grid event
```

## Architecture

Confidence can combine:

```text
Anomaly Score
Bias Score
Model Probability
Rule Evidence
Sensor Health
Cross-Sensor Agreement
```

into:

```text
Final Confidence Score
```

## Important

Confidence should not simply mean:

> "The neural network says 91%."

It should ideally represent combined evidence that can be inspected.

---

# FEATURE 10 — Explainability

The challenge requires a human-understandable verdict.

The system should answer:

> **What happened?**

> **Why did the system believe it?**

> **Which measurements influenced the decision?**

> **What should the operator do?**

## Explainability options

### SHAP

Best for:
- Tree models
- Feature importance
- Individual predictions

### LIME

Best for:
- Local explanations
- Model-agnostic explanations

### Rule-backed explanations

Example:

```text
BIAS DETECTED BECAUSE:

• Sensor offset = +7.8 V
• Persistent for 12 minutes
• Neighboring sensors remain normal
• No corresponding grid event detected
```

### Recommended architecture

```text
Prediction
    ↓
Explainability Engine
    ├── SHAP
    ├── Rules
    └── Supporting Evidence
             ↓
      Human-readable explanation
```

The challenge specifically encourages SHAP, LIME, rule-backed models, interpretable ensembles, and readable decision logs. 

---

# FEATURE 11 — Decision / Audit Log

Every AI decision should be recorded.

## Log structure

```text
Event ID
Timestamp
Sensor
Input values
Detected anomaly
Classification
Confidence
Reasons
Model version
Rules triggered
Recommended action
Human decision
Final outcome
```

## Example

```text
EVENT #1042

10:31:24
Sensor: S-17
Parameter: Voltage

Detection:
Sensor Bias

Confidence:
94%

Evidence:
+8.2 V persistent offset
Neighbor sensors normal
No grid-wide disturbance

Recommendation:
Inspect sensor

Human action:
Approved

Model:
bias-detector-v1.3
```

This creates traceability and supports post-event auditing.

---

# FEATURE 12 — Human-AI Escalation

The AI must know when it can act and when it must ask a human.

The challenge explicitly requires thresholds for automatic corrective actions and situations requiring human approval.

## Recommended three-level architecture

```text
                  Detection
                     ↓
                Confidence
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
      HIGH         MEDIUM         LOW
        ↓            ↓            ↓
   Auto-action   Human review   Escalate
```

Example:

```text
Confidence ≥ 95%
    → automatic low-risk action

70–95%
    → operator approval

<70%
    → human investigation
```

Thresholds should be configurable rather than hard-coded.

---

# FEATURE 13 — Human Override

The operator must be able to:

- Approve AI recommendation
- Reject recommendation
- Override automated action
- Request more information
- Mark detection as true/false positive
- Add a comment

## Architecture

```text
AI Recommendation
       ↓
Operator Dashboard
   ┌───┴────┐
 Approve   Reject
   │         │
   └────┬────┘
        ↓
    Audit Log
```

---

# FEATURE 14 — Operator Dashboard

The dashboard is the main human interface.

## Main sections

### System Health

```text
Sensors:       98%
Healthy:       91
Warning:        5
Critical:       2
```

### Live Events

```text
10:31 Sensor Bias        94%
10:29 Grid Event         89%
10:25 Sensor Drift       87%
```

### Event Detail

Show:

- Signal graph
- Expected vs actual
- Anomaly score
- Confidence
- Explanation
- Recommended action
- Approve / Reject / Override

### Sensor Health Map

```text
GREEN   Healthy
YELLOW  Suspicious
RED     Faulty
```

---

# FEATURE 15 — Real-Time Monitoring

For the final prototype, a live stream makes the system much more convincing.

## Architecture

```text
Simulator
   ↓
WebSocket / MQTT
   ↓
Backend
   ↓
Detection Engine
   ↓
WebSocket
   ↓
Dashboard
```

Possible technologies:

- FastAPI
- WebSockets
- MQTT
- Redis
- Kafka

For a student prototype, **FastAPI + WebSockets** is sufficient.

---

# FEATURE 16 — Alerting

Alerts should be generated for important events.

## Alert types

- Critical sensor fault
- Strong bias
- Data corruption
- Equipment anomaly
- Low confidence
- Multiple sensors failing
- Potential falsification

## Channels

Prototype:

- Dashboard notification
- Browser notification

Optional:

- Email
- SMS
- Telegram

---

# FEATURE 17 — Synthetic Anomaly Generator

This is extremely important because the challenge expects simulation due to the limited availability of labeled real fault data.

The challenge explicitly permits:

- Synthetic faults
- Sensor drift
- Biased readings
- Falsified readings

## Generator

```text
Clean Baseline
      ↓
┌─────────────────────────┐
│ Anomaly Injection       │
│                         │
│ Bias                    │
│ Drift                   │
│ Noise                   │
│ Spike                   │
│ Dropout                 │
│ Falsification           │
│ Equipment Fault         │
└────────────┬────────────┘
             ↓
       Labeled Dataset
```

## Important

Every injected anomaly should have metadata:

```text
anomaly_type
sensor_id
start_time
end_time
severity
injection_parameters
```

This allows proper evaluation.

---

# FEATURE 18 — Dataset Management

The project should maintain:

```text
/raw
/clean
/anomalies
/processed
/train
/validation
/test
```

Dataset metadata should document:

- Source
- Sampling rate
- Features
- Units
- Missing values
- Anomaly generation process
- Train/test split

---

# FEATURE 19 — Model Management

Store:

- Model
- Version
- Training dataset
- Features
- Hyperparameters
- Metrics
- Date trained

Example:

```text
models/
├── anomaly_detector_v1.pkl
├── bias_detector_v1.pkl
├── fault_classifier_v2.pkl
└── metadata.json
```

---

# FEATURE 20 — Model Evaluation

The challenge explicitly evaluates:

- Detection precision/recall
- False-positive rate
- Explanation quality
- Response latency

## Additional useful metrics

### Classification

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC

### Detection

- Detection rate
- False alarm rate
- Detection delay

### Operational

- Inference latency
- Throughput
- CPU/RAM usage

---

# FEATURE 21 — Multi-Node / Noosphere Learning

This is the fourth challenge goal.

Different nodes can represent:

```text
Factory
Neighborhood
Microgrid
Energy site
```

They should potentially share:

- Anomaly patterns
- Calibration insights
- Relevant knowledge

while protecting local/private data.

The challenge allows multi-node sharing to remain a documented design for the prototype.

---

# FEATURE 22 — Privacy Architecture

The system should explicitly define:

```text
LOCAL DATA
    │
    ├── Raw measurements
    ├── Customer information
    └── Sensitive metadata

        NOT SHARED

SHARED KNOWLEDGE
    │
    ├── Anomaly pattern
    ├── Model parameters
    ├── Calibration insight
    └── Aggregated statistics
```

## Architecture options

### Centralized

```text
Node A ─┐
Node B ─┼→ Central Server
Node C ─┘
```

### Federated Learning

```text
          Global Model
          /    |    \
         ↓     ↓     ↓
      Node A Node B Node C
         │     │     │
       Local Local Local
      Training Training
```

### Knowledge sharing

Instead of sharing raw data, nodes exchange:

- Anomaly signatures
- Model updates
- Statistical patterns
- Calibration information

---

# FEATURE 23 — Knowledge / Pattern Registry

Optional but valuable for the Noosphere concept.

Store known patterns:

```text
Pattern ID
Pattern type
Characteristics
Origin node
Confidence
Date discovered
Affected equipment
Recommended response
```

Example:

```text
PATTERN-027

Type:
Sensor Bias

Signature:
Persistent +5–10% deviation

Observed:
12 times

Confidence:
92%

Recommendation:
Calibration inspection
```

---

# FEATURE 24 — Feedback Learning

Human decisions can become future training data.

```text
AI Detection
     ↓
Human Review
     ↓
True Positive / False Positive
     ↓
Feedback Dataset
     ↓
Model Retraining
     ↓
Improved Detector
```

This creates a continuous improvement loop.

---

# FEATURE 25 — Configuration / Rules Engine

Thresholds should not be buried inside code.

Example:

```yaml
confidence:
  automatic: 0.95
  human_review: 0.70

bias:
  voltage_threshold: 5
  persistence_minutes: 10

sensor:
  missing_data_timeout: 30

escalation:
  critical_events: always_human
```

This makes the system configurable and auditable.

---

# FEATURE 26 — Health Score

Each sensor can have a continuously updated health score.

Example:

```text
SENSOR S-17

Health: 72 / 100

Bias:        -15
Drift:       -5
Missing:     -3
Correlation: -5

Status: WARNING
```

This provides an easy dashboard-level representation.

---

# FEATURE 27 — System Risk Score

An overall site/grid risk indicator can combine:

```text
Sensor Health
+
Active Anomalies
+
Equipment Faults
+
Data Integrity
+
Confidence
```

Output:

```text
SYSTEM RISK

LOW       0–30
MEDIUM   31–60
HIGH     61–80
CRITICAL 81–100
```

This is an optional presentation feature, not explicitly required by the challenge.

---

# FEATURE 28 — Event Timeline

Every incident should be reconstructed chronologically.

```text
10:20 Normal
10:24 Sensor drift begins
10:27 Bias detected
10:28 Confidence reaches 91%
10:29 Human review requested
10:31 Operator confirms
10:35 Sensor isolated
```

This is extremely useful for explainability and auditing.

---

# FEATURE 29 — Replay / Simulation Mode

For demonstrations:

```text
Select Scenario
      ↓
Normal Grid
Sensor Bias
Sensor Drift
Equipment Fault
False Data
      ↓
Play
      ↓
Live Dashboard
```

This lets judges see the entire detection pipeline in real time.

---

# FEATURE 30 — Scenario Comparison

Allow the user to compare:

```text
REAL GRID EVENT

vs.

SENSOR BIAS

vs.

FALSIFIED DATA
```

The dashboard can show why the AI classified each case differently.

This directly demonstrates the central challenge requirement.

---

# 5. MODEL ARCHITECTURE OPTIONS

There is no requirement to use a single AI model.

A strong solution can use a **hybrid architecture**.

## Architecture 1 — Pure Rule-Based

```text
Data
 ↓
Rules
 ↓
Detection
```

### Advantages

- Extremely explainable
- Easy to implement
- Easy to audit

### Disadvantages

- Limited adaptability
- Harder to detect unknown patterns

Use as a baseline, not necessarily as the final architecture.

---

# 6. ARCHITECTURE 2 — Classical Machine Learning

```text
Data
 ↓
Feature Engineering
 ↓
ML Model
 ↓
Prediction
```

Possible models:

- Random Forest
- XGBoost
- LightGBM
- SVM
- Logistic Regression
- Isolation Forest
- One-Class SVM

### Recommended for

A reliable competition prototype with limited training data.

---

# 7. ARCHITECTURE 3 — Deep Learning

```text
Time-Series
     ↓
Sequence Model
     ↓
Anomaly / Fault
     ↓
Prediction
```

Possible models:

- Autoencoder
- LSTM
- GRU
- 1D CNN
- CNN-LSTM
- Transformer

Use when the dataset is large enough.

---

# 8. ARCHITECTURE 4 — Hybrid AI

## Recommended

```text
                  DATA
                    ↓
            Feature Engineering
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
     Rules      ML Model    Statistical
        │           │           │
        └───────────┼───────────┘
                    ↓
             Evidence Fusion
                    ↓
              Final Verdict
                    ↓
          Confidence + Explanation
                    ↓
             Governance Engine
```

### Why this is recommended

It combines:

- ML adaptability
- Statistical detection
- Rule-based safety
- Explainability
- Human oversight

This is much more aligned with a **trust layer** than simply putting one neural network behind a dashboard.

---

# 9. RECOMMENDED MODEL STACK

For a realistic student implementation:

## Layer 1 — Data Quality

```text
Pandas
Pydantic
Custom validation
```

## Layer 2 — Statistical Detection

```text
Rolling statistics
Z-score
EWMA
CUSUM
```

## Layer 3 — Unsupervised Detection

```text
Isolation Forest
```

## Layer 4 — Bias Detection

```text
Residual analysis
Rolling bias
Sensor correlation
Change-point detection
```

## Layer 5 — Supervised Classification

```text
XGBoost / Random Forest
```

## Layer 6 — Explainability

```text
SHAP
Rule explanations
```

## Layer 7 — Governance

```text
Confidence thresholds
Rule engine
Human approval
```

---

# 10. RECOMMENDED BACKEND ARCHITECTURE

```text
Frontend
React / Vue
     │
     ▼
FastAPI Backend
     │
     ├── /api/data
     ├── /api/events
     ├── /api/sensors
     ├── /api/models
     ├── /api/explanations
     ├── /api/decisions
     └── WebSocket
              │
              ▼
       Detection Engine
              │
       ┌──────┼───────┐
       ↓      ↓       ↓
    Anomaly  Bias   Fault
       │      │       │
       └──────┼───────┘
              ↓
       Evidence Fusion
              ↓
       Confidence Engine
              ↓
       Governance Engine
              ↓
          Audit Log
```

---

# 11. DATABASE ARCHITECTURE

## PostgreSQL

Recommended for structured application data.

Tables:

```text
users
sensors
measurements
events
anomalies
decisions
audit_logs
models
model_versions
alerts
feedback
```

## Time-series option

For a more advanced architecture:

- TimescaleDB
- InfluxDB

Use a time-series database if measurements become very large.

---

# 12. FRONTEND ARCHITECTURE

## Main screens

### 1. Command Center

```text
System Health
Active Alerts
Risk Level
Sensor Status
Recent Events
```

### 2. Live Monitoring

```text
Real-time graphs
Sensor values
Expected values
Anomaly markers
```

### 3. Event Investigation

```text
Event
Timeline
Evidence
Confidence
Explanation
Recommended action
```

### 4. Sensor Health

```text
Sensor list
Health score
Bias
Drift
Missing data
```

### 5. AI Decision Center

```text
Pending approvals
AI recommendations
Confidence
Explanation
Approve / Reject / Override
```

### 6. Audit Center

```text
Historical decisions
Who decided
What AI detected
Why
What happened afterward
```

### 7. Simulation Center

```text
Scenario selection
Anomaly injection
Replay
Results
```

---

# 13. PROJECT FOLDER ARCHITECTURE

Recommended:

```text
energymind/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │
│   │   ├── detection/
│   │   │   ├── anomaly.py
│   │   │   ├── bias.py
│   │   │   ├── drift.py
│   │   │   ├── fault.py
│   │   │   └── integrity.py
│   │   │
│   │   ├── explainability/
│   │   │   ├── shap_engine.py
│   │   │   ├── rules.py
│   │   │   └── explanations.py
│   │   │
│   │   ├── governance/
│   │   │   ├── confidence.py
│   │   │   ├── escalation.py
│   │   │   └── decisions.py
│   │   │
│   │   └── main.py
│   │
│   └── tests/
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── charts/
│   └── services/
│
├── ml/
│   ├── datasets/
│   ├── preprocessing/
│   ├── feature_engineering/
│   ├── training/
│   ├── evaluation/
│   └── models/
│
├── simulation/
│   ├── baseline/
│   ├── generators/
│   └── scenarios/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── generated/
│
├── docs/
│
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 14. DOCKER ARCHITECTURE

Recommended final deployment:

```text
┌──────────────────────────────────────────────┐
│                  Docker                      │
│                                              │
│  ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │ Frontend │──→│ FastAPI  │──→│Postgres │ │
│  └──────────┘   └────┬─────┘   └─────────┘ │
│                      │                       │
│                ┌─────▼─────┐                 │
│                │ ML Engine │                 │
│                └─────┬─────┘                 │
│                      │                       │
│                ┌─────▼─────┐                 │
│                │ Simulator │                 │
│                └───────────┘                 │
└──────────────────────────────────────────────┘
```

Optional:

```text
Redis
MQTT
Kafka
TimescaleDB
```

Do not add these unless they solve an actual project requirement.

---

# 15. COMPLETE DATA FLOW

The final end-to-end workflow should be:

```text
1. DATA ARRIVES
        ↓
2. VALIDATE DATA
        ↓
3. CLEAN / NORMALIZE
        ↓
4. EXTRACT FEATURES
        ↓
5. DETECT ANOMALIES
        ↓
6. CHECK SENSOR BIAS / DRIFT
        ↓
7. CHECK EQUIPMENT HEALTH
        ↓
8. CHECK DATA INTEGRITY
        ↓
9. CLASSIFY EVENT
        ↓
10. CALCULATE CONFIDENCE
        ↓
11. GENERATE EXPLANATION
        ↓
12. DETERMINE AI AUTHORITY
        ↓
13. AUTO-ACTION OR HUMAN REVIEW
        ↓
14. RECORD AUDIT LOG
        ↓
15. COLLECT HUMAN FEEDBACK
        ↓
16. IMPROVE MODEL
```

---

# 16. WHAT IS MANDATORY VS OPTIONAL

## MUST HAVE

### Challenge requirements

- [x] Anomaly detection
- [x] Bias detection
- [x] Equipment fault detection
- [x] Degraded sensor detection
- [x] Corrupted/falsified data detection
- [x] Genuine event vs data-quality distinction
- [x] Confidence score
- [x] Human-readable explanation
- [x] Auditable decision log
- [x] Human-AI escalation
- [x] Human approval/override interface
- [x] Single-node working prototype
- [x] Evaluation metrics
- [x] Documented anomaly generation

## STRONGLY RECOMMENDED

- [ ] Real-time dashboard
- [ ] WebSockets
- [ ] Sensor health score
- [ ] Event timeline
- [ ] Synthetic anomaly generator
- [ ] Scenario replay
- [ ] SHAP
- [ ] Hybrid rules + ML architecture
- [ ] Human feedback loop
- [ ] Docker deployment

## ADVANCED / OPTIONAL

- [ ] Federated learning
- [ ] Multi-node simulation
- [ ] Knowledge-sharing network
- [ ] MQTT
- [ ] Kafka
- [ ] Redis
- [ ] Digital twin
- [ ] Transformer
- [ ] LLM-based explanation layer
- [ ] Automated model retraining
- [ ] Mobile application

---

# 17. BEST ARCHITECTURE FOR THIS PROJECT

The recommended architecture is **not**:

```text
Dataset → Neural Network → Dashboard
```

Instead:

```text
                  ENERGY DATA
                      ↓
              DATA QUALITY LAYER
                      ↓
              FEATURE ENGINEERING
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   STATISTICAL     UNSUPERVISED   SUPERVISED
    DETECTION       DETECTION     CLASSIFICATION
        │             │             │
        └─────────────┼─────────────┘
                      ↓
               BIAS / DRIFT
                  ANALYSIS
                      ↓
                RULE ENGINE
                      ↓
              EVIDENCE FUSION
                      ↓
               FINAL VERDICT
                      ↓
             CONFIDENCE SCORE
                      ↓
              EXPLAINABILITY
                      ↓
             GOVERNANCE ENGINE
                 ↙        ↘
          AUTO-ACTION    HUMAN
                         REVIEW
                            ↓
                       AUDIT LOG
                            ↓
                    HUMAN FEEDBACK
                            ↓
                     MODEL LEARNING
```

This architecture best represents the project's actual identity:

> **EnergyMind is not simply an anomaly detector. It is a trustworthy decision layer that evaluates the reliability of energy data before that data is allowed to influence automated decisions.**

---

# 18. Suggested Technology Stack

| Layer | Recommended Technology |
|---|---|
| Language | Python |
| ML | scikit-learn |
| Advanced ML | XGBoost / LightGBM |
| Deep Learning | PyTorch |
| Explainability | SHAP |
| Backend | FastAPI |
| Real-time | WebSockets |
| Database | PostgreSQL |
| Time-series | TimescaleDB |
| Frontend | React |
| Charts | Plotly / Recharts |
| Simulation | Python |
| Containerization | Docker |
| Testing | Pytest |
| API documentation | FastAPI / OpenAPI |
| Version control | Git / GitHub |

---

# 19. Recommended Development Order

Do NOT implement everything at once.

## Phase 1 — Dataset

```text
Baseline energy data
        ↓
Anomaly injection
        ↓
Labeled dataset
```

## Phase 2 — Detection

Implement:

1. Statistical baseline
2. Anomaly detection
3. Bias detection
4. Drift detection
5. Data integrity

## Phase 3 — Classification

Build:

```text
Real Event
vs
Data Problem
vs
Sensor Problem
vs
Equipment Problem
```

## Phase 4 — Trust Layer

Add:

- Confidence
- Explanations
- Rules
- Audit log

## Phase 5 — Governance

Add:

- Automatic actions
- Human approval
- Override
- Escalation

## Phase 6 — Dashboard

Add:

- Live monitoring
- Events
- Sensor health
- Explanations
- Decisions

## Phase 7 — Advanced

Add:

- Feedback learning
- Multi-node simulation
- Knowledge sharing
- Federated architecture

---

# 20. Minimum Viable Competition Prototype

If time is limited, build this:

```text
              CSV / Simulator
                    ↓
             FastAPI Backend
                    ↓
           Feature Engineering
                    ↓
       ┌────────────┼────────────┐
       ↓            ↓            ↓
   Isolation     Bias/Drift    Rules
    Forest        Detection     Engine
       └────────────┼────────────┘
                    ↓
             Event Classifier
                    ↓
            Confidence Score
                    ↓
              SHAP + Rules
                    ↓
           Human-AI Governance
                    ↓
              React Dashboard
                    ↓
               Audit Log
```

And demonstrate **three scenarios**:

### Scenario A — Genuine Grid Event

```text
Multiple sensors change consistently
→ Real event
→ High confidence
→ Appropriate response
```

### Scenario B — Sensor Bias

```text
One sensor deviates persistently
→ Bias detected
→ Data-quality problem
→ Inspect sensor
```

### Scenario C — Falsified Data

```text
Measurement violates temporal/
cross-sensor consistency
→ Data integrity warning
→ Human review
```

This gives the judges a clear demonstration of the central idea rather than showing disconnected AI models.

---

# 21. Final Design Principle

Every feature should answer one of these questions:

### TRUST

**Can we trust this data?**

### DETECT

**What is wrong?**

### CLASSIFY

**Is this a real energy event or a data problem?**

### EXPLAIN

**Why does the AI believe this?**

### CONFIDENCE

**How certain is it?**

### GOVERN

**Can AI act, or does a human need to decide?**

### LEARN

**Can the system become better from validated experience?**

### AUDIT

**Can we prove afterward what happened and why?**

That is the conceptual architecture that should guide the entire EnergyMind project.
