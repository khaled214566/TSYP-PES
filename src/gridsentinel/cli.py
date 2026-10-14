"""CLI runner for GridSentinel smart-metered neighborhood simulation and evaluation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

from .simulator import generate_dataset_with_labels, save_dataset
from .detector import GridSentinelDetector


def build_audit_log(scored: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    """Build simulated human-in-the-loop audit trail for Pillar 3 governance."""
    audit_records = []
    role_map = {
        "GENUINE_GRID_EVENT": "Substation Automated Dispatch Controller",
        "FALSIFICATION_ATTACK": "Revenue Protection & Cybersecurity Specialist",
        "DATA_QUALITY_ISSUE": "AMI Meter Operations & Communication Lead",
        "EQUIPMENT_FAULT": "Distribution Equipment Protection Engineer",
        "NORMAL": "System Telemetry Supervisor",
    }

    for idx, row in labels.iterrows():
        e_id = row["event_id"]
        matching = scored[scored["event_id"] == e_id]
        if len(matching) == 0:
            continue

        dominant_verdict = matching["verdict"].mode().iloc[0]
        dominant_class = matching["event_class"].mode().iloc[0]
        dominant_tier = matching["escalation_tier"].mode().iloc[0]
        mean_conf = float(matching["confidence"].mean())

        if dominant_tier == "AUTO_ACTION":
            operator_action = "AUTOMATICALLY_EXECUTED_BY_AI"
            status = "CLOSED_VERIFIED"
        elif dominant_tier == "OPERATOR_APPROVAL":
            operator_action = "OPERATOR_REVIEWED_AND_CONFIRMED"
            status = "ACTION_DISPATCHED"
        else:
            operator_action = "QUARANTINED_FOR_FIELD_INVESTIGATION"
            status = "PENDING_FIELD_REPORT"

        audit_records.append({
            "audit_id": f"AUD-{idx + 1:04d}",
            "timestamp": row["start_time"],
            "event_id": e_id,
            "target_entity": row["target_entity"],
            "event_type": row["event_type"],
            "event_class": dominant_class,
            "verdict": dominant_verdict,
            "confidence": round(mean_conf, 3),
            "escalation_tier": dominant_tier,
            "assigned_role": role_map.get(dominant_class, "Operations Analyst"),
            "operator_action": operator_action,
            "audit_status": status,
            "feedback_to_model": "TRUE_POSITIVE_VERIFIED",
            "audit_note": matching["explanation"].iloc[0] if "explanation" in matching.columns else "Event processed.",
        })

    return pd.DataFrame(audit_records)


def build_pattern_registry(labels: pd.DataFrame) -> dict:
    """Build anonymized Noosphere collective intelligence pattern registry for Pillar 4."""
    signatures = [
        {
            "pattern_id": "PAT_GRID_DISTURBANCE_01",
            "type": "feeder_voltage_sag",
            "category": "real_event",
            "consensus_signature": {
                "feeder_consensus_threshold": 0.70,
                "nominal_sag_delta_v": -18.0,
                "line_impedance_physics_valid": True,
            },
            "privacy_guarantee": "Zero customer telemetry exposed; only feeder-level consensus ratios shared.",
            "recommended_action": "dispatch_distribution_voltage_regulation",
        },
        {
            "pattern_id": "PAT_STEALTH_THEFT_02",
            "type": "bias_injection",
            "category": "falsification",
            "consensus_signature": {
                "power_current_proportional_scaling": 0.65,
                "rolling_energy_residual_threshold_kwh": 0.0018,
                "voltage_stability": "nominal_230V",
            },
            "privacy_guarantee": "Zero customer telemetry exposed; only dimensionless residual fingerprints shared.",
            "recommended_action": "dispatch_field_tamper_inspection_and_quarantine",
        },
        {
            "pattern_id": "PAT_SEQUENCE_REPLAY_03",
            "type": "replay_like",
            "category": "falsification",
            "consensus_signature": {
                "temporal_vector_entropy_match": 4,
                "buffer_lag_min": 20,
            },
            "privacy_guarantee": "Zero raw waveforms exposed; sequence hash collision signature only.",
            "recommended_action": "request_operator_review_and_check_meter_health",
        },
        {
            "pattern_id": "PAT_INDUCTIVE_FAULT_04",
            "type": "equipment_fault",
            "category": "real_event",
            "consensus_signature": {
                "pf_collapse_threshold": 0.65,
                "current_surge_multiplier": 1.8,
            },
            "privacy_guarantee": "Aggregated impedance profile shared across distribution districts.",
            "recommended_action": "quarantine_circuit_and_inspect_inductive_load",
        },
    ]

    return {
        "node_id": "ENERGYMIND_NODE_TUNISIA_DISTRICT_01",
        "protocol_version": "Noosphere-v1.0-Federated",
        "generated_timestamp": "2026-10-14T18:00:00Z",
        "node_district": "STEG_Residential_Microgrid",
        "privacy_compliance": "Decentralized / GDPR & STEG Smart Grid Data Protection Standard",
        "shared_pattern_count": len(signatures),
        "patterns": signatures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a smart-metered neighborhood and run GridSentinel")
    parser.add_argument("--steps", type=int, default=10080, help="one-minute samples per meter (default: 10080 = 7 days)")
    parser.add_argument("--meters", type=int, default=30, help="number of household smart meters (default: 30)")
    parser.add_argument("--zones", type=int, default=None, help="deprecated alias for --meters")
    parser.add_argument("--seed", type=int, default=42, help="random seed (default: 42)")
    parser.add_argument("--out", default="data/generated", help="output directory (default: data/generated)")
    args = parser.parse_args()

    meters = args.zones if args.zones is not None else args.meters
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"=== GridSentinel Simulation & Trust Layer Evaluation ===")
    print(f"Configuration: {meters} household meters, {args.steps} one-minute samples per meter ({args.steps / 1440:.1f} days, Seed: {args.seed})")

    # Generate baseline normal training data and scenario-injected evaluation data
    train, _ = generate_dataset_with_labels(steps=args.steps, meters=meters, seed=args.seed, inject_anomalies=False)
    test, labels = generate_dataset_with_labels(steps=args.steps, meters=meters, seed=args.seed + 1, inject_anomalies=True)

    # Train and score
    detector = GridSentinelDetector().fit(train)
    scored = detector.predict(test)

    # Build Governance Audit Log & Noosphere Pattern Registry
    audit_df = build_audit_log(scored, labels)
    pattern_registry = build_pattern_registry(labels)

    # Save artifacts
    save_dataset(train, str(out / "normal_training.csv"))
    save_dataset(scored, str(out / "scored_demo.csv"))
    save_dataset(labels, str(out / "labels.csv"))
    save_dataset(audit_df, str(out / "audit_log.csv"))

    with open(out / "pattern_registry.json", "w") as f:
        json.dump(pattern_registry, f, indent=2)

    # Multi-dimensional summary
    summary = scored.groupby(["event_type", "verdict", "event_class", "escalation_tier"], dropna=False).size().rename("rows").reset_index()
    summary.to_csv(out / "summary.csv", index=False)

    # Metrics computation
    binary_predicted = (scored["verdict"] != "TRUSTED")
    metrics = {
        "precision": precision_score(scored.anomaly_flag, binary_predicted, zero_division=0),
        "recall": recall_score(scored.anomaly_flag, binary_predicted, zero_division=0),
        "f1": f1_score(scored.anomaly_flag, binary_predicted, zero_division=0),
    }
    normal_rows = scored[scored.anomaly_flag == 0]
    metrics["false_positive_rate"] = float((normal_rows["verdict"] != "TRUSTED").mean()) if len(normal_rows) else 0.0

    print(f"\nSaved artifacts to {out.resolve()}:")
    print(f"  - normal_training.csv ({len(train)} rows)")
    print(f"  - scored_demo.csv ({len(scored)} rows)")
    print(f"  - labels.csv ({len(labels)} injected events)")
    print(f"  - audit_log.csv ({len(audit_df)} governance records)")
    print(f"  - pattern_registry.json ({pattern_registry['shared_pattern_count']} shared Noosphere patterns)")
    print(f"  - summary.csv ({len(summary)} breakdown records)")

    print("\n--- Key Challenge Scenario Verification ---")
    grid_rows = scored[scored["event_type"] == "grid_event"]
    grid_actionable = (grid_rows["verdict"] == "ACTIONABLE_GRID_EVENT").mean() if len(grid_rows) else 0.0
    print(f"Scenario A (Genuine Grid Event): {grid_actionable * 100:.1f}% confirmed as ACTIONABLE_GRID_EVENT (High Confidence)")

    theft_rows = scored[scored["event_type"] == "bias_injection"]
    theft_caught = (theft_rows["verdict"] == "SUSPICIOUS").mean() if len(theft_rows) else 0.0
    print(f"Scenario C (Stealth Theft / Bias Injection): {theft_caught * 100:.1f}% detected as SUSPICIOUS")

    replay_rows = scored[scored["event_type"] == "replay_like"]
    replay_caught = (replay_rows["verdict"] == "SUSPICIOUS").mean() if len(replay_rows) else 0.0
    print(f"Scenario C (Telemetry Replay Attack): {replay_caught * 100:.1f}% detected as SUSPICIOUS")

    drift_rows = scored[scored["event_type"] == "meter_drift"]
    drift_caught = (drift_rows["verdict"] == "SUSPICIOUS").mean() if len(drift_rows) else 0.0
    print(f"Scenario B (Sensor Drift): {drift_caught * 100:.1f}% detected as SUSPICIOUS")

    print(f"\n--- Overall Detection Performance ---")
    print(f"Precision: {metrics['precision']:.3f}")
    print(f"Recall:    {metrics['recall']:.3f}")
    print(f"F1 Score:  {metrics['f1']:.3f}")
    print(f"Normal False Positive Rate: {metrics['false_positive_rate'] * 100:.2f}%")

    print("\n--- Verdict Distribution by Scenario ---")
    crosstab_verdict = pd.crosstab(scored["event_type"], scored["verdict"])
    print(crosstab_verdict.to_string())

    print("\n--- Event Classification Distribution ---")
    crosstab_class = pd.crosstab(scored["event_type"], scored["event_class"])
    print(crosstab_class.to_string())

    print("\n--- Governance Escalation Tier Distribution ---")
    print(scored["escalation_tier"].value_counts().to_string())


if __name__ == "__main__":
    main()
