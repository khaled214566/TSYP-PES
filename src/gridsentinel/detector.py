"""Hybrid anomaly detector for a simulated smart-metered neighborhood."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["voltage_v", "current_a", "active_power_kw", "power_factor", "frequency_hz", "power_consistency_residual", "energy_step_kwh"]
MEASUREMENT_COLUMNS = ["voltage_v", "current_a", "active_power_kw", "power_factor", "frequency_hz", "energy_kwh"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().reset_index(drop=True)
    expected_power = out["voltage_v"] * out["current_a"] * out["power_factor"] / 1000.0
    out["power_consistency_residual"] = out["active_power_kw"] - expected_power
    out["missing_measurement"] = out[MEASUREMENT_COLUMNS].isna().any(axis=1).astype(int)
    group_col = "meter_id" if "meter_id" in out.columns else "zone_id"
    out["power_delta"] = out.groupby(group_col, sort=False)["active_power_kw"].diff().fillna(0)
    previous_power = out.groupby(group_col, sort=False)["active_power_kw"].shift(1)
    out["relative_power_change"] = (out["power_delta"].abs() / previous_power.abs().clip(lower=0.15)).replace([np.inf, -np.inf], np.nan).fillna(0)
    rolling_baseline = out.groupby(group_col, sort=False)["active_power_kw"].transform(lambda s: s.shift(1).rolling(30, min_periods=5).median())
    out["power_vs_recent_baseline"] = (out["active_power_kw"] / rolling_baseline.clip(lower=0.15)).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    out["voltage_delta"] = out.groupby(group_col, sort=False)["voltage_v"].diff().fillna(0)
    out["energy_step_kwh"] = out.groupby(group_col, sort=False)["energy_kwh"].diff().fillna(0)
    out["energy_expected_kwh"] = out["active_power_kw"] / 60.0
    out["energy_consistency_residual"] = out["energy_step_kwh"] - out["energy_expected_kwh"]
    out["repeated_reading_run"] = 0
    for _, indices in out.groupby(group_col, sort=False).groups.items():
        previous = None
        run = 0
        for i in indices:
            values = out.loc[i, MEASUREMENT_COLUMNS].tolist()
            comparable = tuple(None if pd.isna(v) else float(v) for v in values)
            if previous is not None and comparable == previous:
                run += 1
            else:
                run = 1
            out.loc[i, "repeated_reading_run"] = run
            previous = comparable
    return out


class GridSentinelDetector:
    """Isolation Forest plus transparent rules; no rule proves malicious intent."""
    def __init__(self, contamination: float = 0.03, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("detector", IsolationForest(n_estimators=160, contamination=contamination, random_state=random_state, n_jobs=-1)),
        ])
        self._fitted = False
        self._score_threshold: float | None = None

    def fit(self, normal_df: pd.DataFrame) -> "GridSentinelDetector":
        features = add_features(normal_df)
        if len(features) < 30:
            raise ValueError("Provide at least 30 normal training rows")
        self.model.fit(features[FEATURES])
        scores = self.model.decision_function(features[FEATURES])
        self._score_threshold = float(np.quantile(scores, self.contamination))
        self._fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError("Call fit() on normal-only data before predict()")
        df = df.reset_index(drop=True)
        feat = add_features(df)
        normality = self.model.decision_function(feat[FEATURES])
        spread = max(float(np.std(normality)), 1e-6)
        anomaly_score = 1.0 / (1.0 + np.exp(np.clip((normality - self._score_threshold) / spread, -30, 30)))
        outputs = []
        for i, row in feat.iterrows():
            score = float(anomaly_score[i])
            evidence: list[str] = []
            if int(row["missing_measurement"]):
                evidence.append("missing_or_unavailable_meter_reading")
            if pd.notna(row["voltage_v"]) and not (207 <= row["voltage_v"] <= 253):
                evidence.append("voltage_outside_illustrative_range")
            if pd.notna(row["frequency_hz"]) and not (49.5 <= row["frequency_hz"] <= 50.5):
                evidence.append("frequency_outside_illustrative_range")
            if pd.notna(row["power_consistency_residual"]) and abs(row["power_consistency_residual"]) > 0.25:
                evidence.append("power_current_voltage_inconsistency")
            if pd.notna(row["energy_consistency_residual"]) and abs(row["energy_consistency_residual"]) > 0.08:
                evidence.append("energy_increment_power_inconsistency")
            if (abs(float(row.get("power_delta", 0) or 0)) > 1.5
                    or float(row.get("relative_power_change", 0) or 0) > 1.0
                    or float(row.get("power_vs_recent_baseline", 1.0) or 1.0) > 1.8
                    or float(row.get("power_vs_recent_baseline", 1.0) or 1.0) < 0.35):
                evidence.append("unusual_consumption_change_vs_recent_baseline")
            if int(row.get("repeated_reading_run", 0) or 0) >= 5:
                evidence.append("possible_frozen_or_replayed_meter_readings")
            ml_anomaly = normality[i] < self._score_threshold
            flagged = bool(ml_anomaly or evidence)
            if "missing_or_unavailable_meter_reading" in evidence:
                verdict, diagnosis, action = "SUSPICIOUS", "meter_data_unavailable", "request_operator_review_and_check_communications"
            elif "power_current_voltage_inconsistency" in evidence or "energy_increment_power_inconsistency" in evidence:
                verdict, diagnosis, action = "SUSPICIOUS", "meter_measurement_inconsistency_cause_unconfirmed", "retain_sample_for_review_and_check_meter_quality"
            elif "possible_frozen_or_replayed_meter_readings" in evidence:
                verdict, diagnosis, action = "SUSPICIOUS", "possible_frozen_or_replayed_readings", "request_operator_review_and_check_meter_health"
            elif "unusual_consumption_change_vs_recent_baseline" in evidence:
                verdict, diagnosis, action = "UNCERTAIN", "unusual_consumption_change_physical_cause_unknown", "compare_with_recent_household_baseline_and_review"
            elif flagged:
                verdict, diagnosis, action = "UNCERTAIN", "statistical_anomaly_cause_unconfirmed", "request_operator_review"
            else:
                verdict, diagnosis, action = "TRUSTED", "no_anomaly_detected_by_current_checks", "continue_monitoring"
            outputs.append({
                "anomaly_score": score,
                "ml_anomaly": bool(ml_anomaly),
                "flagged": flagged,
                "verdict": verdict,
                "diagnosis": diagnosis,
                "evidence": ";".join(evidence) if evidence else "no_rule_triggered",
                "recommended_action": action,
                "confidence": round(min(0.99, 0.50 + abs(score - 0.5)), 3),
                "confidence_note": "heuristic indicator; not a calibrated probability",
            })
        return pd.concat([df, pd.DataFrame(outputs)], axis=1)
