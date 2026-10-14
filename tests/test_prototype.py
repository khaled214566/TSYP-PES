import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gridsentinel.simulator import generate_dataset, METER_SCENARIOS
from gridsentinel.detector import GridSentinelDetector


def test_neighborhood_generator_is_reproducible_and_meter_labelled():
    a = generate_dataset(steps=240, meters=10, seed=7)
    b = generate_dataset(steps=240, meters=10, seed=7)
    assert a.equals(b)
    assert {"meter_id", "building_id", "feeder_id", "energy_kwh", "neighborhood_feeder_power_kw", "event_type", "anomaly_flag"}.issubset(a.columns)
    assert set(a.event_type.unique()) >= {"normal", "consumption_spike", "meter_drift"}
    assert a.meter_id.nunique() == 10


def test_detector_outputs_required_fields_on_smart_meter_data():
    train = generate_dataset(steps=240, meters=10, seed=11, inject_anomalies=False)
    test = generate_dataset(steps=240, meters=10, seed=12, inject_anomalies=True)
    result = GridSentinelDetector().fit(train).predict(test)
    assert {"anomaly_score", "flagged", "verdict", "evidence", "recommended_action"}.issubset(result.columns)
    assert result["verdict"].isin(["TRUSTED", "SUSPICIOUS", "COMPROMISED", "UNCERTAIN"]).all()
    assert set(METER_SCENARIOS).issubset(set(test.event_type.unique()))
