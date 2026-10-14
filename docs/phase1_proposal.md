# GridSentinel: Trustworthy AI for a Smart-Metered Neighborhood

**Challenge:** TSYP14 EnergyMind Tunisia — *Architects of the Energy Noosphere: A Human-AI Collective Intelligence Network for Energy Resilience*  
**Phase:** Phase 1 — Ideation & Data Exploration  
**Status:** Revised proposal draft aligned with the selected smart-metered-neighborhood scope.

## 1. Problem statement

A smart-metered neighborhood produces time-stamped household measurements that can support energy visibility and resilience. However, downstream monitoring can be misled by missing readings, meter drift, repeated or replayed values, altered measurements, and genuine changes in household demand. These cases should not be conflated: an unusual consumption pattern is not, by itself, proof of a faulty meter, electricity theft, or malicious behavior.

GridSentinel proposes an explainable trust layer that monitors individual smart-meter streams and neighborhood feeder aggregates. It flags abnormal observations, presents evidence and uncertainty, supports human review, records decisions, and provides a privacy-aware approach for sharing validated event summaries between monitoring nodes.

The design addresses the challenge themes of anomaly/bias detection, confidence and plain-language explanations, human–AI governance, and privacy-conscious collective learning.

## 2. Chosen scope and objectives

### Scope: a simulated smart-metered neighborhood

The Phase 1 prototype represents a small residential neighborhood using synthetic smart meters. Each meter represents a household and belongs to a building and a feeder group. Measurements are sampled at one-minute intervals and include voltage, current, active power, power factor, frequency, and cumulative energy. The simulator also computes a neighborhood feeder-power aggregate by timestamp and feeder group.

The prototype does **not** connect to STEG or real smart meters. The feeder aggregate is calculated from simulated household records; it is not an independent physical feeder-meter reading. The electrical and household-load models are simplified and must not be described as a validated power-flow or consumer-behavior model.

### Objectives

1. Generate reproducible, labelled smart-meter data for multiple household profiles.
2. Inject distinguishable consumption and data-quality/integrity scenarios.
3. Detect unusual meter readings with an Isolation Forest baseline and transparent consistency rules.
4. Provide evidence, a heuristic anomaly indicator, a conservative verdict, and a recommended review action.
5. Analyze the neighborhood aggregate as a context signal for feeder-level demand peaks and unusual aggregate changes.
6. Define human review, auditability, and privacy-aware sharing of compact event summaries.

### Out of scope for Phase 1

Live metering, direct STEG integration, automatic disconnection, autonomous grid control, definitive fraud/theft detection, production-grade federated learning, and claims of real-world performance are out of scope. These require access authorization, domain validation, security and privacy assessment, and operational approval.

## 3. Data and anomaly-simulation plan

### Baseline data

The generator creates household smart-meter records at one-minute intervals. Each record includes:

- `timestamp`, `meter_id`, `household_type`, `building_id`, and `feeder_id`;
- `voltage_v`, `current_a`, `active_power_kw`, `power_factor`, and `frequency_hz`;
- cumulative `energy_kwh`;
- ground-truth `event_type`, `anomaly_flag`, `affected_channel`, and `event_id` for evaluation.

The baseline uses three illustrative household profiles with different typical load levels, smooth synthetic time variation, and random variation. It approximates single-phase active power as

\[P_{kW} \approx \frac{V I PF}{1000}.\]

The neighborhood feeder-power total is computed by summing household active power for each timestamp and feeder group. It is a derived simulation signal, not a separately measured physical quantity. All assumptions are visible in code and results are reproducible for a fixed random seed.

### Injected scenarios

- **Consumption spike:** active power and corresponding current rise sharply, representing a possible real load event.
- **Meter drift:** the reported active-power value acquires a gradual offset.
- **Constant bias:** the reported active-power value receives a persistent offset.
- **False-data injection:** reported active power is altered without a matching change in companion measurements.
- **Replay-like readings:** a prior sequence is repeated in a later window.
- **Frozen meter:** multiple reported channels remain constant through an event window.
- **Missing data:** active-power readings are unavailable.
- **Energy–power mismatch:** cumulative energy is altered inconsistently with the reported power increment.

These scenarios are deliberately synthetic and are not exhaustive. Their labels are experimental ground truth for this simulator only; they do not establish real-world causes.

## 4. Detection and trust workflow

