# Data Notes & Artifact Registry

All data in this project is synthetic and generated locally by `src/gridsentinel/simulator.py` for the TSYP14 EnergyMind Tunisia challenge.

## Generated Artifacts (`data/generated/`)

- **`normal_training.csv` (302,400 rows)**: 7-day baseline smart-meter telemetry representing 30 households across 1-minute intervals, modeling realistic diurnal curves, weekday routines, and weekend consumption shifts.
- **`scored_demo.csv` (302,400 rows)**: 7-day evaluation telemetry passed through the AI Trust Layer. Contains anomaly scores, physical/spatial evidence codes, dual-layer verdicts (`verdict` and `event_class`), plain-language diagnosis, natural language explanation, recommended actions, calibrated confidence scores, and governance escalation tiers (`escalation_tier`).
- **`labels.csv` (39 injected events)**: Comprehensive ground-truth event registry recording every injected anomaly episode across the 7 days (event ID, scenario type, category, target entity, start/end timestamps, duration, affected channels, severity, and parameters JSON).
- **`audit_log.csv` (39 governance records)**: Simulated human-in-the-loop audit trail fulfilling **Pillar 3 (Human-AI Escalation and Governance)**, logging event timestamps, assigned operator roles, operator actions, and model feedback verification.
- **`pattern_registry.json` (4 shared patterns)**: Anonymized Noosphere collective intelligence pattern registry fulfilling **Pillar 4 (Shared Learning Across the Noosphere)**, demonstrating how nodes share mathematical disturbance signatures without leaking customer raw telemetry.
- **`summary.csv`**: Breakdown table cross-tabulating event types against trust verdicts, event classifications, and escalation tiers.
- **`sample/sample_scored_rows.csv`**: 28-row representative sample across all 14 event types for lightweight inspection and smoke tests.

## Data Schema (`scored_demo.csv`)

| Field | Type | Description |
|---|---|---|
| `timestamp` | datetime | UTC timestamp (minute resolution) |
| `meter_id` | string | Unique household smart meter identifier |
| `household_type` | string | Profile (`small_flat`, `family_home`, `high_usage_home`) |
| `building_id` | string | Building group identifier |
| `feeder_id` | string | Feeder cohort identifier |
| `voltage_v` | float | Single-phase voltage (V) |
| `current_a` | float | Line current (A) |
| `active_power_kw` | float | Active power (kW) |
| `power_factor` | float | Dimensionless power factor (0–1) |
| `frequency_hz` | float | Grid frequency (Hz, nominal 50 Hz) |
| `energy_kwh` | float | Smart meter cumulative energy register (kWh) |
| `event_type` | string | Ground-truth injected scenario |
| `anomaly_flag` | int | 0 = Normal, 1 = Injected event |
| `affected_channel` | string | Injected channel(s) |
| `event_id` | string | Unique event identifier mapping to `labels.csv` |
| `neighborhood_feeder_power_kw` | float | Aggregate feeder load |
| `active_meter_count` | int | Active meters reporting on feeder |
| `anomaly_score` | float | Normalized ML decision score [0, 1] |
| `ml_anomaly` | bool | Isolation Forest outlier flag |
| `flagged` | bool | Combined model or rule flag |
| `verdict` | string | Trust layer verdict (`TRUSTED`, `ACTIONABLE_GRID_EVENT`, `SUSPICIOUS`, `UNCERTAIN`) |
| `event_class` | string | Classification (`NORMAL`, `GENUINE_GRID_EVENT`, `DATA_QUALITY_ISSUE`, `FALSIFICATION_ATTACK`, `EQUIPMENT_FAULT`) |
| `diagnosis` | string | Diagnostic summary |
| `explanation` | string | Inspectable natural-language explanation for operators and judges |
| `evidence` | string | Semicolon-separated rule/physical evidence codes |
| `recommended_action` | string | Prescribed operational response |
| `confidence` | float | Calibrated composite confidence score [0.0, 1.0] |
| `escalation_tier` | string | 3-tier governance escalation (`AUTO_ACTION`, `OPERATOR_APPROVAL`, `HUMAN_INVESTIGATION`) |
| `confidence_note` | string | Calibrated multi-evidence indicator metadata |
