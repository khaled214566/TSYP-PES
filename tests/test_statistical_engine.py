"""Unit tests for Phase 2, Module 1: Statistical Outlier and Drift Engine."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gridsentinel.simulator import generate_dataset
from gridsentinel.detectors.statistical.engine import (
    StatisticalEngine,
    StatisticalConfig,
    RollingZScoreDetector,
    EWMADetector,
    CUSUMDetector,
    PageHinkleyDetector,
)


def test_rolling_z_score_detector():
    """Verify rolling Z-score flags sudden transient spikes."""
    detector = RollingZScoreDetector(window=20, threshold=3.0)
    data = [1.0] * 30 + [10.0] + [1.0] * 10
    series = pd.Series(data)
    z, alert = detector.compute(series)

    # Spike at index 30 should be flagged
    assert alert.iloc[30] == 1
    assert abs(z.iloc[30]) > 3.0
    # Normal points should not be flagged
    assert alert.iloc[5] == 0


def test_cusum_detector():
    """Verify CUSUM detects persistent constant bias."""
    detector = CUSUMDetector(slack=0.10, threshold=0.40, decay=0.15)
    # Baseline normal residual mean=0.0
    normal_data = np.random.normal(0.0, 0.02, 30)
    # Biased data residual=+1.0 (shift of 1.0 kW)
    biased_data = np.random.normal(1.0, 0.02, 30)
    series = np.concatenate([normal_data, biased_data])

    s_pos, s_neg, alerts = detector.compute(series)
    # Biased region should trigger positive CUSUM alert
    assert alerts[35:].sum() > 0
    assert s_pos[35:].max() >= 0.40


def test_page_hinkley_detector():
    """Verify Page-Hinkley detects progressive gradual drift."""
    detector = PageHinkleyDetector(delta=0.05, threshold=0.60, decay=0.96)
    # Normal data residual mean=0.0
    normal_data = np.random.normal(0.0, 0.02, 30)
    # Linear drift ramp from 0.0 to 1.2
    drift_data = np.linspace(0.0, 1.2, 40)
    series = np.concatenate([normal_data, drift_data])

    ph_stat, alerts, drift_rates = detector.compute(series)
    # The progressive drift must trigger a Page-Hinkley alert
    assert alerts[40:].sum() > 0
    assert ph_stat[-1] >= 0.60


def test_statistical_engine_end_to_end_on_baseline():
    """Verify StatisticalEngine fit and detect on synthetic smart-meter telemetry."""
    train_df = generate_dataset(steps=240, meters=5, seed=42, inject_anomalies=False)
    test_df = generate_dataset(steps=240, meters=5, seed=43, inject_anomalies=True)

    engine = StatisticalEngine()
    engine.fit(train_df)

    scored = engine.detect(test_df)

    # Check required output columns
    expected_cols = [
        "z_score_voltage",
        "z_score_power",
        "statistical_spike_alert",
        "ewma_drift_score",
        "ewma_alert",
        "cusum_pos_power",
        "cusum_neg_power",
        "cusum_alert_power",
        "page_hinkley_stat",
        "page_hinkley_alert",
        "drift_rate_kw_per_min",
        "sustained_drift_flag",
        "persistent_bias_flag",
        "statistical_anomaly_flag",
    ]
    for col in expected_cols:
        assert col in scored.columns, f"Missing output column: {col}"

    # Extract feature matrix for downstream classifiers
    feature_matrix = engine.get_feature_matrix(test_df)
    assert len(feature_matrix) == len(test_df)
    assert set(expected_cols).issubset(set(feature_matrix.columns))


def test_statistical_engine_detects_drift_and_bias_scenarios():
    """Verify that meter_drift and constant_bias scenarios trigger statistical alerts."""
    train_df = generate_dataset(steps=240, meters=10, seed=10, inject_anomalies=False)
    test_df = generate_dataset(steps=240, meters=10, seed=11, inject_anomalies=True)

    engine = StatisticalEngine()
    engine.fit(train_df)
    scored = engine.detect(test_df)

    # Constant bias scenario should be caught by CUSUM / bias flags
    bias_rows = scored[scored["event_type"] == "constant_bias"]
    assert len(bias_rows) > 0
    bias_caught = (bias_rows["persistent_bias_flag"] == 1).mean()
    assert bias_caught >= 0.70, f"Expected >= 70% detection on constant_bias, got {bias_caught:.2f}"

    # Meter drift scenario should be caught by sustained drift / Page-Hinkley
    drift_rows = scored[scored["event_type"] == "meter_drift"]
    assert len(drift_rows) > 0
    drift_caught = (drift_rows["sustained_drift_flag"] == 1).mean()
    assert drift_caught >= 0.60, f"Expected >= 60% detection on meter_drift, got {drift_caught:.2f}"

    # Consumption spike should trigger statistical spike alert
    spike_rows = scored[scored["event_type"] == "consumption_spike"]
    assert len(spike_rows) > 0
    spike_caught = (spike_rows["statistical_spike_alert"] == 1).mean()
    assert spike_caught >= 0.70, f"Expected >= 70% detection on consumption_spike, got {spike_caught:.2f}"


if __name__ == "__main__":
    test_rolling_z_score_detector()
    test_cusum_detector()
    test_page_hinkley_detector()
    test_statistical_engine_end_to_end_on_baseline()
    test_statistical_engine_detects_drift_and_bias_scenarios()
    print("All Phase 2, Module 1 unit tests passed successfully!")
