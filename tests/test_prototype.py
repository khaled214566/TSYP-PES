import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gridsentinel.simulator import generate_dataset, generate_dataset_with_labels, METER_SCENARIOS
from gridsentinel.detector import GridSentinelDetector


def test_neighborhood_generator_is_reproducible_and_meter_labelled():
    a = generate_dataset(steps=240, meters=10, seed=7)
    b = generate_dataset(steps=240, meters=10, seed=7)
    assert a.equals(b)
    assert {"meter_id", "building_id", "distance_from_transformer_m", "feeder_id", "energy_kwh", "neighborhood_feeder_power_kw", "event_type", "anomaly_flag"}.issubset(a.columns)
    assert set(a.event_type.unique()) >= {"normal", "consumption_spike", "meter_drift"}
    assert a.meter_id.nunique() == 10

    # Verify labels generation
    df, labels = generate_dataset_with_labels(steps=240, meters=10, seed=7)
    assert len(labels) == len(METER_SCENARIOS)
    assert {"event_id", "event_type", "category", "target_entity", "start_time", "end_time", "duration_min", "parameters_json"}.issubset(labels.columns)


def test_detector_outputs_required_fields_and_dual_classification():
    train = generate_dataset(steps=240, meters=10, seed=11, inject_anomalies=False)
    test = generate_dataset(steps=240, meters=10, seed=12, inject_anomalies=True)
    result = GridSentinelDetector().fit(train).predict(test)
    assert {"anomaly_score", "flagged", "verdict", "event_class", "diagnosis", "evidence", "recommended_action", "confidence", "escalation_tier"}.issubset(result.columns)
    assert result["verdict"].isin(["TRUSTED", "ACTIONABLE_GRID_EVENT", "SUSPICIOUS", "UNCERTAIN", "COMPROMISED"]).all()
    assert result["event_class"].isin(["NORMAL", "GENUINE_GRID_EVENT", "DATA_QUALITY_ISSUE", "FALSIFICATION_ATTACK", "EQUIPMENT_FAULT"]).all()
    assert result["escalation_tier"].isin(["AUTO_ACTION", "OPERATOR_APPROVAL", "HUMAN_INVESTIGATION"]).all()
    assert set(METER_SCENARIOS).issubset(set(test.event_type.unique()))


def test_scenario_a_feeder_grid_event_confirmed_by_consensus():
    train = generate_dataset(steps=240, meters=10, seed=21, inject_anomalies=False)
    test = generate_dataset(steps=240, meters=10, seed=22, inject_anomalies=True)
    result = GridSentinelDetector().fit(train).predict(test)
    grid_rows = result[result["event_type"] == "grid_event"]
    assert len(grid_rows) > 0
    # Scenario A must be recognized as actionable grid event with high confidence
    assert (grid_rows["verdict"] == "ACTIONABLE_GRID_EVENT").all()
    assert (grid_rows["event_class"] == "GENUINE_GRID_EVENT").all()
    assert (grid_rows["confidence"] >= 0.90).all()


def test_scenario_c_stealth_falsification_detected():
    train = generate_dataset(steps=240, meters=10, seed=31, inject_anomalies=False)
    test = generate_dataset(steps=240, meters=10, seed=32, inject_anomalies=True)
    result = GridSentinelDetector().fit(train).predict(test)

    bias_rows = result[result["event_type"] == "bias_injection"]
    assert len(bias_rows) > 0
    bias_flagged_ratio = (bias_rows["verdict"] == "SUSPICIOUS").mean()
    assert bias_flagged_ratio >= 0.80

    replay_rows = result[result["event_type"] == "replay_like"]
    assert len(replay_rows) > 0
    replay_flagged_ratio = (replay_rows["verdict"] == "SUSPICIOUS").mean()
    assert replay_flagged_ratio >= 0.80
