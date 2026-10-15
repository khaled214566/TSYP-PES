"""Statistical Outlier and Drift Engine.

Phase 2, Module 1 of EnergyMind Tunisia / GridSentinel.
Implements:
1. Rolling Z-Score (sudden impulses & spikes on Voltage and Power)
2. EWMA (Exponentially Weighted Moving Average drift tracking)
3. CUSUM (Cumulative Sum with decay for persistent level shifts and constant biases)
4. Page-Hinkley Test (sequential change-point and progressive drift detection)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd


@dataclass
class StatisticalConfig:
    """Configuration parameters for the statistical detection engine."""

    # Rolling Z-score
    z_window: int = 30
    z_spike_threshold: float = 3.0

    # EWMA
    ewma_span: int = 25
    ewma_threshold: float = 2.5

    # CUSUM on residuals (slack and decision threshold)
    cusum_slack: float = 0.10      # Tolerance before accumulation begins (kW)
    cusum_threshold: float = 0.40  # Decision threshold H (kW)
    cusum_decay: float = 0.15      # Decay rate when residual is within normal limits

    # Page-Hinkley test
    page_hinkley_delta: float = 0.05    # Minimum drift gradient tolerance
    page_hinkley_lambda: float = 0.60   # Decision threshold for drift alarm
    page_hinkley_decay: float = 0.96    # Forgetting factor for temporal stability

    # Grouping key
    group_col: str = "meter_id"


class RollingZScoreDetector:
    """Detects sudden spikes and impulses using rolling mean and standard deviation."""

    def __init__(self, window: int = 30, threshold: float = 3.0):
        self.window = window
        self.threshold = threshold

    def compute(self, series: pd.Series) -> tuple[pd.Series, pd.Series]:
        """Compute rolling Z-score and binary spike alerts.
        
        Uses past-only rolling window (shifted by 1) so an incoming spike
        does not corrupt its own baseline mean and variance.
        """
        rolling = series.shift(1).rolling(self.window, min_periods=max(5, self.window // 5))
        mean = rolling.mean()
        std = rolling.std().replace(0, np.nan).fillna(1e-4)

        z_score = ((series - mean) / std).fillna(0.0)
        spike_alert = (z_score.abs() >= self.threshold).astype(int)
        return z_score, spike_alert


class EWMADetector:
    """Tracks smoothed telemetry trends and flags sustained deviation via EWMA."""

    def __init__(self, span: int = 25, threshold: float = 2.5):
        self.span = span
        self.threshold = threshold

    def compute(self, series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Compute EWMA, residual, normalized drift score, and alert."""
        ewma = series.ewm(span=self.span, adjust=False).mean()
        residual = series - ewma
        res_std = residual.rolling(self.span, min_periods=5).std().replace(0, np.nan).fillna(1e-4)
        drift_score = (residual / res_std).fillna(0.0)
        alert = (drift_score.abs() >= self.threshold).astype(int)
        return ewma, drift_score, alert


