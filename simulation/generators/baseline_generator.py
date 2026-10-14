import numpy as np
import pandas as pd
from typing import Dict, Any

class BaselineGenerator:
    """
    Generates realistic nominal baseline energy time-series data for multiple sensors.
    Simulates diurnal (24h) and weekly cycles, base loads, realistic voltage/power physics, and natural noise.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sim_cfg = config["simulation"]
        self.sig_cfg = config["signals"]
        self.num_sensors = self.sim_cfg["num_sensors"]
        self.interval_min = self.sim_cfg["sampling_interval_minutes"]
        self.duration_days = self.sim_cfg["duration_days"]
        self.start_date = pd.to_datetime(self.sim_cfg.get("start_date", "2026-09-01T00:00:00"))
        self.seed = self.sim_cfg.get("seed", 42)
        
    def generate(self) -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        total_minutes = self.duration_days * 24 * 60
        num_steps = total_minutes // self.interval_min
        
        timestamps = pd.date_range(
            start=self.start_date,
            periods=num_steps,
            freq=f"{self.interval_min}min"
        )
        
        # Diurnal pattern based on hour of day
        minute_of_day = timestamps.hour * 60 + timestamps.minute
        # Diurnal cycle: morning peak (8-10am) & evening peak (6-9pm)
        morning_peak = np.exp(-((minute_of_day - 540) ** 2) / (2 * (90 ** 2)))
        evening_peak = 1.3 * np.exp(-((minute_of_day - 1230) ** 2) / (2 * (100 ** 2)))
        night_dip = -0.3 * np.exp(-((minute_of_day - 240) ** 2) / (2 * (120 ** 2)))
        base_cycle = 1.0 + 0.35 * morning_peak + 0.45 * evening_peak + night_dip
        
        # Weekend load factor (lower industrial/commercial consumption)
        weekend_factor = np.where(timestamps.dayofweek >= 5, 0.85, 1.0)
        demand_profile = base_cycle * weekend_factor
        
        dfs = []
        for s_idx in range(1, self.num_sensors + 1):
            sensor_id = f"S-{s_idx:02d}"
            # Sensor specific baseline variability
            sensor_seed = self.seed + s_idx * 101
            s_rng = np.random.default_rng(sensor_seed)
            sensor_scale = s_rng.uniform(0.85, 1.15)
            
            # Active power (kW)
            nom_power = self.sig_cfg["active_power"]["nominal"] * sensor_scale
            power_noise = s_rng.normal(0, self.sig_cfg["active_power"]["noise_std"], size=num_steps)
            active_power = np.maximum(0.2, nom_power * demand_profile + power_noise)
            
            # Power factor typically slightly dips during high reactive demand
            nom_pf = self.sig_cfg["power_factor"]["nominal"]
            pf_noise = s_rng.normal(0, self.sig_cfg["power_factor"]["noise_std"], size=num_steps)
            power_factor = np.clip(nom_pf - 0.03 * (demand_profile - 1.0) + pf_noise, 0.75, 0.99)
            
            # Grid voltage (V) typically exhibits slight sag under high load
            nom_v = self.sig_cfg["voltage"]["nominal"]
            v_noise = s_rng.normal(0, self.sig_cfg["voltage"]["noise_std"], size=num_steps)
            voltage = nom_v - 2.5 * (demand_profile - 1.0) + v_noise
            
            # Current I = P / (V * PF) * 1000 (A)
            current = (active_power * 1000.0) / (voltage * power_factor)
            
            # Energy consumption per interval: kWh = kW * (interval_min / 60)
            energy_consumption = active_power * (self.interval_min / 60.0)
            
            sensor_df = pd.DataFrame({
                "timestamp": timestamps,
                "sensor_id": sensor_id,
                "voltage": np.round(voltage, 2),
                "current": np.round(current, 2),
                "active_power": np.round(active_power, 3),
                "power_factor": np.round(power_factor, 3),
                "energy_consumption": np.round(energy_consumption, 4),
                "is_anomaly": False,
                "anomaly_type": None
            })
            dfs.append(sensor_df)
            
        full_baseline = pd.concat(dfs, ignore_index=True)
        full_baseline = full_baseline.sort_values(by=["timestamp", "sensor_id"]).reset_index(drop=True)
        return full_baseline
