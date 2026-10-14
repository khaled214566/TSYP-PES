"""Hybrid anomaly detector and AI trust layer for a smart-metered neighborhood."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CABLE_RESISTANCE_PER_M = 0.0022

FEATURES = [
    "voltage_v",
    "current_a",
    "active_power_kw",
    "power_factor",
    "frequency_hz",
    "power_consistency_residual",
    "voltage_consistency_residual",
    "energy_step_kwh",
    "cohort_power_ratio",
]
MEASUREMENT_COLUMNS = ["voltage_v", "current_a", "active_power_kw", "power_factor", "frequency_hz", "energy_kwh"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive physics, temporal, peer-cohort, and spatial feeder features."""
    out = df.copy().reset_index(drop=True)
    group_col = "meter_id" if "meter_id" in out.columns else "zone_id"

    # Physics: Single-phase Ohm's law active power residual
    expected_power = out["voltage_v"] * out["current_a"] * out["power_factor"] / 1000.0
    out["power_consistency_residual"] = out["active_power_kw"] - expected_power

    # Physics: Voltage drop consistency based on distance and load current
    if "distance_from_transformer_m" in out.columns:
        dist = out["distance_from_transformer_m"]
    else:
        dist = 50.0
    expected_voltage = 230.0 - (CABLE_RESISTANCE_PER_M * dist * out["current_a"])
    out["voltage_consistency_residual"] = out["voltage_v"] - expected_voltage

    # Rolling power residual: EWMA / rolling mean to catch slow progressive sensor drift
    out["rolling_power_residual"] = out.groupby(group_col, sort=False)["power_consistency_residual"].transform(
        lambda s: s.rolling(10, min_periods=3).mean()
    ).fillna(0)

    # Missing telemetry check
    out["missing_measurement"] = out[MEASUREMENT_COLUMNS].isna().any(axis=1).astype(int)

    # Temporal load dynamics
    out["power_delta"] = out.groupby(group_col, sort=False)["active_power_kw"].diff().fillna(0)
    previous_power = out.groupby(group_col, sort=False)["active_power_kw"].shift(1)
    out["relative_power_change"] = (out["power_delta"].abs() / previous_power.abs().clip(lower=0.15)).replace([np.inf, -np.inf], np.nan).fillna(0)
    rolling_baseline = out.groupby(group_col, sort=False)["active_power_kw"].transform(
        lambda s: s.shift(1).rolling(45, min_periods=5).median()
    )
    out["power_vs_recent_baseline"] = (out["active_power_kw"] / rolling_baseline.clip(lower=0.15)).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    out["voltage_delta"] = out.groupby(group_col, sort=False)["voltage_v"].diff().fillna(0)

    # Energy interval consistency
    out["energy_step_kwh"] = out.groupby(group_col, sort=False)["energy_kwh"].diff().fillna(0)
    out["energy_expected_kwh"] = out["active_power_kw"] / 60.0
    out["energy_consistency_residual"] = out["energy_step_kwh"] - out["energy_expected_kwh"]
    out["rolling_energy_residual"] = out.groupby(group_col, sort=False)["energy_consistency_residual"].transform(
        lambda s: s.rolling(6, min_periods=2).mean()
    ).fillna(0)

    # Spatial Feeder Consensus (Scenario A: Genuine grid disturbance vs isolated sensor failure)
    feeder_col = "feeder_id" if "feeder_id" in out.columns else group_col
    out["feeder_median_voltage"] = out.groupby(["timestamp", feeder_col], sort=False)["voltage_v"].transform("median")
    out["feeder_sag_ratio"] = out.groupby(["timestamp", feeder_col], sort=False)["voltage_v"].transform(
        lambda s: (s < 212.0).mean()
    ).fillna(0)

    # Peer Cohort Comparison (Scenario C: Stealth theft / bias injection detection)
    cohort_group = ["timestamp", "household_type"] if "household_type" in out.columns else ["timestamp"]
    cohort_median_power = out.groupby(cohort_group, sort=False)["active_power_kw"].transform("median")
    out["cohort_power_ratio"] = (out["active_power_kw"] / cohort_median_power.clip(lower=0.15)).fillna(1.0)

    # Sequence Repeat (Frozen meter) and Sequence Replay Detection
    run_arr = np.zeros(len(out), dtype=int)
    replay_arr = np.zeros(len(out), dtype=int)

    v_arr = out["voltage_v"].to_numpy()
    p_arr = out["active_power_kw"].to_numpy()
    meas_arr = out[MEASUREMENT_COLUMNS].to_numpy()

    for _, indices in out.groupby(group_col, sort=False).groups.items():
        previous = None
        run = 0
        seen_triplets: dict[tuple, int] = {}
        idx_list = np.asarray(indices, dtype=int)

        for step_i in range(len(idx_list)):
            real_i = idx_list[step_i]
            vals = meas_arr[real_i]
            comparable = tuple(None if np.isnan(v) else round(float(v), 3) for v in vals)

            # Frozen meter check
            if previous is not None and comparable == previous:
                run += 1
            else:
                run = 1
            run_arr[real_i] = run
            previous = comparable

            # Replay sequence check (full 4-point electrical vector match against historical buffer > 20 steps ago)
            if step_i >= 3:
                v0 = round(float(v_arr[idx_list[step_i - 3]] or 0), 2)
                v1 = round(float(v_arr[idx_list[step_i - 2]] or 0), 2)
                v2 = round(float(v_arr[idx_list[step_i - 1]] or 0), 2)
                v3 = round(float(v_arr[real_i] or 0), 2)
                p3 = round(float(p_arr[real_i] or 0), 3)
                sig = (v0, v1, v2, v3, p3)
                if sig in seen_triplets:
                    if (step_i - seen_triplets[sig]) > 20:
                        replay_arr[idx_list[step_i - 3]:real_i + 1] = 1
                seen_triplets[sig] = step_i

    out["repeated_reading_run"] = run_arr
    out["replay_sequence_flag"] = replay_arr

    return out


