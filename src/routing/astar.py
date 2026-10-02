"""A* for a fixed, complete TrafficSnapshot (technical document section 9)."""

import heapq
import math
from itertools import count
from time import perf_counter

from src.routing.cost import edge_cost
from src.routing.heuristic import haversine_distance, travel_time_heuristic
from src.routing.models import RouteResult


class AStar:
    def __init__(self, graph):
        self.graph = graph
        # Validate the road-length assumption once, before using the proof.
        for key, edge in graph.edge_index.items():
            u, v, _ = key
            if u not in graph.nodes or v not in graph.nodes:
                raise ValueError(f"Unknown endpoint on edge {key}")
            a, b = graph.nodes[u], graph.nodes[v]
            straight = haversine_distance(a.lat, a.lon, b.lat, b.lon)
            length = float(edge["meta"]["distance_m"])
            if not math.isfinite(length) or length < 0:
                raise ValueError(f"Invalid length on edge {key}")
            if length + 1e-6 < straight:
                raise ValueError(f"Edge {key}: road length is shorter than Haversine distance")

    def search(self, start, goal, snapshot):
        return self._search(start, goal, snapshot, use_heuristic=True)

    def _search(self, start, goal, snapshot, use_heuristic):
        started = perf_counter()
        if start not in self.graph.nodes or goal not in self.graph.nodes:
            raise ValueError("Start and goal must be known road nodes")
        missing = self.graph.edge_index.keys() - snapshot.edge_speed.keys()
        if missing:
            raise ValueError(f"Incomplete snapshot: {len(missing)} edges have no speed; fill missing speeds first")
        v_bound = snapshot.v_bound
        serial = count()
        estimates = {}

        def h(node_id):
            if not use_heuristic:
                return 0.0
            if node_id not in estimates:
                estimates[node_id] = travel_time_heuristic(
                    self.graph.nodes[node_id], self.graph.nodes[goal], v_bound)
            return estimates[node_id]

        frontier = [(h(start), next(serial), start, 0.0)]
        best = {start: 0.0}
        parents = {}
        expanded = 0
        while frontier:
            _, _, current, queued_g = heapq.heappop(frontier)
            if queued_g != best[current]:
                continue
            if current == goal:
                path_nodes, path_edges = [goal], []
                while current in parents:
                    key = parents[current]
                    path_edges.append(key)
                    current = key[0]
                    path_nodes.append(current)
                path_edges.reverse()
                path_nodes.reverse()
                provenance = {}
                for key in path_edges:
                    source = snapshot.provenance[key]
                    provenance[source] = provenance.get(source, 0) + 1
                return RouteResult(
                    path_edges=path_edges, total_time_s=queued_g,
                    total_distance_m=sum(self.graph.edge_index[key]["meta"]["distance_m"] for key in path_edges),
                    expanded_nodes=expanded, runtime_ms=(perf_counter() - started) * 1000,
                    snapshot_timestamp=snapshot.timestamp, traffic_mode=snapshot.mode,
                    path_nodes=path_nodes, provenance_counts=provenance)
            expanded += 1
            for edge in self.graph.edges.get(current, []):
                neighbor = edge["target"]
                key = (current, neighbor, edge["meta"]["edge_key"])
                tentative = queued_g + edge_cost(self.graph, snapshot, key)
                if tentative < best.get(neighbor, math.inf):
                    best[neighbor] = tentative
                    parents[neighbor] = key
                    heapq.heappush(frontier, (tentative + h(neighbor), next(serial), neighbor, tentative))
        # No-path uses found=False, not a non-standard JSON Infinity value.
        return RouteResult([], 0.0, 0.0, expanded, (perf_counter() - started) * 1000,
                           snapshot.timestamp, snapshot.mode, found=False)
