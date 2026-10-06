"""Check h(u) <= c(u,v) + h(v) for every directed parallel edge."""

import math

from src.routing.heuristic import travel_time_heuristic
from src.traffic.cost import travel_time_seconds


def check_consistency(graph, snapshot, goal,
                      heuristic=travel_time_heuristic, epsilon=1e-7):
    if not math.isfinite(epsilon) or epsilon < 0:
        raise ValueError("epsilon must be finite and nonnegative")
    target = graph.nodes[goal]
    values = {n: heuristic(node, target, snapshot.v_bound)
              for n, node in graph.nodes.items()}
    violations = []
    invalid_nodes = [n for n, h in values.items() if not math.isfinite(h) or h < 0]
    checked = 0
    for source, edges in graph.edges.items():
        for edge in edges:
            target_id = edge["target"]
            meta = edge["meta"]
            key = (source, target_id, meta.get("edge_key", 0))
            cost = travel_time_seconds(meta.get("distance_m", edge["weight"]),
                                       snapshot.speed(*key))
            checked += 1
            if values[source] > cost + values[target_id] + epsilon:
                violations.append({"edge": key,
                                   "h_source_s": values[source] if math.isfinite(values[source]) else None,
                                   "edge_cost_s": cost,
                                   "h_target_s": values[target_id] if math.isfinite(values[target_id]) else None})
    goal_zero = math.isfinite(values[goal]) and abs(values[goal]) <= epsilon
    return {"passed": not violations and not invalid_nodes and goal_zero,
            "checked_edges": checked, "goal": goal,
            "snapshot_timestamp": snapshot.timestamp, "epsilon_s": epsilon,
            "goal_heuristic_zero": goal_zero, "invalid_nodes": invalid_nodes,
            "violations": violations}


def is_consistent(heuristic, graph, start, goal, snapshot, epsilon=1e-7):
    """Boolean global check; start retained for the previous call shape."""
    return check_consistency(graph, snapshot, goal, heuristic, epsilon)["passed"]