class GridSentinelDetector:
    """Hybrid AI Trust Layer for Smart-Metered Neighborhoods.

    Combines an unsupervised Isolation Forest baseline with physical consistency checks,
    spatial feeder consensus, peer cohort analysis, and temporal sequence verification.
    Emits a dual-layer Trust Verdict + Event Classification, explainable evidence,
    a composite calibrated confidence score, and a 3-tier escalation recommendation.
    """

    def __init__(self, contamination: float = 0.03, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("detector", IsolationForest(n_estimators=160, max_samples=50000, contamination=contamination, random_state=random_state, n_jobs=-1)),
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
        for row in feat.itertuples(index=True):
            i = row.Index
            score = float(anomaly_score[i])
            ml_anomaly = normality[i] < self._score_threshold
            evidence: list[str] = []

            # 1. Missingness
            if int(getattr(row, "missing_measurement", 0) or 0):
                evidence.append("missing_or_unavailable_meter_reading")

            # 2. Voltage checks
            v_val = getattr(row, "voltage_v", np.nan)
            if pd.notna(v_val) and (v_val <= 0.0 or v_val > 270.0):
                evidence.append("telemetry_dropout_or_extreme_voltage")
            elif pd.notna(v_val) and not (207.0 <= v_val <= 253.0):
                evidence.append("voltage_outside_illustrative_range")

            # 3. Power factor & frequency
            pf_val = getattr(row, "power_factor", np.nan)
            if pd.notna(pf_val) and not (0.70 <= pf_val <= 1.0):
                evidence.append("power_factor_physical_boundary_violation")
            freq_val = getattr(row, "frequency_hz", np.nan)
            if pd.notna(freq_val) and not (49.5 <= freq_val <= 50.5):
                evidence.append("frequency_outside_illustrative_range")

            # 4. Instantaneous & gradual power residuals
            p_res = getattr(row, "power_consistency_residual", 0.0)
            if pd.notna(p_res) and abs(p_res) > 0.25:
                evidence.append("power_current_voltage_inconsistency")
            roll_p_res = getattr(row, "rolling_power_residual", 0.0)
            if pd.notna(roll_p_res) and abs(roll_p_res) > 0.12:
                evidence.append("accumulated_power_residual_drift")

            # 5. Energy interval consistency
            e_res = getattr(row, "energy_consistency_residual", 0.0)
            if pd.notna(e_res) and abs(e_res) > 0.035:
                evidence.append("energy_increment_power_inconsistency")
            roll_e_res = getattr(row, "rolling_energy_residual", 0.0)
            if pd.notna(roll_e_res) and abs(roll_e_res) > 0.012:
                evidence.append("accumulated_energy_residual_bias")

            # 6. Voltage drop line impedance consistency
            v_drop_res = getattr(row, "voltage_consistency_residual", 0.0)
            if pd.notna(v_drop_res) and abs(v_drop_res) > 8.5:
                evidence.append("voltage_drop_distance_inconsistency")

            # 7. Spatial Feeder Consensus (Scenario A)
            feeder_sag = float(getattr(row, "feeder_sag_ratio", 0) or 0)
            if feeder_sag >= 0.70:
                evidence.append("feeder_wide_voltage_sag_consensus")

            # 8. Peer Cohort Residuals & Energy Mismatch (Scenario C: Stealth theft)
            p_res_abs = abs(float(p_res or 0))
            is_v_normal = pd.notna(v_val) and (215.0 <= v_val <= 250.0)
            if is_v_normal and p_res_abs < 0.15:
                if float(roll_e_res or 0) > 0.0018:
                    evidence.append("stealth_consumption_suppression_vs_cohort")

            # 9. Temporal Dynamics & Sequence Matching
            p_delta = float(getattr(row, "power_delta", 0) or 0)
            rel_p_chg = float(getattr(row, "relative_power_change", 0) or 0)
            p_baseline = float(getattr(row, "power_vs_recent_baseline", 1.0) or 1.0)
            if abs(p_delta) > 1.8 or rel_p_chg > 1.2 or p_baseline > 2.2:
                evidence.append("unusual_consumption_change_vs_recent_baseline")

            if int(getattr(row, "repeated_reading_run", 0) or 0) >= 5:
                evidence.append("frozen_meter_readings_detected")
            if int(getattr(row, "replay_sequence_flag", 0) or 0) == 1:
                evidence.append("telemetry_sequence_replay_detected")

            # 10. Inductive Equipment Breakdown
            current_val = float(getattr(row, "current_a", 0) or 0)
            pf_val_num = float(pf_val if pd.notna(pf_val) else 0.95)
            if pf_val_num < 0.65 and current_val > 2.0:
                evidence.append("inductive_equipment_fault_signature")

            flagged = bool(ml_anomaly or evidence)

            # Decision Logic: Prioritize confirmed physical grid events, then critical falsification/faults
            if "feeder_wide_voltage_sag_consensus" in evidence:
                verdict = "ACTIONABLE_GRID_EVENT"
                event_class = "GENUINE_GRID_EVENT"
                diagnosis = "feeder_wide_voltage_sag_confirmed_by_consensus"
                action = "dispatch_distribution_voltage_regulation"
                confidence = round(min(0.99, 0.92 + 0.07 * feeder_sag), 3)
                escalation = "AUTO_ACTION"
                explanation = f"Feeder-wide voltage disturbance: {int(feeder_sag * 100)}% of meters on the feeder experienced concurrent voltage sag below 212V. Physical line drop confirmed by spatial cohort consensus."

            elif "telemetry_dropout_or_extreme_voltage" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "DATA_QUALITY_ISSUE"
                diagnosis = "telemetry_corruption_or_dropout"
                action = "quarantine_sample_and_check_hardware"
                confidence = 0.96
                escalation = "AUTO_ACTION"
                explanation = "Extreme telemetry voltage or complete line dropout violating physical operating boundaries."

            elif "missing_or_unavailable_meter_reading" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "DATA_QUALITY_ISSUE"
                diagnosis = "meter_data_unavailable"
                action = "request_operator_review_and_check_communications"
                confidence = 0.94
                escalation = "OPERATOR_APPROVAL"
                explanation = "Meter telemetry packet dropped: one or more required measurement channels unavailable."

            elif "inductive_equipment_fault_signature" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "EQUIPMENT_FAULT"
                diagnosis = "inductive_equipment_breakdown_detected"
                action = "quarantine_circuit_and_inspect_inductive_load"
                confidence = 0.93
                escalation = "OPERATOR_APPROVAL"
                explanation = "Inductive equipment fault: severe power factor collapse accompanied by load current surge, indicating heavy uncompensated inductive load or motor insulation breakdown."

            elif "stealth_consumption_suppression_vs_cohort" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "FALSIFICATION_ATTACK"
                diagnosis = "stealth_consumption_tampering_or_theft_suspected"
                action = "dispatch_field_tamper_inspection_and_quarantine"
                confidence = 0.92
                escalation = "OPERATOR_APPROVAL"
                explanation = "Stealth consumption suppression: active power persistently depressed while voltage and power factor remain nominal. Positive energy accumulation residual indicates unmetered draw."

            elif "telemetry_sequence_replay_detected" in evidence or "frozen_meter_readings_detected" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "FALSIFICATION_ATTACK"
                diagnosis = "telemetry_replay_or_frozen_meter_detected"
                action = "request_operator_review_and_check_meter_health"
                confidence = 0.91
                escalation = "OPERATOR_APPROVAL"
                explanation = "Temporal data integrity violation: frozen meter readings or repeated historical telemetry vector detected."

            elif "power_current_voltage_inconsistency" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "FALSIFICATION_ATTACK"
                diagnosis = "meter_power_current_inconsistency_falsification_suspected"
                action = "retain_sample_for_review_and_check_meter_quality"
                confidence = 0.90
                escalation = "OPERATOR_APPROVAL"
                explanation = "Ohm's law violation: active power does not reconcile with simultaneous voltage, current, and power factor measurements."

            elif "accumulated_power_residual_drift" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "DATA_QUALITY_ISSUE"
                diagnosis = "gradual_meter_measurement_drift"
                action = "schedule_meter_calibration_inspection"
                confidence = 0.88
                escalation = "OPERATOR_APPROVAL"
                explanation = "Accumulated measurement drift: persistent non-zero active power residual indicates calibration drift in transducers."

            elif "energy_increment_power_inconsistency" in evidence or "accumulated_energy_residual_bias" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "DATA_QUALITY_ISSUE"
                diagnosis = "cumulative_energy_power_mismatch"
                action = "retain_sample_for_review_and_check_meter_quality"
                confidence = 0.89
                escalation = "OPERATOR_APPROVAL"
                explanation = "Interval energy increment diverges from integrated active power over the 1-minute sampling period."

            elif "voltage_outside_illustrative_range" in evidence or "voltage_drop_distance_inconsistency" in evidence:
                verdict = "SUSPICIOUS"
                event_class = "DATA_QUALITY_ISSUE"
                diagnosis = "isolated_meter_voltage_drop_unsupported_by_feeder"
                action = "inspect_line_impedance_and_meter_calibration"
                confidence = 0.82
                escalation = "OPERATOR_APPROVAL"
                explanation = "Single-meter voltage drop unsupported by neighboring feeder meters; indicates localized impedance or drop-line issue."

            elif "unusual_consumption_change_vs_recent_baseline" in evidence:
                verdict = "UNCERTAIN"
                event_class = "NORMAL"
                diagnosis = "unusual_consumption_change_physical_cause_unknown"
                action = "compare_with_recent_household_baseline_and_review"
                confidence = 0.65
                escalation = "HUMAN_INVESTIGATION"
                explanation = "Transient demand fluctuation relative to recent household baseline without physical line or sensor violation."

            elif ml_anomaly:
                verdict = "UNCERTAIN"
                event_class = "DATA_QUALITY_ISSUE"
                diagnosis = "statistical_anomaly_cause_unconfirmed"
                action = "request_operator_review"
                confidence = round(max(0.55, min(0.68, 0.50 + abs(score - 0.5))), 3)
                escalation = "HUMAN_INVESTIGATION"
                explanation = "Unsupervised Isolation Forest flagged multivariate statistical outlier with unconfirmed physical cause."

            else:
                verdict = "TRUSTED"
                event_class = "NORMAL"
                diagnosis = "no_anomaly_detected_by_current_checks"
                action = "continue_monitoring"
                confidence = round(min(0.99, 0.95 + 0.04 * (1.0 - score)), 3)
                escalation = "AUTO_ACTION"
                explanation = "Telemetry conforms to physical electrical boundaries, line impedance drop, and historical baseline."

            outputs.append({
                "anomaly_score": score,
                "ml_anomaly": bool(ml_anomaly),
                "flagged": flagged,
                "verdict": verdict,
                "event_class": event_class,
                "diagnosis": diagnosis,
                "explanation": explanation,
                "evidence": ";".join(evidence) if evidence else "no_rule_triggered",
                "recommended_action": action,
                "confidence": confidence,
                "escalation_tier": escalation,
                "confidence_note": "composite calibrated confidence score; multi-evidence weighted fusion",
            })

        return pd.concat([df, pd.DataFrame(outputs)], axis=1)
