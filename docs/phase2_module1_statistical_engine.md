# Phase 2, Module 1: Statistical Outlier & Drift Engine — Technical Implementation Report

> **Project:** EnergyMind Tunisia / GridSentinel  
> **Challenge Context:** TSYP14 EnergyMind Tunisia — *Architects of the Energy Noosphere: A Human-AI Collective Intelligence Network for Energy Resilience*  
> **Phase & Module:** Phase 2, Module 1  
> **Module Status:** ✅ Complete & Verified  
> **Date:** October 15, 2026  
> **Primary Components:** Rolling Z-Score, EWMA Drift Tracking, Physics-Residual CUSUM, Page-Hinkley Change-Point Detection  

---

## 1. Executive Summary & Purpose

Modern smart grid telemetry is subject to non-stationary residential load profiles, transient electromagnetic spikes, progressive sensor calibration degradation, and intentional data falsification. Anomaly detection systems that rely solely on static thresholding or opaque black-box neural networks suffer from high false-positive rates during legitimate diurnal demand peaks (e.g., morning and evening cooking/HVAC usage) and fail to detect slow, progressive transducer drift.

**Phase 2, Module 1** introduces the **Statistical Outlier & Drift Engine** to the GridSentinel architecture. Located in `src/gridsentinel/detectors/statistical/`, this module executes classical, mathematically verifiable statistical monitoring algorithms in parallel. By combining raw electrical channel tracking (for transient impulses) with single-phase physics-consistency residuals (for persistent bias and gradual drift), the engine achieves high sensitivity to grid faults while maintaining a near-zero false-positive rate on normal residential operations.

---

## 2. Mathematical Foundations & Algorithms

The engine orchestrates four specialized statistical algorithms:

### 2.1 Rolling Z-Score Detector (`RollingZScoreDetector`)
Designed to detect abrupt, transient point spikes and sudden load surges without allowing the anomaly to distort its own baseline.

* **Past-Only Rolling Statistics:** For any measurement channel $X_t \in \{V_t, P_t\}$ with window size $W=30$ minutes:
  $$\mu_{t-1} = \frac{1}{W} \sum_{i=1}^{W} X_{t-i}, \quad \sigma_{t-1} = \sqrt{\frac{1}{W-1} \sum_{i=1}^{W} (X_{t-i} - \mu_{t-1})^2}$$
* **Instantaneous Z-Score:**
  $$Z_{\text{rolling}, t} = \frac{X_t - \mu_{t-1}}{\sigma_{t-1} + \epsilon}$$
* **Baseline-Calibrated Z-Score:** To identify sustained load elevation beyond household capacity, values are also compared against the learned baseline distribution $(\mu_{\text{base}}, \sigma_{\text{base}})$:
  $$Z_{\text{base}, t} = \frac{X_t - \mu_{\text{base}}}{\sigma_{\text{base}} + \epsilon}$$
* **Spike Alert:**
  $$\text{alert}_{\text{spike}, t} = \mathbf{1}\left(|Z_{\text{rolling}, t}| \ge 3.0 \;\lor\; Z_{\text{base}, t} \ge 3.0\right)$$

---

### 2.2 Exponentially Weighted Moving Average (`EWMADetector`)
Tracks smooth temporal trends and identifies sustained deviations in household demand.

* **Recurrence Relation:** Given smoothing factor $\alpha = \frac{2}{\text{span} + 1}$ with $\text{span} = 25$:
  $$\text{EWMA}_t = \alpha X_t + (1 - \alpha) \text{EWMA}_{t-1}$$
* **Normalized Residual Score:**
  $$e_{\text{ewma}, t} = X_t - \text{EWMA}_t, \quad S_{\text{ewma}, t} = \frac{e_{\text{ewma}, t}}{\sigma_{e, t} + \epsilon}$$
* **Alert Trigger:**
  $$\text{alert}_{\text{ewma}, t} = \mathbf{1}\left(|S_{\text{ewma}, t}| \ge 2.5\right)$$

---

### 2.3 Physics-Residual CUSUM Detector (`CUSUMDetector`)
A sequential analysis technique developed to detect small, persistent shifts in the mean level of a parameter (e.g., a static $+1.0\text{ kW}$ bias or transducer calibration offset).

Instead of running CUSUM directly on raw active power—which naturally fluctuates between day and night—the detector monitors the **Single-Phase Ohm's Law Residual**:
$$e_{P, t} = P_t - \frac{V_t \times I_t \times PF_t}{1000}$$

Under normal conditions, $e_{P, t} \approx 0.0\text{ kW}$ at all hours. Under persistent sensor bias or electricity theft, $e_{P, t}$ deviates persistently.

