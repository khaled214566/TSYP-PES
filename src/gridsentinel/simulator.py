"""Synthetic smart-metered neighborhood telemetry and anomaly injection.

This is an explicitly simplified, reproducible research simulator. It models
household smart meters reporting every minute and an aggregate neighborhood
feeder. It is not a validated distribution-network power-flow simulator.
"""
from __future__ import annotations

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
]
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
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2026-01-01T00:00:00Z")
    frames: list[pd.DataFrame] = []
    t = np.arange(steps)
    # One day if the supplied series spans 1440 samples; otherwise the cycle
    # is compressed to the requested experiment duration for quick tests.
    daily_phase = 2 * np.pi * t / max(steps, 1)
    for m in range(meters):
        meter_id = f"meter_{m + 1:03d}"
        building_num = m // 5 + 1
        feeder_num = m // 10 + 1
        distance_m = BUILDING_DISTANCES_M.get(building_num, 50.0 + (building_num - 1) * 110.0)
        household_type = ["small_flat", "family_home", "high_usage_home", "small_flat", "family_home"][m % 5]
        base_kw = {"small_flat": 0.38, "family_home": 0.72, "high_usage_home": 1.05}[household_type]
        morning_evening = 0.35 + 0.55 * np.maximum(0, np.sin(daily_phase - 0.7))
        random_load = rng.gamma(shape=2.0, scale=0.10, size=steps)
        power = np.clip(base_kw * (0.55 + morning_evening) + random_load, 0.08, 4.5)
        power += 0.06 * np.sin(2 * np.pi * t / max(30, min(180, steps)) + m * 0.17)
        power = np.clip(power, 0.05, 5.0)

        # Physics: Substation bus voltage modulated by distance and dynamic load current
        v_substation = 230 + 1.8 * np.sin(2 * np.pi * t / max(120, min(600, steps)) + m * 0.13) + rng.normal(0, 0.8, steps)
        pf = np.clip(0.96 + rng.normal(0, 0.012, steps), 0.88, 0.995)
        i_approx = (power * 1000.0) / (230.0 * pf)
        delta_v = CABLE_RESISTANCE_PER_M * distance_m * i_approx
        voltage = np.clip(v_substation - delta_v, 195.0, 253.0)
        current = power * 1000 / (voltage * pf)

        frequency = 50 + rng.normal(0, 0.015, steps)
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


