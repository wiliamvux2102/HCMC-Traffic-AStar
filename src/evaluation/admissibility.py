"""Compare heuristic estimates to reverse-Dijkstra ground truth."""

import math

from src.routing.dijkstra_baseline import exact_costs_to_goal
from src.routing.heuristic import travel_time_heuristic


def check_admissibility(graph, snapshot, goal, nodes=None,
                        heuristic=travel_time_heuristic, epsilon=1e-7):
    """Check all nodes or a sample; costs and epsilon are seconds.

    The heuristic receives (Node, goal Node, snapshot.v_bound).
    Unreachable nodes have infinite exact cost.
    """
    if not math.isfinite(epsilon) or epsilon < 0:
        raise ValueError("epsilon must be finite and nonnegative")
    exact = exact_costs_to_goal(graph, snapshot, goal)
    target = graph.nodes[goal]
    violations = []
    checked = 0
    for node_id in graph.nodes if nodes is None else nodes:
        estimate = heuristic(graph.nodes[node_id], target, snapshot.v_bound)
        optimal = exact[node_id]
        checked += 1
        if not math.isfinite(estimate) or estimate < 0 or estimate > optimal + epsilon:
            violations.append({"node": node_id,
                               "heuristic_s": estimate if math.isfinite(estimate) else None,
                               "optimal_s": optimal if math.isfinite(optimal) else None})
    goal_estimate = heuristic(target, target, snapshot.v_bound)
    goal_zero = math.isfinite(goal_estimate) and abs(goal_estimate) <= epsilon
    return {"passed": not violations and goal_zero, "checked_nodes": checked,
            "goal_heuristic_zero": goal_zero,
            "goal": goal, "snapshot_timestamp": snapshot.timestamp,
            "epsilon_s": epsilon, "violations": violations}


def is_admissible(heuristic, graph, start, goal, snapshot, epsilon=1e-7):
    """Boolean check at start; traffic snapshot is explicitly required."""
    return check_admissibility(graph, snapshot, goal, [start], heuristic, epsilon)["passed"]
