"""Run A*, Dijkstra and heuristic checks on a fixed supplied snapshot."""

import argparse
import json

import math
import random

from src.graph.loader import load_graph, PROJECT_ROOT
from src.routing.astar import AStar
from src.routing.dijkstra_baseline import exact_costs_to_goal
from src.traffic.fallback_provider import FallbackTrafficProvider
from src.traffic.replay_provider import ReplayTrafficProvider
from src.traffic.models import TrafficSnapshot


def resolve_node(graph, location):
    if location in graph.poi_to_node:
        return graph.poi_to_node[location]
    node = int(location)
    if node not in graph.nodes:
        raise ValueError(f"Unknown node or POI: {location}")
    return node


def prepare_snapshot(graph, timestamp, mode, snapshot_path):
    """Local test harness; traffic providers remain owned by the traffic module."""
    fallback = FallbackTrafficProvider(str(PROJECT_ROOT / "data/processed/edges_enriched.csv"))
    if mode == "FALLBACK":
        return fallback.get_snapshot(timestamp)
    if not snapshot_path:
        raise ValueError("REPLAY requires --snapshot pointing to a normalized CSV")
    selected = ReplayTrafficProvider(snapshot_path).get_snapshot(timestamp)
    if selected.edge_speed.keys() - graph.edge_index.keys():
        raise ValueError("Snapshot references edges outside the road graph")
    missing = graph.edge_index.keys() - selected.edge_speed.keys()
    if not missing:
        return selected
    baseline = fallback.get_snapshot(selected.timestamp)
    speeds, provenance = dict(selected.edge_speed), dict(selected.provenance)
    for key in missing:
        speeds[key] = baseline.speed(*key)
        provenance[key] = "fallback"
    return TrafficSnapshot(selected.timestamp, speeds, provenance, mode="REPLAY")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", help="POI or road node ID, e.g. POI0001")
    parser.add_argument("--goal", help="POI or road node ID, e.g. POI0002")
    parser.add_argument("--timestamp", help="ISO departure, e.g. 2026-10-02T17:30:00+07:00")
    parser.add_argument("--mode", choices=["REPLAY", "FALLBACK"], default="FALLBACK")
    parser.add_argument("--snapshot", help="Recorded normalized CSV for REPLAY")
    parser.add_argument("--list-pois", action="store_true")
    parser.add_argument("--benchmark-pairs", type=int, default=0, help="Check this many deterministic random POI pairs")
    parser.add_argument("--verify", action="store_true", help="Check heuristic and compare with reverse Dijkstra")
    args = parser.parse_args()
    try:
        graph = load_graph()
        if args.list_pois:
            for poi_id, poi in graph.pois.items():
                print(f"{poi_id}: {poi['name']} ({poi['category']})")
            return
        if not args.timestamp:
            parser.error("Supply --timestamp")
        snapshot = prepare_snapshot(graph, args.timestamp, args.mode, args.snapshot)
        if args.benchmark_pairs:
            from src.evaluation.benchmark import compare_routes
            if args.benchmark_pairs < 1:
                raise ValueError("--benchmark-pairs must be positive")
            nodes = list(graph.poi_to_node.values())
            rng = random.Random(3061)
            cases = [tuple(rng.sample(nodes, 2)) for _ in range(args.benchmark_pairs)]
            record = compare_routes(graph, snapshot, cases)
        else:
            if not args.start or not args.goal:
                parser.error("Supply --start and --goal")
            start, goal = resolve_node(graph, args.start), resolve_node(graph, args.goal)
            result = AStar(graph).search(start, goal, snapshot)
            record = result.to_dict()
            record["requested_timestamp"] = args.timestamp
            if args.verify:
                from src.evaluation.admissibility import check_admissibility
                from src.evaluation.consistency import check_consistency
                admissibility = check_admissibility(graph, snapshot, goal)
                consistency = check_consistency(graph, snapshot, goal)
                exact = exact_costs_to_goal(graph, snapshot, goal)[start]
                optimal = math.isclose(result.total_time_s, exact, rel_tol=1e-9, abs_tol=1e-6) if result.found else math.isinf(exact)
                record["verification"] = {"admissibility": admissibility, "consistency": consistency, "optimal": optimal}
        print(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