def generate_dataset(
    steps: int = 1440,
    meters: int = 30,
    seed: int = 42,
    inject_anomalies: bool = True,
    scenarios: Iterable[str] | None = None,
    zones: int | None = None,
) -> pd.DataFrame:
    """Create a labelled smart-metered-neighborhood dataset.

    ``zones`` is retained as a backward-compatible alias for older prototype
    commands; when supplied it maps to meters, but new work should use meters.
    Each scenario is injected into a distinct window on selected meters.
    """
    if zones is not None:
        meters = zones
    if steps < 120:
        raise ValueError("steps must be at least 120 to fit scenario windows")
    if meters < 1:
        raise ValueError("meters must be >= 1")
    df = _make_baseline(steps, meters, seed)
    if not inject_anomalies:
        return df

    rng = np.random.default_rng(seed + 101)
    chosen = list(METER_SCENARIOS if scenarios is None else scenarios)
    unknown = sorted(set(chosen) - set(METER_SCENARIOS))
    if unknown:
        raise ValueError(f"unknown scenario(s): {unknown}")

    # Rotate scenario ownership across meters so small experiments still get
    # broad coverage, while larger runs distribute scenarios across households.
    slot_width = max(1, steps // (len(chosen) + 1))
    for j, scenario in enumerate(chosen):
        meter_index = j % meters
        meter_id = f"meter_{meter_index + 1:03d}"
        start = int((j + 0.55) * slot_width + rng.integers(-max(1, slot_width // 10), max(2, slot_width // 10)))
        start = min(max(start, 2), steps - 20)
        duration = max(8, min(int(slot_width * 0.55), steps - start))
        mask = df["meter_id"].eq(meter_id)
        meter_indices = df.index[mask]
        idx = meter_indices[start:start + duration]
        if len(idx) == 0:
            continue
        df.loc[idx, "event_type"] = scenario
        df.loc[idx, "anomaly_flag"] = 1
        df.loc[idx, "affected_channel"] = "multiple"
        df.loc[idx, "event_id"] = f"{meter_id}_{scenario}_{start}"

        if scenario == "consumption_spike":
            original_power = df.loc[idx, "active_power_kw"].to_numpy(copy=True)
            spiked_power = original_power * rng.uniform(2.0, 3.2)
            df.loc[idx, "active_power_kw"] = spiked_power

            # Dynamic physics: Increased load current through cable impedance pulls voltage down further
            dist_m = df.loc[idx, "distance_from_transformer_m"].to_numpy()
            pf_val = df.loc[idx, "power_factor"].to_numpy()
            v_curr = df.loc[idx, "voltage_v"].to_numpy()
            i_curr = df.loc[idx, "current_a"].to_numpy()
            v_sub = v_curr + (CABLE_RESISTANCE_PER_M * dist_m * i_curr)
            i_approx_spike = (spiked_power * 1000.0) / (230.0 * pf_val)
            new_v = np.clip(v_sub - (CABLE_RESISTANCE_PER_M * dist_m * i_approx_spike), 190.0, 253.0)
            df.loc[idx, "voltage_v"] = new_v
            df.loc[idx, "current_a"] = spiked_power * 1000.0 / (new_v * pf_val)
            # Treat this scenario as a genuine load change: cumulative energy
            # should increase by the additional consumed energy.
            delta_kwh = np.cumsum((spiked_power - original_power) / 60.0)
            tail_idx = df.index[mask & (df.index >= idx[-1] + 1)]
            df.loc[idx, "energy_kwh"] += delta_kwh
            if len(tail_idx):
                df.loc[tail_idx, "energy_kwh"] += float(delta_kwh[-1])
            df.loc[idx, "affected_channel"] = "active_power_kw,current_a,energy_kwh"
        elif scenario == "meter_drift":
            drift = np.linspace(0.0, rng.uniform(0.4, 0.9), len(idx))
            df.loc[idx, "active_power_kw"] += drift
            # Current and energy remain unchanged: this is a drift in the
            # reported power channel, not a true increase in household load.
            df.loc[idx, "affected_channel"] = "active_power_kw"
        elif scenario == "constant_bias":
            df.loc[idx, "active_power_kw"] += rng.uniform(0.7, 1.3)
            df.loc[idx, "affected_channel"] = "active_power_kw"
        elif scenario == "false_data_injection":
            # Alter reported power without updating the companion current value.
            df.loc[idx, "active_power_kw"] *= rng.choice([0.55, 1.65])
            df.loc[idx, "affected_channel"] = "active_power_kw"
        elif scenario == "replay_like":
            n = len(idx)
            prior_start = max(0, start - n - 10)
            source = df.loc[meter_indices[prior_start:prior_start + n], MEASUREMENT_COLUMNS].copy()
            if len(source) == n:
                for col in MEASUREMENT_COLUMNS:
                    df.loc[idx, col] = source[col].to_numpy()
            else:
                df.loc[idx, "active_power_kw"] = float(df.loc[idx[0], "active_power_kw"])
            df.loc[idx, "affected_channel"] = "multiple"
        elif scenario == "frozen_meter":
            for col in MEASUREMENT_COLUMNS:
                df.loc[idx, col] = float(df.loc[idx[0], col])
            df.loc[idx, "affected_channel"] = "multiple"
        elif scenario == "missing_data":
            df.loc[idx, "active_power_kw"] = np.nan
            df.loc[idx, "affected_channel"] = "active_power_kw"
        elif scenario == "energy_power_mismatch":
            df.loc[idx, "energy_kwh"] += np.linspace(0.8, 3.8, len(idx))
            df.loc[idx, "affected_channel"] = "energy_kwh"

    # Recompute aggregate feeder measurements per timestamp. These are
    # simulated totals, not independent physical feeder-meter measurements.
    agg = df.groupby(["timestamp", "feeder_id"], as_index=False, dropna=False).agg(
        neighborhood_feeder_power_kw=("active_power_kw", "sum"),
        active_meter_count=("meter_id", "nunique"),
    )
    df = df.merge(agg, on=["timestamp", "feeder_id"], how="left")
    return df.sort_values(["meter_id", "timestamp"]).reset_index(drop=True)


def save_dataset(df: pd.DataFrame, path: str) -> None:
    """Save CSV and create parent directories when needed."""
    from pathlib import Path
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
