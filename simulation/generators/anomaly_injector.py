import json
import uuid
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List

class AnomalyInjector:
    """
    Injects 10 specific anomaly types into clean energy baseline data
    and generates detailed ground-truth labels and event metadata.
    """
    CATEGORY_MAP = {
        "sensor_bias": "data_quality",
        "sensor_drift": "data_quality",
        "spike": "data_quality",
        "dropout": "data_quality",
        "constant_freeze": "data_integrity",
        "replay_attack": "falsification",
        "bias_injection": "falsification",
        "random_corruption": "falsification",
        "grid_event": "real_event",
        "equipment_fault": "real_event"
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.inj_cfg = config["anomaly_injection"]
        self.seed = config["simulation"].get("seed", 42) + 777
        self.rng = np.random.default_rng(self.seed)

    def inject(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        df = df.copy()
        sensors = sorted(df["sensor_id"].unique())
        timestamps = sorted(df["timestamp"].unique())
        total_steps = len(timestamps)
        
        # Prepare lookup table indexed by (timestamp, sensor_id)
        df.set_index(["timestamp", "sensor_id"], inplace=True)
        
        labels_list: List[Dict[str, Any]] = []
        anomaly_types_cfg = self.inj_cfg["types"]
        
        # Guard margins to avoid boundary indexing issues
        margin = 120
        valid_indices = np.arange(margin, total_steps - margin)

        for anom_type, type_cfg in anomaly_types_cfg.items():
            if not type_cfg.get("enabled", True):
                continue
                
            count = type_cfg.get("count", 10)
            chosen_starts = self.rng.choice(valid_indices, size=min(count, len(valid_indices)), replace=False)
            
            for start_idx in chosen_starts:
                dur_range = type_cfg.get("duration_min", [10, 30])
                duration = int(self.rng.integers(dur_range[0], dur_range[1] + 1))
                end_idx = min(start_idx + duration, total_steps - 1)
                
                t_slice = timestamps[start_idx:end_idx]
                if len(t_slice) == 0:
                    continue
                    
                start_time = t_slice[0]
                end_time = t_slice[-1]
                anom_id = f"ANOM-{uuid.uuid4().hex[:8].upper()}"
                
                if anom_type == "grid_event":
                    # Affects multiple or all sensors simultaneously
                    affected_sensors = sensors.copy()
                    mag_range = type_cfg.get("magnitude_factor", [0.1, 0.25])
                    factor = float(self.rng.uniform(mag_range[0], mag_range[1]))
                    # Grid event: e.g. voltage sag and current surge
                    direction = self.rng.choice([-1.0, 1.0])
                    v_delta = direction * 230.0 * factor
                    severity = float(np.clip(abs(v_delta) / 45.0, 0.1, 1.0))
                    
                    for s in affected_sensors:
                        idx_tuples = [(t, s) for t in t_slice]
                        df.loc[idx_tuples, "voltage"] = np.round(df.loc[idx_tuples, "voltage"] + v_delta, 2)
                        # Current responds inversely or surges accordingly
                        if direction < 0:
                            df.loc[idx_tuples, "current"] = np.round(df.loc[idx_tuples, "current"] * (1.0 + factor * 0.8), 2)
                        df.loc[idx_tuples, "is_anomaly"] = True
                        df.loc[idx_tuples, "anomaly_type"] = anom_type
                        
                    labels_list.append({
                        "anomaly_id": anom_id,
                        "anomaly_type": anom_type,
                        "sensor_id": "ALL",
                        "start_time": str(start_time),
                        "end_time": str(end_time),
                        "severity": round(severity, 3),
                        "affected_signals": ["voltage", "current"],
                        "injection_parameters": json.dumps({"factor": round(factor, 3), "voltage_delta": round(v_delta, 2)}),
                        "category": self.CATEGORY_MAP[anom_type]
                    })
                    
                else:
                    # Single sensor anomaly
                    target_sensor = str(self.rng.choice(sensors))
                    idx_tuples = [(t, target_sensor) for t in t_slice]
                    affected_signals = []
                    params = {}
                    severity = 0.5
                    
                    if anom_type == "sensor_bias":
                        offset_range = type_cfg.get("offset_range", [5.0, 15.0])
                        offset = float(self.rng.uniform(offset_range[0], offset_range[1]) * self.rng.choice([-1, 1]))
                        df.loc[idx_tuples, "voltage"] = np.round(df.loc[idx_tuples, "voltage"] + offset, 2)
                        affected_signals = ["voltage"]
                        severity = float(min(1.0, abs(offset) / 20.0))
                        params = {"offset": round(offset, 2)}
                        
                    elif anom_type == "sensor_drift":
                        rate_range = type_cfg.get("rate_per_min", [0.02, 0.08])
                        rate = float(self.rng.uniform(rate_range[0], rate_range[1]) * self.rng.choice([-1, 1]))
                        drift_ramp = np.arange(len(idx_tuples)) * rate
                        df.loc[idx_tuples, "voltage"] = np.round(df.loc[idx_tuples, "voltage"] + drift_ramp, 2)
                        affected_signals = ["voltage"]
                        severity = float(min(1.0, abs(drift_ramp[-1]) / 25.0))
                        params = {"drift_rate": round(rate, 4), "total_drift": round(drift_ramp[-1], 2)}
                        
                    elif anom_type == "spike":
                        mag_range = type_cfg.get("magnitude_range", [5.0, 15.0])
                        spikes = self.rng.uniform(mag_range[0], mag_range[1], size=len(idx_tuples)) * self.rng.choice([-1, 1])
                        df.loc[idx_tuples, "voltage"] = np.round(df.loc[idx_tuples, "voltage"] + spikes, 2)
                        affected_signals = ["voltage"]
                        severity = float(min(1.0, np.max(np.abs(spikes)) / 25.0))
                        params = {"max_spike": round(float(np.max(np.abs(spikes))), 2)}
                        
                    elif anom_type == "dropout":
                        # Sudden signal collapse or missing measurement representation
                        df.loc[idx_tuples, "voltage"] = 0.0
                        df.loc[idx_tuples, "current"] = 0.0
                        df.loc[idx_tuples, "active_power"] = 0.0
                        affected_signals = ["voltage", "current", "active_power"]
                        severity = 1.0
                        params = {"dropout_type": "zero_collapse"}
                        
                    elif anom_type == "constant_freeze":
                        # Value gets locked to previous constant
                        freeze_v = float(df.loc[idx_tuples[0], "voltage"])
                        freeze_i = float(df.loc[idx_tuples[0], "current"])
                        freeze_p = float(df.loc[idx_tuples[0], "active_power"])
                        df.loc[idx_tuples, "voltage"] = freeze_v
                        df.loc[idx_tuples, "current"] = freeze_i
                        df.loc[idx_tuples, "active_power"] = freeze_p
                        affected_signals = ["voltage", "current", "active_power"]
                        severity = 0.65
                        params = {"frozen_voltage": freeze_v, "frozen_power": freeze_p}
                        
                    elif anom_type == "replay_attack":
                        # Replays an older window of identical duration
                        window_len = len(idx_tuples)
                        replay_offset = int(self.rng.integers(60, 240))
                        rep_start = max(0, start_idx - replay_offset)
                        rep_timestamps = timestamps[rep_start : rep_start + window_len]
                        if len(rep_timestamps) == window_len:
                            rep_tuples = [(t, target_sensor) for t in rep_timestamps]
                            df.loc[idx_tuples, "voltage"] = df.loc[rep_tuples, "voltage"].values
                            df.loc[idx_tuples, "current"] = df.loc[rep_tuples, "current"].values
                            df.loc[idx_tuples, "active_power"] = df.loc[rep_tuples, "active_power"].values
                        affected_signals = ["voltage", "current", "active_power"]
                        severity = 0.85
                        params = {"replayed_lag_minutes": replay_offset}
                        
                    elif anom_type == "bias_injection":
                        # Deliberate intentional offset attack to deceive billing or trust layer
                        offset_range = type_cfg.get("offset_range", [10.0, 25.0])
                        offset = float(self.rng.uniform(offset_range[0], offset_range[1]))
                        # Lower power or alter voltage to cheat billing
                        df.loc[idx_tuples, "active_power"] = np.round(np.maximum(0.1, df.loc[idx_tuples, "active_power"] * 0.65), 3)
                        df.loc[idx_tuples, "energy_consumption"] = np.round(df.loc[idx_tuples, "active_power"] * (1.0 / 60.0), 4)
                        affected_signals = ["active_power", "energy_consumption"]
                        severity = 0.9
                        params = {"power_reduction_pct": 35.0}
                        
                    elif anom_type == "random_corruption":
                        # Corrupted garbage readings / extreme impossible values
                        corrupt_v = self.rng.choice([999.0, -10.0, 480.0, 99.0], size=len(idx_tuples))
                        df.loc[idx_tuples, "voltage"] = corrupt_v
                        affected_signals = ["voltage"]
                        severity = 0.95
                        params = {"corruption": "out_of_bounds_injection"}
                        
                    elif anom_type == "equipment_fault":
                        # Characteristic equipment fault: severe harmonic distortion, low PF and surge current
                        df.loc[idx_tuples, "current"] = np.round(df.loc[idx_tuples, "current"] * 2.2, 2)
                        df.loc[idx_tuples, "power_factor"] = np.round(np.clip(df.loc[idx_tuples, "power_factor"] * 0.6, 0.45, 0.7), 3)
                        affected_signals = ["current", "power_factor"]
                        severity = 0.8
                        params = {"fault_pattern": "inductive_overcurrent"}
                        
                    df.loc[idx_tuples, "is_anomaly"] = True
                    df.loc[idx_tuples, "anomaly_type"] = anom_type
                    
                    labels_list.append({
                        "anomaly_id": anom_id,
                        "anomaly_type": anom_type,
                        "sensor_id": target_sensor,
                        "start_time": str(start_time),
                        "end_time": str(end_time),
                        "severity": round(severity, 3),
                        "affected_signals": affected_signals,
                        "injection_parameters": json.dumps(params),
                        "category": self.CATEGORY_MAP[anom_type]
                    })
        
        df.reset_index(inplace=True)
        labels_df = pd.DataFrame(labels_list)
        return df, labels_df
