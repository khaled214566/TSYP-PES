# Data notes

All data in this project is synthetic and generated locally by `src/gridsentinel/simulator.py`.

- `normal_training.csv`: generated household smart-meter records with no injected event labels.
- `scored_demo.csv`: synthetic test records and detector outputs.
- `summary.csv`: scenario/verdict row counts.

The generator records household meter, building and feeder identifiers; one-minute timestamp; voltage, current, active power, power factor, frequency and cumulative energy; event type and affected channel; and a feeder aggregate derived from the simulated household values. These files are not actual utility or household data.