class CUSUMDetector:
    """Cumulative Sum (CUSUM) with leak/decay for persistent level shifts and static biases."""

    def __init__(self, slack: float = 0.10, threshold: float = 0.40, decay: float = 0.15):
        self.slack = slack
        self.threshold = threshold
        self.decay = decay

    def compute(self, residual_series: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute CUSUM statistics and alerts on physics residual."""
        n = len(residual_series)
        s_pos = np.zeros(n, dtype=float)
        s_neg = np.zeros(n, dtype=float)
        alerts = np.zeros(n, dtype=int)

        curr_pos = 0.0
        curr_neg = 0.0

        for t in range(n):
            val = float(residual_series[t])
            if np.isnan(val):
                s_pos[t] = curr_pos
                s_neg[t] = curr_neg
                continue

            # Positive deviation accumulation
            if val > self.slack:
                curr_pos = min(10.0, curr_pos + (val - self.slack))
            else:
                curr_pos = max(0.0, curr_pos - self.decay)

            # Negative deviation accumulation
            if val < -self.slack:
                curr_neg = min(10.0, curr_neg + (-val - self.slack))
            else:
                curr_neg = max(0.0, curr_neg - self.decay)

            s_pos[t] = curr_pos
            s_neg[t] = curr_neg

            if curr_pos >= self.threshold or curr_neg >= self.threshold:
                alerts[t] = 1

        return s_pos, s_neg, alerts


class PageHinkleyDetector:
    """Sequential Page-Hinkley test for progressive linear drift detection."""

    def __init__(self, delta: float = 0.05, threshold: float = 0.60, decay: float = 0.96):
        self.delta = delta
        self.threshold = threshold
        self.decay = decay

    def compute(self, residual_series: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute Page-Hinkley cumulative statistics and drift rate estimates."""
        n = len(residual_series)
        ph_stat = np.zeros(n, dtype=float)
        alerts = np.zeros(n, dtype=int)
        drift_rates = np.zeros(n, dtype=float)

        cum_u = 0.0
        min_u = 0.0
        drift_start = 0

        for t in range(n):
            val = float(residual_series[t])
            if np.isnan(val):
                ph_stat[t] = max(0.0, cum_u - min_u)
                continue

            # Accumulate with forgetting factor to avoid long-term stationary drift
            cum_u = self.decay * cum_u + (val - self.delta)
            if cum_u < min_u:
                min_u = cum_u
                drift_start = t

            stat = max(0.0, cum_u - min_u)
            ph_stat[t] = stat

            if stat >= self.threshold:
                alerts[t] = 1
                dt = max(1, t - drift_start)
                drift_rates[t] = val / float(dt)

        return ph_stat, alerts, drift_rates


class StatisticalEngine:
    """Master Statistical Detection & Drift Engine.
    
    Fits baseline distributions from normal training data, then executes:
      1. Rolling Z-Score on raw Voltage and Active Power (instantaneous spikes).
      2. EWMA trend tracking on Active Power.
      3. CUSUM on physics residual (persistent bias / static offset).
      4. Page-Hinkley on physics residual (gradual linear drift detection).
    """

    def __init__(self, config: StatisticalConfig | None = None):
        self.config = config or StatisticalConfig()
        self.z_detector = RollingZScoreDetector(window=self.config.z_window, threshold=self.config.z_spike_threshold)
        self.ewma_detector = EWMADetector(span=self.config.ewma_span, threshold=self.config.ewma_threshold)
        self.cusum_detector = CUSUMDetector(
            slack=self.config.cusum_slack,
            threshold=self.config.cusum_threshold,
            decay=self.config.cusum_decay,
        )
        self.ph_detector = PageHinkleyDetector(
            delta=self.config.page_hinkley_delta,
            threshold=self.config.page_hinkley_lambda,
            decay=self.config.page_hinkley_decay,
        )
        self.meter_baselines_: dict[str, dict[str, Any]] = {}
        self.global_baselines_: dict[str, float] = {}
        self._fitted = False

    def fit(self, baseline_df: pd.DataFrame) -> "StatisticalEngine":
        """Learn per-meter and global baseline statistics from clean normal data."""
        df = baseline_df.copy()
        group_col = self.config.group_col

        self.global_baselines_ = {
            "voltage_mean": float(df["voltage_v"].mean()) if "voltage_v" in df.columns else 230.0,
            "voltage_std": float(df["voltage_v"].std()) if "voltage_v" in df.columns else 2.5,
            "power_mean": float(df["active_power_kw"].mean()) if "active_power_kw" in df.columns else 0.75,
            "power_std": float(df["active_power_kw"].std()) if "active_power_kw" in df.columns else 0.45,
        }

        meters = df[group_col].unique() if group_col in df.columns else ["default"]
        self.meter_baselines_ = {}

        for meter in meters:
            m_df = df[df[group_col] == meter] if group_col in df.columns else df
            self.meter_baselines_[str(meter)] = {
                "voltage_mean": float(m_df["voltage_v"].mean()) if "voltage_v" in m_df.columns else self.global_baselines_["voltage_mean"],
                "voltage_std": float(m_df["voltage_v"].std()) if "voltage_v" in m_df.columns else self.global_baselines_["voltage_std"],
                "power_mean": float(m_df["active_power_kw"].mean()) if "active_power_kw" in m_df.columns else self.global_baselines_["power_mean"],
                "power_std": float(m_df["active_power_kw"].std()) if "active_power_kw" in m_df.columns else self.global_baselines_["power_std"],
            }

        self._fitted = True
        return self

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process telemetry and output statistical anomaly scores and alerts."""
        if not self._fitted:
            raise RuntimeError("StatisticalEngine must be fitted on baseline normal data before calling detect().")

        out = df.copy().reset_index(drop=True)
        group_col = self.config.group_col

        # Single-phase Ohm's law expected power and residual
        expected_p = out["voltage_v"] * out["current_a"] * out["power_factor"] / 1000.0
        p_residual = (out["active_power_kw"] - expected_p).fillna(0.0).to_numpy()

        n = len(out)
        z_score_v = np.zeros(n, dtype=float)
        z_score_p = np.zeros(n, dtype=float)
        z_spike_alert = np.zeros(n, dtype=int)

        ewma_p = np.zeros(n, dtype=float)
        ewma_score_p = np.zeros(n, dtype=float)
        ewma_alert_p = np.zeros(n, dtype=int)

        cusum_pos = np.zeros(n, dtype=float)
        cusum_neg = np.zeros(n, dtype=float)
        cusum_alert = np.zeros(n, dtype=int)

        ph_stat = np.zeros(n, dtype=float)
        ph_alert = np.zeros(n, dtype=int)
        drift_rate = np.zeros(n, dtype=float)

        groups = out.groupby(group_col, sort=False).groups if group_col in out.columns else {"default": out.index}

        for _, indices in groups.items():
            idx_list = np.asarray(indices, dtype=int)
            meter_key = str(out.loc[idx_list[0], group_col]) if group_col in out.columns else "default"
            m_base = self.meter_baselines_.get(meter_key, self.global_baselines_)

            m_v = out.loc[idx_list, "voltage_v"]
            m_p = out.loc[idx_list, "active_power_kw"]
            m_res = p_residual[idx_list]

            # 1. Rolling Z-Scores (spikes & transient load surges)
            zv, zv_alert = self.z_detector.compute(m_v)
            zp, zp_alert = self.z_detector.compute(m_p)

            # Baseline Z-Scores relative to meter's learned normal mean and std
            p_base_mean = m_base.get("power_mean", self.global_baselines_["power_mean"])
            p_base_std = max(float(m_base.get("power_std", self.global_baselines_["power_std"])), 1e-4)
            z_base_p = (m_p - p_base_mean) / p_base_std

            # Spike alert fires on either sharp rolling transition OR large baseline elevation
            spike_alert = (zv_alert | zp_alert | (z_base_p >= self.config.z_spike_threshold)).astype(int)

            z_score_v[idx_list] = zv.to_numpy()
            z_score_p[idx_list] = zp.to_numpy()
            z_spike_alert[idx_list] = spike_alert.to_numpy()

            # 2. EWMA trend tracking
            ew_val, ew_score, ew_al = self.ewma_detector.compute(m_p)
            ewma_p[idx_list] = ew_val.to_numpy()
            ewma_score_p[idx_list] = ew_score.to_numpy()
            ewma_alert_p[idx_list] = ew_al.to_numpy()

            # 3. CUSUM on physics residual (constant bias & level shifts)
            c_pos, c_neg, c_al = self.cusum_detector.compute(m_res)
            cusum_pos[idx_list] = c_pos
            cusum_neg[idx_list] = c_neg
            cusum_alert[idx_list] = c_al

            # 4. Page-Hinkley on physics residual (progressive linear drift)
            ph_s, ph_al, d_rate = self.ph_detector.compute(m_res)
            ph_stat[idx_list] = ph_s
            ph_alert[idx_list] = ph_al
            drift_rate[idx_list] = d_rate

        # Attach statistical outputs to DataFrame
        out["z_score_voltage"] = z_score_v
        out["z_score_power"] = z_score_p
        out["statistical_spike_alert"] = z_spike_alert

        out["ewma_power_kw"] = ewma_p
        out["ewma_drift_score"] = ewma_score_p
        out["ewma_alert"] = ewma_alert_p

        out["cusum_pos_power"] = cusum_pos
        out["cusum_neg_power"] = cusum_neg
        out["cusum_alert_power"] = cusum_alert

        out["page_hinkley_stat"] = ph_stat
        out["page_hinkley_alert"] = ph_alert
        out["drift_rate_kw_per_min"] = drift_rate

        # Consolidated flags
        out["sustained_drift_flag"] = (out["page_hinkley_alert"] | out["ewma_alert"]).astype(int)
        out["persistent_bias_flag"] = out["cusum_alert_power"].astype(int)
        out["statistical_anomaly_flag"] = (
            out["statistical_spike_alert"] | out["sustained_drift_flag"] | out["persistent_bias_flag"]
        ).astype(int)

        return out

    def get_feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return only the statistical feature columns suitable for downstream classifiers."""
        scored = self.detect(df)
        cols = [
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
        return scored[cols]
