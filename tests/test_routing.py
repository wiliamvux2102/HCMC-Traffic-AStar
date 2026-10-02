"""Routing contracts from technical document sections 8, 9 and 11."""

import json
import math
import unittest

from src.graph.graph import Graph
from src.graph.node import Node
from src.traffic.models import TrafficSnapshot
from src.routing.astar import AStar
from src.routing.dijkstra_baseline import Dijkstra, exact_costs_to_goal
from src.routing.heuristic import haversine_distance, travel_time_heuristic
from src.evaluation.admissibility import check_admissibility
from src.evaluation.consistency import check_consistency
from src.evaluation.benchmark import compare_routes


class RoutingContracts(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        for n, lat, lon in [(1, 0, 0), (2, 0, .001), (3, 0, .002),
                             (4, .001, .001), (5, .01, .01)]:
            self.graph.add_node(n, Node(n, lat, lon))
        self.speeds = {}
        for u, v, k, length, speed in [(1, 2, 0, 200, 10), (1, 2, 1, 300, 60),
                                        (2, 3, 0, 200, 60), (1, 4, 0, 300, 60),
                                        (4, 3, 0, 300, 60)]:
            self.graph.add_edge(u, v, weight=length, edge_key=k, distance_m=length)
            self.speeds[(u, v, k)] = speed
        self.snapshot = self.make_snapshot(self.speeds)

    @staticmethod
    def make_snapshot(speeds):
        return TrafficSnapshot("2026-10-02T17:30:00+07:00", speeds,
                               {key: "replay" for key in speeds})

    def test_parallel_edge_key_and_cost_ground_truth(self):
        a = AStar(self.graph).search(1, 3, self.snapshot)
        d = Dijkstra(self.graph).search(1, 3, self.snapshot)
        self.assertTrue(a.found)
        self.assertEqual(a.path_edges, [(1, 2, 1), (2, 3, 0)])
        self.assertEqual(a.path_nodes, [1, 2, 3])
        self.assertAlmostEqual(a.total_time_s, 30)
        self.assertAlmostEqual(a.total_distance_m, 500)
        self.assertAlmostEqual(a.total_time_s, d.total_time_s)
        self.assertAlmostEqual(a.total_time_s, exact_costs_to_goal(self.graph, self.snapshot, 3)[1])
        self.assertEqual(a.traffic_mode, "REPLAY")
        self.assertEqual(a.snapshot_timestamp, self.snapshot.timestamp)

    def test_snapshot_changes_best_route(self):
        changed = dict(self.speeds)
        changed[(1, 2, 1)] = 1
        snapshot = self.make_snapshot(changed)
        route = AStar(self.graph).search(1, 3, snapshot)
        self.assertEqual(route.path_edges, [(1, 4, 0), (4, 3, 0)])
        self.assertAlmostEqual(route.total_time_s, 36)
        self.assertEqual(self.snapshot.speed(1, 2, 1), 60)
        changed[(1, 4, 0)] = 1
        self.assertEqual(snapshot.speed(1, 4, 0), 60)

    def test_invalid_speeds_rejected(self):
        for speed in [0, -1, math.nan, math.inf, -math.inf]:
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                self.make_snapshot({(1, 2, 0): speed})

    def test_missing_speed_rejected(self):
        incomplete = dict(self.speeds)
        del incomplete[(1, 2, 0)]
        with self.assertRaises(ValueError):
            AStar(self.graph).search(1, 3, self.make_snapshot(incomplete))

    def test_unreachable_and_identical_endpoints(self):
        solver = AStar(self.graph)
        missing = solver.search(3, 1, self.snapshot)
        self.assertFalse(missing.found)
        self.assertEqual(missing.path_edges, [])
        self.assertTrue(math.isinf(exact_costs_to_goal(self.graph, self.snapshot, 3)[5]))
        same = solver.search(1, 1, self.snapshot)
        self.assertTrue(same.found)
        self.assertEqual(same.path_nodes, [1])
        self.assertEqual(same.path_edges, [])
        self.assertEqual(same.total_time_s, 0)

    def test_haversine_units_and_valid_heuristic(self):
        self.assertAlmostEqual(haversine_distance(0, 0, 0, .001), 111.1949266, places=5)
        self.assertEqual(travel_time_heuristic(self.graph.nodes[3], self.graph.nodes[3], 60), 0)
        self.assertTrue(check_admissibility(self.graph, self.snapshot, 3)["passed"])
        report = check_consistency(self.graph, self.snapshot, 3)
        self.assertTrue(report["passed"])
        self.assertEqual(report["checked_edges"], 5)

    def test_admissible_but_inconsistent_is_detected(self):
        def heuristic(node, goal, bound):
            return 20.0 if node.id == 1 else 0.0
        self.assertTrue(check_admissibility(self.graph, self.snapshot, 3,
                                            heuristic=heuristic)["passed"])
        report = check_consistency(self.graph, self.snapshot, 3, heuristic=heuristic)
        self.assertFalse(report["passed"])
        self.assertIn((1, 2, 1), [v["edge"] for v in report["violations"]])

    def test_overestimate_and_nonzero_goal_fail(self):
        def overestimate(node, goal, bound):
            return 100 if node.id == 1 else 0
        self.assertFalse(check_admissibility(self.graph, self.snapshot, 3,
                                             heuristic=overestimate)["passed"])
        def nonzero(node, goal, bound):
            return 1.0
        self.assertFalse(check_admissibility(self.graph, self.snapshot, 3,
                                             nodes=[1], heuristic=nonzero)["passed"])
        self.assertFalse(check_consistency(self.graph, self.snapshot, 3,
                                           heuristic=nonzero)["passed"])

    def test_graph_assumption_and_query_bounds(self):
        graph = Graph()
        graph.add_node(1, Node(1, 0, 0))
        graph.add_node(2, Node(2, 0, .001))
        graph.add_edge(1, 2, weight=1, edge_key=0, distance_m=1)
        with self.assertRaises(ValueError):
            AStar(graph)
        with self.assertRaises(ValueError):
            AStar(self.graph).search(999, 3, self.snapshot)
        with self.assertRaises(ValueError):
            haversine_distance(91, 0, 0, 0)

    def test_benchmark_handles_unreachable_and_json(self):
        report = compare_routes(self.graph, self.snapshot, [(1, 3), (3, 1), (1, 1)])
        self.assertTrue(report["passed"])
        self.assertEqual(report["case_count"], 3)
        json.dumps(report, allow_nan=False)
        json.dumps(check_admissibility(self.graph, self.snapshot, 3), allow_nan=False)
        json.dumps(check_consistency(self.graph, self.snapshot, 3), allow_nan=False)


if __name__ == "__main__":
    unittest.main()