1. **Smart-meter simulator:** generates baseline household measurements and event-labelled test data.
2. **Feature engineering:** computes active-power consistency, cumulative-energy increments, temporal changes, missingness, and repeated-reading indicators per meter.
3. **Anomaly detector:** fits Isolation Forest on normal-only training data; transparent rules separately flag missing readings, implausible illustrative ranges, power/current/voltage inconsistency, energy–power inconsistency, abrupt demand changes, and repeated readings.
4. **Trust decision:** returns `TRUSTED`, `SUSPICIOUS`, or `UNCERTAIN` based on current evidence. `COMPROMISED` is reserved for future governance requiring stronger evidence and is not automatically assigned by the baseline.
5. **Human review:** suspicious data-quality cases are retained for inspection; unusual demand changes are compared with context and recent household baselines. The prototype issues no real control command and makes no automatic accusation against a household.
6. **Audit and collective learning:** a future review record will include event reference, timestamp, detector/model version, evidence, verdict, recommended action, reviewer decision, and override reason. Shared messages will contain compact, versioned event summaries rather than raw household time series by default.

### Confidence and explainability

The prototype returns rule evidence and a relative anomaly score. Its current `confidence` field is a **heuristic indicator, not a calibrated probability**. Plain-language explanation quality, confidence calibration, and reviewer usefulness remain evaluation tasks; no calibration claim is made in Phase 1.

## 5. Collective intelligence and privacy

The neighborhood can be represented as a set of meter-monitoring nodes and feeder-level aggregation nodes. For a later prototype, nodes may share a versioned event summary containing a coarse event category, abstracted feature ranges, timestamp bucket, detector version, validation status, and provenance. Household-level raw time series should remain local by default.

Receiving nodes must validate the message schema, version, provenance, and consistency before incorporating it into shared insights. This design reduces unnecessary data exchange but does not, by itself, guarantee anonymity or formal privacy. Risks include re-identification from fine-grained patterns and poisoning of shared summaries; these require explicit tests and safeguards before deployment.

## 6. Evaluation plan

The first experiment will train on normal-only synthetic rows and score a separately seeded synthetic dataset. It will report precision, recall, F1, false-positive rate on normal rows, per-scenario outcomes, and processing latency. A later evaluation should hold out complete scenarios or time windows, compare with simple statistical baselines, and test sensitivity to household profiles and random seeds.

A row-level metric on data generated by this same simulator measures only internal prototype behavior. It is not evidence of performance on real smart meters, real households, or a real distribution network. Results must be labelled accordingly.

## 7. Implementation plan

- **Phase 1:** document scope and assumptions; generate synthetic household telemetry; implement a reproducible baseline detector; include tests and sample outputs; submit the proposal and repository.
- **Phase 2:** add scenario-held-out experiments and per-scenario metrics; implement neighborhood aggregate alerts; add a human review and append-only audit workflow; validate versioned event-summary exchange; improve confidence estimation and explanations; prepare a reproducible demo.

## 8. Business and deployment considerations

Potential users include distribution-system stakeholders, smart-metering service providers, housing or campus energy managers, and operators of local energy communities. Potential value hypotheses include improved visibility into meter-data quality, earlier awareness of unusual demand, and more traceable alert review. These benefits have not yet been measured.

A cost model should separate software development, meter/interface integration, hosting or edge infrastructure, storage, cybersecurity, training, monitoring, model maintenance, and support. TND estimates should only be added after documenting deployment assumptions and obtaining local quotations.

## 9. Risks and limitations

- Synthetic household profiles and event patterns may not reflect real consumption diversity.
- The derived feeder aggregate is not independent ground truth.
- Unusual consumption is not proof of theft, tampering, or malicious intent.
- Illustrative thresholds require validation against the chosen meter specifications and local operating conditions.
- The current anomaly score/confidence indicator is not probability-calibrated.
- Shared summaries can leak information or be poisoned without governance and validation.
- No real-grid connection or control action is implemented.

## 10. Phase 1 checklist

- [x] Chosen scope explicitly defined as a smart-metered neighborhood.
- [x] Synthetic meter data schema and anomaly scenarios documented.
- [x] Initial detector and tests adapted to meter-level records.
- [x] Limitations and safe human-review posture documented.
- [ ] Run and review the revised prototype in the team's target environment.
- [ ] Add scenario-held-out and per-scenario evaluation before making performance claims.
- [ ] Confirm team details and any eligibility requirements.
- [ ] Verify final deliverables against the official submission instructions.
