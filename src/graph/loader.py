"""Load the group's CSV contract, preserving every directed (u, v, k)."""

import csv
import math
from pathlib import Path

from src.graph.graph import Graph
from src.graph.node import Node

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_rows(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        return list(reader)


def finite_number(value, field):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def load_graph(nodes_path=None, edges_path=None, pois_path=None):
    data = PROJECT_ROOT / "data/processed"
    nodes_path = nodes_path or data / "nodes.csv"
    edges_path = edges_path or data / "edges_enriched.csv"
    pois_path = pois_path or data / "poi_final.csv"
    graph = Graph()
    for row in read_rows(nodes_path, ("node_id", "latitude", "longitude")):
        node_id = int(row["node_id"])
        lat = finite_number(row["latitude"], "latitude")
        lon = finite_number(row["longitude"], "longitude")
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"Invalid coordinates for {node_id}")
        if node_id in graph.nodes:
            raise ValueError(f"Duplicate node: {node_id}")
        graph.add_node(node_id, Node(node_id, lat=lat, lon=lon))
    for row in read_rows(edges_path, ("source", "target", "edge_key", "distance_m")):
        u, v, k = int(row["source"]), int(row["target"]), int(row["edge_key"])
        if u not in graph.nodes or v not in graph.nodes:
            raise ValueError(f"Edge {(u, v, k)} references an unknown node")
        length = finite_number(row["distance_m"], "distance_m")
        if length < 0:
            raise ValueError(f"Negative distance for {(u, v, k)}")
        meta = {name: value for name, value in row.items()
                if name not in {"source", "target", "edge_key", "distance_m"}}
        graph.add_edge(u, v, weight=length, edge_key=k, distance_m=length, **meta)
    for row in read_rows(pois_path, ("poi_id", "name", "latitude", "longitude", "nearest_node")):
        row["latitude"] = finite_number(row["latitude"], "latitude")
        row["longitude"] = finite_number(row["longitude"], "longitude")
        row["nearest_node"] = int(row["nearest_node"])
        if "distance_to_node_m" in row:
            row["distance_to_node_m"] = finite_number(row["distance_to_node_m"], "distance_to_node_m")
        graph.add_poi(row["poi_id"], row, row["nearest_node"])
    return graph
