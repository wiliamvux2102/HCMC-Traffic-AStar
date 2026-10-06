"""Dijkstra baseline and independent reverse-graph ground truth."""

import heapq
import math
from itertools import count

from src.routing.astar import AStar
from src.routing.cost import edge_cost


class Dijkstra(AStar):
    def search(self, start, goal, snapshot):
        return self._search(start, goal, snapshot, use_heuristic=False)


def exact_costs_to_goal(graph, snapshot, goal):
    if goal not in graph.nodes:
        raise ValueError("Unknown goal")
    missing = graph.edge_index.keys() - snapshot.edge_speed.keys()
    if missing:
        raise ValueError("Incomplete snapshot")
    reverse = {}
    for key in graph.edge_index:
        u, v, _ = key
        reverse.setdefault(v, []).append((u, edge_cost(graph, snapshot, key)))
    best = {node: math.inf for node in graph.nodes}
    best[goal] = 0.0
    serial = count()
    queue = [(0.0, next(serial), goal)]
    while queue:
        cost, _, node = heapq.heappop(queue)
        if cost != best[node]:
            continue
        for previous, step_cost in reverse.get(node, []):
            tentative = cost + step_cost
            if tentative < best[previous]:
                best[previous] = tentative
                heapq.heappush(queue, (tentative, next(serial), previous))
    return best
