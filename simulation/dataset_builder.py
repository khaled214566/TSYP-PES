import os
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from simulation.generators.baseline_generator import BaselineGenerator
from simulation.generators.anomaly_injector import AnomalyInjector
from simulation.scenarios.demo_scenarios import (
    generate_scenario_a_grid_event,
    generate_scenario_b_sensor_bias,
    generate_scenario_c_falsified_data
)

def run_pipeline():
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "simulation" / "config" / "simulation_config.yaml"
    
    print(f"[+] Loading simulation config from {config_path}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    gen_dir = data_dir / "generated"
    proc_dir = data_dir / "processed"
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    test_dir = data_dir / "test"
    
    for d in [raw_dir, gen_dir, proc_dir, train_dir, val_dir, test_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    # 1. Generate Clean Baseline
    print("[+] Step 1: Generating 30-day multi-sensor clean baseline...")
    baseline_gen = BaselineGenerator(config)
    baseline_df = baseline_gen.generate()
    raw_file = raw_dir / "baseline_30d.csv"
    baseline_df.to_csv(raw_file, index=False)
    print(f"    Saved baseline ({len(baseline_df):,} rows) -> {raw_file}")
    
    # 2. Inject Anomaly Matrix
    print("[+] Step 2: Injecting 10 anomaly types & tracking metadata...")
    injector = AnomalyInjector(config)
    full_dataset, labels_df = injector.inject(baseline_df)
    
    master_file = gen_dir / "full_dataset.csv"
    labels_file = gen_dir / "labels.csv"
    full_dataset.to_csv(master_file, index=False)
    labels_df.to_csv(labels_file, index=False)
    
    anom_count = full_dataset["is_anomaly"].sum()
    print(f"    Saved master dataset -> {master_file}")
    print(f"    Saved labels metadata ({len(labels_df)} events) -> {labels_file}")
    print(f"    Total anomalous timesteps: {anom_count:,} ({anom_count/len(full_dataset)*100:.2f}%)")
    
    # 3. Pre-generate 3 Competition Demo Scenarios
    print("[+] Step 3: Generating pre-packaged judging scenarios...")
    scenarios_dir = data_dir / "scenarios"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    
    # Demo window: 24h sample from baseline
    t_min = baseline_df["timestamp"].min()
    demo_base = baseline_df[baseline_df["timestamp"] < t_min + pd.Timedelta(days=2)].copy()
    
    df_scen_a, meta_a = generate_scenario_a_grid_event(demo_base, config)
    df_scen_a.to_csv(scenarios_dir / "scenario_a_genuine_grid_event.csv", index=False)
    
    df_scen_b, meta_b = generate_scenario_b_sensor_bias(demo_base, config)
    df_scen_b.to_csv(scenarios_dir / "scenario_b_sensor_bias.csv", index=False)
    
    df_scen_c, meta_c = generate_scenario_c_falsified_data(demo_base, config)
    df_scen_c.to_csv(scenarios_dir / "scenario_c_falsified_data.csv", index=False)
    print("    Pre-packaged Scenarios A, B, and C saved to data/scenarios/")
    
    # 4. Feature Engineering for ML Readiness
    print("[+] Step 4: Extracting temporal & statistical features...")
    df_feat = full_dataset.copy()
    df_feat["hour"] = pd.to_datetime(df_feat["timestamp"]).dt.hour
    df_feat["dayofweek"] = pd.to_datetime(df_feat["timestamp"]).dt.dayofweek
    
    # Rolling statistics per sensor
    df_feat = df_feat.sort_values(by=["sensor_id", "timestamp"]).reset_index(drop=True)
    df_feat["v_rolling_mean_15"] = df_feat.groupby("sensor_id")["voltage"].transform(lambda x: x.rolling(15, min_periods=1).mean())
    df_feat["v_rolling_std_15"] = df_feat.groupby("sensor_id")["voltage"].transform(lambda x: x.rolling(15, min_periods=1).std().fillna(0))
    df_feat["v_residual"] = df_feat["voltage"] - df_feat["v_rolling_mean_15"]
    
    # Power residual and current surge index
    df_feat["p_rolling_mean_15"] = df_feat.groupby("sensor_id")["active_power"].transform(lambda x: x.rolling(15, min_periods=1).mean())
    df_feat["p_residual"] = df_feat["active_power"] - df_feat["p_rolling_mean_15"]
    
    processed_file = proc_dir / "features.csv"
    df_feat.to_csv(processed_file, index=False)
    print(f"    Saved processed feature matrix -> {processed_file}")
    
    # 5. Stratified Chronological Split (70% train / 15% val / 15% test)
    print("[+] Step 5: Partitioning 70/15/15 train/val/test splits...")
    timestamps_sorted = sorted(df_feat["timestamp"].unique())
    n_ts = len(timestamps_sorted)
    idx_train_end = int(n_ts * config["split"]["train"])
    idx_val_end = int(n_ts * (config["split"]["train"] + config["split"]["val"]))
    
    ts_train = set(timestamps_sorted[:idx_train_end])
    ts_val = set(timestamps_sorted[idx_train_end:idx_val_end])
    ts_test = set(timestamps_sorted[idx_val_end:])
    
    train_mask = df_feat["timestamp"].isin(ts_train)
    val_mask = df_feat["timestamp"].isin(ts_val)
    test_mask = df_feat["timestamp"].isin(ts_test)
    
    feature_cols = [
        "voltage", "current", "active_power", "power_factor", "energy_consumption",
        "hour", "dayofweek", "v_rolling_mean_15", "v_rolling_std_15", "v_residual",
        "p_rolling_mean_15", "p_residual"
    ]
    target_cols = ["is_anomaly", "anomaly_type"]
    
    # Train
    df_feat[train_mask][feature_cols].to_csv(train_dir / "X_train.csv", index=False)
    df_feat[train_mask][target_cols].to_csv(train_dir / "y_train.csv", index=False)
    
    # Val
    df_feat[val_mask][feature_cols].to_csv(val_dir / "X_val.csv", index=False)
    df_feat[val_mask][target_cols].to_csv(val_dir / "y_val.csv", index=False)
    
    # Test
    df_feat[test_mask][feature_cols].to_csv(test_dir / "X_test.csv", index=False)
    df_feat[test_mask][target_cols].to_csv(test_dir / "y_test.csv", index=False)
    
    print(f"    Train size: {train_mask.sum():,} rows")
    print(f"    Val size:   {val_mask.sum():,} rows")
    print(f"    Test size:  {test_mask.sum():,} rows")
    print("[+] Data generation pipeline complete!")

if __name__ == "__main__":
    run_pipeline()