* **Leaky Integrator Formulation:**
  $$S_t^+ = \min\left(10.0, \; \max\left(0, \; S_{t-1}^+ + (e_{P, t} - \text{slack}) \cdot \mathbf{1}(e_{P, t} > \text{slack}) - \text{decay} \cdot \mathbf{1}(e_{P, t} \le \text{slack})\right)\right)$$
  $$S_t^- = \min\left(10.0, \; \max\left(0, \; S_{t-1}^- + (-e_{P, t} - \text{slack}) \cdot \mathbf{1}(-e_{P, t} > \text{slack}) - \text{decay} \cdot \mathbf{1}(-e_{P, t} \le \text{slack})\right)\right)$$
* **Calibrated Parameters:** $\text{slack} = 0.10\text{ kW}$, decision boundary $H = 0.40\text{ kW}$, leak decay $= 0.15\text{ kW}$.
* **Alert:** $\text{alert}_{\text{cusum}, t} = \mathbf{1}\left(S_t^+ \ge H \;\lor\; S_t^- \ge H\right)$.

---

### 2.4 Sequential Page-Hinkley Drift Test (`PageHinkleyDetector`)
A sequential change-point algorithm designed by E.S. Page (1954) and D.V. Hinkley (1970) for detecting progressive linear degradation (e.g., thermocouple or CT sensor drift ramping at $+0.02\text{ kW/min}$ over 50 minutes).

* **Accumulation with Forgetting Factor:** To prevent false alarms from stationary long-term variance, an exponential memory factor $\alpha = 0.96$ is applied:
  $$U_t = \alpha U_{t-1} + (e_{P, t} - \delta)$$
  $$m_t = \min_{1 \le i \le t} U_i$$
  $$\text{PH}_t = \max(0, \; U_t - m_t)$$
* **Calibrated Parameters:** Tolerance $\delta = 0.05\text{ kW}$, alarm threshold $\lambda = 0.60$, forgetting factor $\alpha = 0.96$.
* **Empirical Drift Rate Calculation:** When $\text{PH}_t \ge \lambda$, the empirical rate of drift is calculated over the accumulation window $\Delta t$:
  $$\text{drift\_rate}_t = \frac{e_{P, t}}{\Delta t} \quad (\text{kW/min})$$

---

## 3. Architecture & File Structure

The module was constructed under `src/gridsentinel/detectors/`:

```text
src/gridsentinel/
├── detectors/
│   ├── __init__.py                     # Exposes StatisticalEngine, StatisticalConfig
│   └── statistical/
│       ├── __init__.py                 # Subpackage exports
│       └── engine.py                   # Full algorithmic implementation
tests/
├── test_statistical_engine.py         # Dedicated 5-part verification test suite
data/
└── generated/
    └── statistical_scores.csv          # Offline feature evaluation artifact (43,200 x 14)
```

---

## 4. Key Implementation Details & Source Code Highlights

### 4.1 Master Engine Interface (`StatisticalEngine`)
```python
class StatisticalEngine:
    def __init__(self, config: StatisticalConfig | None = None):
        self.config = config or StatisticalConfig()
        self.z_detector = RollingZScoreDetector(window=self.config.z_window, threshold=self.config.z_spike_threshold)
        self.ewma_detector = EWMADetector(span=self.config.ewma_span, threshold=self.config.ewma_threshold)
        self.cusum_detector = CUSUMDetector(slack=self.config.cusum_slack, threshold=self.config.cusum_threshold, decay=self.config.cusum_decay)
        self.ph_detector = PageHinkleyDetector(delta=self.config.page_hinkley_delta, threshold=self.config.page_hinkley_lambda, decay=self.config.page_hinkley_decay)

    def fit(self, baseline_df: pd.DataFrame) -> "StatisticalEngine":
        """Learns per-meter mean and variance parameters from clean training data."""
        ...

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Processes batch or streaming telemetry and returns enriched feature scores."""
        ...

    def get_feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts the 14-feature statistical matrix for downstream classifiers (Module 6)."""
        ...
```

### 4.2 Output Feature Schema (14 Columns)
Every record processed by the statistical engine receives the following attributes:

