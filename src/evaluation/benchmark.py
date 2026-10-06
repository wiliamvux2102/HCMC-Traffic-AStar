"""Compare routing algorithms on identical traffic snapshots."""

import math
from dataclasses import asdict

from src.routing.astar import AStar
from src.routing.dijkstra_baseline import Dijkstra


def compare_routes(graph, snapshot, cases, epsilon=1e-7):
    """Report cost agreement, expansions and runtime for (start, goal) pairs.

    Equal costs are required, not identical paths: optimal paths may tie.
    Runtime and expansion savings are measurements, not correctness assertions.
    """
    if not math.isfinite(epsilon) or epsilon < 0:
        raise ValueError("epsilon must be finite and nonnegative")
    astar, dijkstra = AStar(graph), Dijkstra(graph)
    rows = []
    for start, goal in cases:
        a = astar.search(start, goal, snapshot)
        d = dijkstra.search(start, goal, snapshot)
        matched = a.found == d.found and (
            not a.found or math.isclose(a.total_time_s, d.total_time_s,
                                       rel_tol=1e-9, abs_tol=epsilon))
        rows.append({"start": start, "goal": goal, "optimality_passed": matched,
                     "astar": asdict(a), "dijkstra": asdict(d),
                     "expanded_nodes_saved": d.expanded_nodes - a.expanded_nodes})
    return {"passed": all(row["optimality_passed"] for row in rows),
            "snapshot_timestamp": snapshot.timestamp, "epsilon_s": epsilon,
            "case_count": len(rows), "cases": rows}


def benchmark_search(search_fn, cases):
    """Run a sequence of search tasks and return a list of results."""
    results = []
    for case in cases:
        result = search_fn(*case)
        results.append({"case": case, "result": result})
    return results
