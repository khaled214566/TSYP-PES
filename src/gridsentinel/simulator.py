"""Synthetic smart-metered neighborhood telemetry and anomaly injection.

This simulator generates multi-day, one-minute smart meter telemetry for a residential
neighborhood hierarchy (meters -> buildings -> feeders). It injects 13 labelled
scenarios covering genuine grid disturbances, sensor degradation, data corruption,
and stealth cyber/falsification attacks, accompanied by a comprehensive ground-truth
event registry (labels.csv).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
import numpy as np
import pandas as pd

METER_SCENARIOS = [
    "consumption_spike",
    "meter_drift",
    "constant_bias",
    "false_data_injection",
    "replay_like",
    "frozen_meter",
    "missing_data",
    "energy_power_mismatch",
    "random_corruption",
    "dropout",
    "bias_injection",
    "equipment_fault",
    "grid_event",
]

SCENARIO_METADATA = {
    "grid_event": {"category": "real_event", "event_class": "GENUINE_GRID_EVENT", "severity": 0.85},
    "equipment_fault": {"category": "real_event", "event_class": "EQUIPMENT_FAULT", "severity": 0.90},
    "consumption_spike": {"category": "real_event", "event_class": "NORMAL", "severity": 0.30},
    "meter_drift": {"category": "data_quality", "event_class": "DATA_QUALITY_ISSUE", "severity": 0.60},
    "constant_bias": {"category": "data_quality", "event_class": "DATA_QUALITY_ISSUE", "severity": 0.70},
    "missing_data": {"category": "data_quality", "event_class": "DATA_QUALITY_ISSUE", "severity": 0.75},
    "dropout": {"category": "data_quality", "event_class": "DATA_QUALITY_ISSUE", "severity": 0.95},
    "random_corruption": {"category": "data_quality", "event_class": "DATA_QUALITY_ISSUE", "severity": 0.90},
    "energy_power_mismatch": {"category": "data_quality", "event_class": "DATA_QUALITY_ISSUE", "severity": 0.75},
    "false_data_injection": {"category": "falsification", "event_class": "FALSIFICATION_ATTACK", "severity": 0.85},
    "bias_injection": {"category": "falsification", "event_class": "FALSIFICATION_ATTACK", "severity": 0.85},
    "replay_like": {"category": "falsification", "event_class": "FALSIFICATION_ATTACK", "severity": 0.80},
    "frozen_meter": {"category": "falsification", "event_class": "FALSIFICATION_ATTACK", "severity": 0.75},
}

MEASUREMENT_COLUMNS = [
    "voltage_v", "current_a", "active_power_kw", "power_factor", "frequency_hz", "energy_kwh"
]

BUILDING_DISTANCES_M = {
    1: 50.0,
    2: 120.0,
    3: 220.0,
    4: 350.0,
    5: 480.0,
    6: 600.0,
}
CABLE_RESISTANCE_PER_M = 0.0022  # Ohm/m loop resistance (phase + neutral)


def _make_baseline(steps: int, meters: int, seed: int) -> pd.DataFrame:
    """Generate realistic residential multi-day baseline telemetry."""
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    frames: list[pd.DataFrame] = []
    t = np.arange(steps)

    if steps <= 1440:
        daily_phase = 2 * np.pi * t / max(steps, 1)
        morning_evening = 0.35 + 0.55 * np.maximum(0, np.sin(daily_phase - 0.7))
    else:
        # Multi-day support with diurnal cycle and weekend profiles
        minute_of_day = t % 1440
        day_of_week = (t // 1440) % 7
        daily_phase = 2 * np.pi * minute_of_day / 1440.0

        # Weekdays: morning peak (7:00-8:30) and evening peak (18:30-22:00)
        weekday_pattern = (
            0.28
            + 0.52 * np.maximum(0, np.sin(daily_phase - 1.15)) ** 2
            + 0.78 * np.maximum(0, np.sin(daily_phase - 4.45)) ** 2
        )
        # Weekends: later wake-up, active midday, sustained evening
        weekend_pattern = (
            0.32
            + 0.38 * np.maximum(0, np.sin(daily_phase - 1.75)) ** 2
            + 0.25 * np.maximum(0, np.sin(daily_phase - 3.10)) ** 2
            + 0.68 * np.maximum(0, np.sin(daily_phase - 4.60)) ** 2
        )
        is_weekend = (day_of_week >= 5).astype(float)
        morning_evening = (1 - is_weekend) * weekday_pattern + is_weekend * weekend_pattern

    for m in range(meters):
        meter_id = f"meter_{m + 1:03d}"
        building_num = m // 5 + 1
        feeder_num = m // 10 + 1
        distance_m = BUILDING_DISTANCES_M.get(building_num, 50.0 + (building_num - 1) * 110.0)
        household_type = ["small_flat", "family_home", "high_usage_home", "small_flat", "family_home"][m % 5]
        base_kw = {"small_flat": 0.38, "family_home": 0.72, "high_usage_home": 1.05}[household_type]

        random_load = rng.gamma(shape=2.0, scale=0.10, size=steps)
        power = np.clip(base_kw * (0.55 + morning_evening) + random_load, 0.08, 4.5)
        # Add slight asynchronous household variability
        power += 0.06 * np.sin(2 * np.pi * t / max(30, min(180, steps)) + m * 0.17)
        power = np.clip(power, 0.05, 5.0)

        # Physics: Substation bus voltage modulated by grid daily demand curve
        v_substation = 230.0 + 1.2 * np.sin(daily_phase) + rng.normal(0, 0.6, steps)
        pf = np.clip(0.96 + rng.normal(0, 0.012, steps), 0.88, 0.995)
        i_approx = (power * 1000.0) / (230.0 * pf)
        delta_v = CABLE_RESISTANCE_PER_M * distance_m * i_approx
        voltage = np.clip(v_substation - delta_v, 195.0, 253.0)
        current = power * 1000.0 / (voltage * pf)

        frequency = 50.0 + rng.normal(0, 0.015, steps)
        energy = np.cumsum(power / 60.0)

        frames.append(pd.DataFrame({
            "timestamp": start + pd.to_timedelta(t, unit="min"),
            "meter_id": meter_id,
            "household_type": household_type,
            "building_id": f"building_{building_num:02d}",
            "distance_from_transformer_m": distance_m,
            "feeder_id": f"feeder_{feeder_num:02d}",
            "voltage_v": voltage,
            "current_a": current,
            "active_power_kw": power,
            "power_factor": pf,
            "frequency_hz": frequency,
            "energy_kwh": energy,
            "event_type": "normal",
            "anomaly_flag": 0,
            "affected_channel": "none",
            "event_id": "",
        }))
    return pd.concat(frames, ignore_index=True)


def generate_dataset_with_labels(
    steps: int = 1440,
    meters: int = 30,
    seed: int = 42,
    inject_anomalies: bool = True,
    scenarios: Iterable[str] | None = None,
    zones: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a labelled smart-metered neighborhood dataset and standalone labels.csv."""
    if zones is not None:
        meters = zones
    if steps < 120:
        raise ValueError("steps must be at least 120 to fit scenario windows")
    if meters < 1:
        raise ValueError("meters must be >= 1")

    df = _make_baseline(steps, meters, seed)
    empty_labels = pd.DataFrame(columns=[
        "event_id", "event_type", "category", "target_entity", "start_time", "end_time",
        "duration_min", "affected_channel", "severity", "parameters_json"
    ])
    if not inject_anomalies:
        return df, empty_labels

    rng = np.random.default_rng(seed + 101)
    chosen = list(METER_SCENARIOS if scenarios is None else scenarios)
    unknown = sorted(set(chosen) - set(METER_SCENARIOS))
    if unknown:
        raise ValueError(f"unknown scenario(s): {unknown}")

    # Build non-overlapping injection schedule across meters and time
    occurrences_per_scenario = max(1, steps // 2800)
    total_events = len(chosen) * occurrences_per_scenario
    slot_width = max(18, (steps - 40) // total_events)
    duration_nominal = min(50, max(12, int(slot_width * 0.65)))

    planned_events: list[tuple[str, int, int, int]] = []
    event_idx = 0
    for occ in range(occurrences_per_scenario):
        for s_idx, scenario in enumerate(chosen):
            m_idx = (s_idx * 3 + occ * 7) % meters
            start = 20 + event_idx * slot_width
            dur = min(duration_nominal, steps - start - 2)
            planned_events.append((scenario, m_idx, start, dur))
            event_idx += 1

    labels_list: list[dict] = []

    for scenario, meter_index, start, duration in planned_events:
        meter_id = f"meter_{meter_index + 1:03d}"
        mask = df["meter_id"].eq(meter_id)
        meter_indices = df.index[mask]
        idx = meter_indices[start:start + duration]
        if len(idx) == 0:
            continue

        meta = SCENARIO_METADATA.get(scenario, {"category": "data_quality", "severity": 0.70})
        event_id = f"{meter_id}_{scenario}_{start}"
        affected_channel = "multiple"
        params: dict = {}

        df.loc[idx, "event_type"] = scenario
        df.loc[idx, "anomaly_flag"] = 1
        df.loc[idx, "event_id"] = event_id

        if scenario == "consumption_spike":
            original_power = df.loc[idx, "active_power_kw"].to_numpy(copy=True)
            spike_factor = float(rng.uniform(2.2, 3.2))
            spiked_power = original_power * spike_factor
            df.loc[idx, "active_power_kw"] = spiked_power

            dist_m = df.loc[idx, "distance_from_transformer_m"].to_numpy()
            pf_val = df.loc[idx, "power_factor"].to_numpy()
            v_curr = df.loc[idx, "voltage_v"].to_numpy()
            i_curr = df.loc[idx, "current_a"].to_numpy()
            v_sub = v_curr + (CABLE_RESISTANCE_PER_M * dist_m * i_curr)
            i_approx_spike = (spiked_power * 1000.0) / (230.0 * pf_val)
            new_v = np.clip(v_sub - (CABLE_RESISTANCE_PER_M * dist_m * i_approx_spike), 190.0, 253.0)
            df.loc[idx, "voltage_v"] = new_v
            df.loc[idx, "current_a"] = spiked_power * 1000.0 / (new_v * pf_val)

            delta_kwh = np.cumsum((spiked_power - original_power) / 60.0)
            tail_idx = df.index[mask & (df.index >= idx[-1] + 1)]
            df.loc[idx, "energy_kwh"] += delta_kwh
            if len(tail_idx):
                df.loc[tail_idx, "energy_kwh"] += float(delta_kwh[-1])
            affected_channel = "active_power_kw,current_a,energy_kwh"
            params = {"spike_factor": round(spike_factor, 2)}

        elif scenario == "meter_drift":
            drift_max = float(rng.uniform(0.6, 1.2))
            drift = np.linspace(0.0, drift_max, len(idx))
            df.loc[idx, "active_power_kw"] += drift
            affected_channel = "active_power_kw"
            params = {"drift_max_kw": round(drift_max, 2)}

        elif scenario == "constant_bias":
            bias_offset = float(rng.uniform(0.8, 1.5))
            df.loc[idx, "active_power_kw"] += bias_offset
            affected_channel = "active_power_kw"
            params = {"offset_kw": round(bias_offset, 2)}

        elif scenario == "false_data_injection":
            factor = float(rng.choice([0.45, 1.85]))
            df.loc[idx, "active_power_kw"] *= factor
            affected_channel = "active_power_kw"
            params = {"multiplicative_factor": factor}

        elif scenario == "replay_like":
            n = len(idx)
            prior_start = max(0, start - n - 20)
            source = df.loc[meter_indices[prior_start:prior_start + n], MEASUREMENT_COLUMNS].copy()
            if len(source) == n:
                for col in MEASUREMENT_COLUMNS:
                    df.loc[idx, col] = source[col].to_numpy()
            else:
                df.loc[idx, "active_power_kw"] = float(df.loc[idx[0], "active_power_kw"])
            affected_channel = "all_measurements"
            params = {"replayed_from_step": prior_start, "window_length": n}

        elif scenario == "frozen_meter":
            for col in MEASUREMENT_COLUMNS:
                df.loc[idx, col] = float(df.loc[idx[0], col])
            affected_channel = "all_measurements"
            params = {"frozen_value_power": round(float(df.loc[idx[0], "active_power_kw"]), 3)}

        elif scenario == "missing_data":
            df.loc[idx, "active_power_kw"] = np.nan
            affected_channel = "active_power_kw"
            params = {"dropped_channel": "active_power_kw"}

        elif scenario == "energy_power_mismatch":
            energy_shift = float(rng.uniform(1.5, 4.0))
            df.loc[idx, "energy_kwh"] += np.linspace(0.5, energy_shift, len(idx))
            affected_channel = "energy_kwh"
            params = {"total_energy_shift_kwh": round(energy_shift, 2)}

        elif scenario == "random_corruption":
            corruption_type = rng.choice(["extreme_voltage", "impossible_pf", "negative_voltage"])
            if corruption_type == "extreme_voltage":
                df.loc[idx, "voltage_v"] = 999.0
                affected_channel = "voltage_v"
                params = {"type": "extreme_voltage", "value": 999.0}
            elif corruption_type == "impossible_pf":
                df.loc[idx, "power_factor"] = 1.85
                affected_channel = "power_factor"
                params = {"type": "impossible_pf", "value": 1.85}
            else:
                df.loc[idx, "voltage_v"] = -15.0
                affected_channel = "voltage_v"
                params = {"type": "negative_voltage", "value": -15.0}

        elif scenario == "dropout":
            df.loc[idx, "voltage_v"] = 0.0
            df.loc[idx, "current_a"] = 0.0
            df.loc[idx, "active_power_kw"] = 0.0
            affected_channel = "voltage_v,current_a,active_power_kw"
            params = {"type": "complete_signal_collapse"}

        elif scenario == "bias_injection":
            # Stealth theft: 35% scaling down of active power AND current (Ohm's law invariant)
            scale = 0.65
            df.loc[idx, "active_power_kw"] *= scale
            df.loc[idx, "current_a"] *= scale
            affected_channel = "active_power_kw,current_a"
            params = {"type": "proportional_stealth_scaling", "scale": scale}

        elif scenario == "equipment_fault":
            # Inductive breakdown: current surge + severe power factor drop
            df.loc[idx, "current_a"] *= 2.2
            df.loc[idx, "power_factor"] = np.clip(df.loc[idx, "power_factor"] * 0.55, 0.42, 0.60)
            affected_channel = "current_a,power_factor"
            params = {"current_multiplier": 2.2, "pf_degradation": 0.55}

        elif scenario == "grid_event":
            # Feeder-wide grid disturbance: simultaneous 18V sag across all meters on the feeder
            f_id = df.loc[idx[0], "feeder_id"]
            event_times = df.loc[idx, "timestamp"].unique()
            feeder_mask = df["feeder_id"].eq(f_id) & df["timestamp"].isin(event_times)
            feeder_idx = df.index[feeder_mask]
            event_id = f"{f_id}_grid_event_{start}"
            df.loc[feeder_idx, "event_type"] = "grid_event"
            df.loc[feeder_idx, "anomaly_flag"] = 1
            df.loc[feeder_idx, "event_id"] = event_id
            df.loc[feeder_idx, "voltage_v"] = np.maximum(185.0, df.loc[feeder_idx, "voltage_v"] - 18.0)
            df.loc[feeder_idx, "current_a"] = (
                df.loc[feeder_idx, "active_power_kw"] * 1000.0 /
                (df.loc[feeder_idx, "voltage_v"] * df.loc[feeder_idx, "power_factor"])
            )
            affected_channel = "voltage_v,current_a"
            target_entity = f_id
            params = {"sag_v": 18.0, "affected_feeder": f_id, "affected_meter_count": int(df.loc[feeder_idx, "meter_id"].nunique())}

        df.loc[idx, "affected_channel"] = affected_channel

        target_entity = f_id if scenario == "grid_event" else meter_id
        labels_list.append({
            "event_id": event_id,
            "event_type": scenario,
            "category": meta["category"],
            "target_entity": target_entity,
            "start_time": str(df.loc[idx[0], "timestamp"]),
            "end_time": str(df.loc[idx[-1], "timestamp"]),
            "duration_min": len(idx),
            "affected_channel": affected_channel,
            "severity": meta["severity"],
            "parameters_json": json.dumps(params),
        })

    # Recompute feeder aggregate totals
    agg = df.groupby(["timestamp", "feeder_id"], as_index=False, dropna=False).agg(
        neighborhood_feeder_power_kw=("active_power_kw", "sum"),
        active_meter_count=("meter_id", "nunique"),
    )
    df = df.merge(agg, on=["timestamp", "feeder_id"], how="left")
    df = df.sort_values(["timestamp", "meter_id"]).reset_index(drop=True)

    labels_df = pd.DataFrame(labels_list)
    df.attrs["labels"] = labels_df
    return df, labels_df


def generate_dataset(
    steps: int = 1440,
    meters: int = 30,
    seed: int = 42,
    inject_anomalies: bool = True,
    scenarios: Iterable[str] | None = None,
    zones: int | None = None,
) -> pd.DataFrame:
    """Convenience wrapper returning only the telemetry DataFrame."""
    df, _ = generate_dataset_with_labels(
        steps=steps, meters=meters, seed=seed,
        inject_anomalies=inject_anomalies, scenarios=scenarios, zones=zones
    )
    return df


def save_dataset(df: pd.DataFrame, path: str) -> None:
    """Save CSV and create parent directories when needed."""
    output = Path(path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(str(output), index=False)