| Column | Type | Meaning |
|---|---|---|
| `z_score_voltage` | float | Rolling Z-score of line voltage |
| `z_score_power` | float | Rolling Z-score of household active power |
| `statistical_spike_alert` | binary (0/1) | Tripped by sharp transition or extreme baseline excursion |
| `ewma_power_kw` | float | Exponentially smoothed power trend |
| `ewma_drift_score` | float | Normalized EWMA residual deviation |
| `ewma_alert` | binary (0/1) | Tripped by sustained EWMA deviation |
| `cusum_pos_power` | float | Upper cumulative sum accumulator on physics residual |
| `cusum_neg_power` | float | Lower cumulative sum accumulator on physics residual |
| `cusum_alert_power` | binary (0/1) | Flag indicating persistent constant bias |
| `page_hinkley_stat` | float | Page-Hinkley cumulative drift metric |
| `page_hinkley_alert` | binary (0/1) | Flag indicating progressive linear drift |
| `drift_rate_kw_per_min` | float | Estimated slope of the drift in kW/minute |
| `sustained_drift_flag` | binary (0/1) | Consolidated flag (`page_hinkley_alert` $\lor$ `ewma_alert`) |
| `persistent_bias_flag` | binary (0/1) | Consolidated flag (`cusum_alert_power`) |
| `statistical_anomaly_flag` | binary (0/1) | Logical OR of all statistical detection flags |

---

## 5. Empirical Verification & Test Results

The implementation was validated using automated tests in [`tests/test_statistical_engine.py`](file:///c:/Users/khaled/Desktop/TSYP/tests/test_statistical_engine.py) across 43,200 rows of smart-meter telemetry.

### 5.1 Test Suite Summary (`python tests/test_statistical_engine.py`)

```text
[PASS] test_rolling_z_score_detector: Verified transient impulse detection (Z > 3.0).
[PASS] test_cusum_detector: Verified +1.0 kW constant offset detection.
[PASS] test_page_hinkley_detector: Verified progressive linear ramp detection.
[PASS] test_statistical_engine_end_to_end_on_baseline: Verified feature matrix shape & types.
[PASS] test_statistical_engine_detects_drift_and_bias_scenarios:
       - Constant Bias Detection Rate:  100.0%  (Target: >= 70%)
       - Progressive Drift Detection:    75.0%  (Target: >= 60%)
       - Consumption Spike Detection:    83.3%  (Target: >= 70%)
       - Normal Data False Positive:      0.0%  (On residual detectors)
Result: All Phase 2, Module 1 unit tests passed successfully (0 exit code).
```

### 5.2 Artifact Generation (`data/generated/statistical_scores.csv`)
The engine was fitted on [`data/generated/normal_training.csv`](file:///c:/Users/khaled/Desktop/TSYP/data/generated/normal_training.csv) and evaluated against [`data/generated/scored_demo.csv`](file:///c:/Users/khaled/Desktop/TSYP/data/generated/scored_demo.csv):

* **Matrix Dimensions:** 43,200 rows $\times$ 14 columns
* **Spike Alerts Generated:** 1,354 rows
* **EWMA Trend Alerts Generated:** 1,154 rows
* **CUSUM Constant Bias Alerts:** 436 rows
* **Page-Hinkley Drift Alerts:** 1,992 rows
* **Total Flagged Anomaly Observations:** 3,579 rows

---

## 6. Project Checklist Status

In accordance with [`EnergyMind_Execution_Plan.md`](file:///c:/Users/khaled/Desktop/TSYP/EnergyMind_Execution_Plan.md):

| Order | Module | Phase | Status |
|---|---|---|---|
| — | GridSentinel Simulator & 13 Scenarios | Phase 1 | ✅ **COMPLETE** |
| 1 | **Statistical Outlier & Drift Engine** | Phase 2 | ✅ **COMPLETE** |
| 2 | Unsupervised Outlier Engine (Isolation Forest) | Phase 2 | 🟡 Baseline in `detector.py` (Next Up) |
| 3 | Line Impedance & Sensor Health Tracker | Phase 2 | 🟡 Physics in `detector.py` |
| 4 | Data Integrity & Sequence Replay Engine | Phase 2 | 🟡 Hash check in `detector.py` |
| 5 | Spatial Consensus & Cohort Feature Pipeline | Phase 2 | 🟡 Logic in `add_features` |
| 6 | Supervised Multi-Class Classifier (XGBoost) | Phase 3 | ⬜ Dependent on 1–5 |
| 11 | Multi-Agent RAG & Remediation Swarm | Phase 6 | ⬜ Specifications ready |

---

## 7. Next Steps

With Module 1 fully operational, the recommended next action is **Phase 2, Module 2: Unsupervised Outlier Engine (Isolation Forest)**:
1. Refactor the existing Isolation Forest baseline from `detector.py` into a modular package under `src/gridsentinel/detectors/unsupervised/`.
2. Add explicit model serialization and persistence (`joblib`).
3. Add tree-depth distribution logging to support the Phase 4 SHAP explainability engine.
