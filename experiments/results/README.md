# Experimental results

The `evaluation/` directory contains:

- `metadata.json`: dataset checks, input hashes, environment, POI pairs and timing method.
- `routing-results.json`: heuristic verification and A*/Dijkstra measurements for each pair and snapshot.
- `freeflow-comparison.json`: free-flow versus recorded-traffic costs and route-change indicators.
- `test-results.json`: results of the automated test suite.

Complete node and edge sequences are omitted from stored results to avoid duplication.
The evaluator retains routes in memory when comparing them; removing them from the
output does not change route costs, optimality checks or route-change indicators.

## Reproduce the experiments

From the repository root, install the test dependencies and run:

```powershell
python experiments/run_tests.py
python experiments/evaluate_routing.py
```

The routing evaluation requires the processed road/POI tables and at least one
complete recorded snapshot in `data/traffic/snapshots/`. It selects the latest
snapshot by filename, uses random seed 3061 and runs three repetitions per
algorithm for each of 20 POI pairs. Runtime depends on the machine and workload;
selecting a different recorded snapshot can change traffic-related results.

Both scripts write to `experiments/results/evaluation/` by default. Set
`ROUTING_EVALUATION_OUTPUT` to another directory to preserve the included results.
Test results cover `tests/`; they do not certify the standalone `main.py` CLI
or fresh LIVE traffic acquisition. The application entry point is `python -m app.app`.
