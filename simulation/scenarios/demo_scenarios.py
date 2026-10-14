import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

def generate_scenario_a_grid_event(baseline_df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Scenario A: Genuine Grid Event (Multi-sensor consistent surge/sag)"""
    df = baseline_df.copy()
    timestamps = sorted(df["timestamp"].unique())
    # Choose an event in the middle
    start_idx = len(timestamps) // 2
    duration = 20
    t_slice = timestamps[start_idx : start_idx + duration]
    
    # 18V sag across ALL sensors consistently
    mask = df["timestamp"].isin(t_slice)
    df.loc[mask, "voltage"] = np.round(df.loc[mask, "voltage"] - 18.0, 2)
    df.loc[mask, "current"] = np.round(df.loc[mask, "current"] * 1.15, 2)
    df.loc[mask, "is_anomaly"] = True
    df.loc[mask, "anomaly_type"] = "grid_event"
    
    meta = {
        "scenario": "A_genuine_grid_event",
        "description": "Multi-sensor consistent voltage sag across entire feeder",
        "expected_verdict": "GENUINE_GRID_EVENT",
        "expected_confidence": "HIGH (>=95%)",
        "recommended_action": "AUTOMATIC_RESPONSE_OR_LOG"
    }
    return df, meta

def generate_scenario_b_sensor_bias(baseline_df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Scenario B: Sensor Bias (Single sensor persistent offset)"""
    df = baseline_df.copy()
    timestamps = sorted(df["timestamp"].unique())
    start_idx = len(timestamps) // 2
    duration = 60
    t_slice = timestamps[start_idx : start_idx + duration]
    target_sensor = "S-03"
    
    mask = (df["timestamp"].isin(t_slice)) & (df["sensor_id"] == target_sensor)
    # +9.5V persistent bias
    df.loc[mask, "voltage"] = np.round(df.loc[mask, "voltage"] + 9.5, 2)
    df.loc[mask, "is_anomaly"] = True
    df.loc[mask, "anomaly_type"] = "sensor_bias"
    
    meta = {
        "scenario": "B_sensor_bias",
        "description": "Single sensor S-03 persistent +9.5V deviation while peers remain nominal",
        "expected_verdict": "DATA_QUALITY_SENSOR_BIAS",
        "expected_confidence": "HIGH (>=90%)",
        "recommended_action": "SCHEDULE_CALIBRATION_INSPECTION"
    }
    return df, meta

def generate_scenario_c_falsified_data(baseline_df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Scenario C: Falsified Data (Replay attack breaking temporal/cross-sensor consistency)"""
    df = baseline_df.copy()
    timestamps = sorted(df["timestamp"].unique())
    start_idx = len(timestamps) // 2
    duration = 45
    t_slice = timestamps[start_idx : start_idx + duration]
    target_sensor = "S-05"
    
    # Replay older window
    rep_slice = timestamps[start_idx - 180 : start_idx - 180 + duration]
    for orig_t, rep_t in zip(t_slice, rep_slice):
        old_vals = df[(df["timestamp"] == rep_t) & (df["sensor_id"] == target_sensor)].iloc[0]
        cur_mask = (df["timestamp"] == orig_t) & (df["sensor_id"] == target_sensor)
        df.loc[cur_mask, "voltage"] = old_vals["voltage"]
        df.loc[cur_mask, "active_power"] = old_vals["active_power"]
        df.loc[cur_mask, "current"] = old_vals["current"]
        df.loc[cur_mask, "is_anomaly"] = True
        df.loc[cur_mask, "anomaly_type"] = "replay_attack"
        
    meta = {
        "scenario": "C_falsified_data",
        "description": "Sensor S-05 data replayed from 3 hours prior; violates cross-sensor correlation",
        "expected_verdict": "FALSIFIED_DATA_ATTACK",
        "expected_confidence": "HIGH (>=90%)",
        "recommended_action": "ESCALATE_HUMAN_SECURITY_REVIEW"
    }
    return df, meta
