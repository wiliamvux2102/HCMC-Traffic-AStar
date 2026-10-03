"""Route plotting utilities for HCMC Traffic A* - using existing routing infrastructure."""

import json
import os
from pathlib import Path
import pandas as pd

from src.graph.loader import load_graph
from src.routing.astar import AStar
from src.routing.models import RouteResult
from src.traffic.snapshot import snapshot_from_dataframe
from src.traffic.models import TrafficSnapshot


# Data file paths
POI_FILE = "data/processed/poi_final.csv"
TRAFFIC_FILE = "data/processed/traffic_snapshot.csv"  # If available


def create_fallback_snapshot(graph):
    """
    Create a fallback traffic snapshot using maxspeed from edges or default speed.
    This allows routing without real-time traffic data.
    """
    edge_speed = {}
    provenance = {}

    for key, edge in graph.edge_index.items():
        # Use maxspeed from edge meta if available, otherwise default to 40 km/h
        maxspeed = edge["meta"].get("maxspeed_raw")
        if maxspeed:
            try:
                speed = float(maxspeed)
            except (ValueError, TypeError):
                speed = 40.0
        else:
            # Default speed based on highway type
            highway = edge["meta"].get("highway", "residential")
            if highway in ["motorway", "trunk"]:
                speed = 80.0
            elif highway in ["primary", "secondary"]:
                speed = 60.0
            elif highway in ["tertiary"]:
                speed = 50.0
            else:
                speed = 40.0

        # Ensure reasonable bounds
        speed = max(10.0, min(120.0, speed))
        edge_speed[key] = speed
        provenance[key] = "fallback"

    return TrafficSnapshot(
        timestamp="2026-10-02T12:00:00+07:00",
        edge_speed=edge_speed,
        provenance=provenance,
        mode="FALLBACK"
    )


def load_traffic_snapshot(graph):
    """
    Try to load traffic snapshot from file, otherwise create fallback.
    """
    if os.path.exists(TRAFFIC_FILE):
        try:
            df = pd.read_csv(TRAFFIC_FILE)
            return snapshot_from_dataframe(df, "2026-10-02T12:00:00+07:00")
        except Exception as e:
            print(f"Warning: Could not load traffic snapshot: {e}")

    return create_fallback_snapshot(graph)


def find_path_between_pois(start_poi_id, end_poi_id, graph=None, snapshot=None):
    """
    Find the shortest path between two POIs using the existing A* implementation.
    Returns: dict with path info or None if failed.
    """
    # Load graph if not provided
    if graph is None:
        graph = load_graph()

    # Load snapshot if not provided
    if snapshot is None:
        snapshot = load_traffic_snapshot(graph)

    # Get POI nearest nodes
    if start_poi_id not in graph.poi_to_node:
        return {"error": f"Start POI {start_poi_id} not found in graph"}
    if end_poi_id not in graph.poi_to_node:
        return {"error": f"End POI {end_poi_id} not found in graph"}

    start_node = graph.poi_to_node[start_poi_id]
    end_node = graph.poi_to_node[end_poi_id]

    # Run A*
    astar = AStar(graph)
    result = astar.search(start_node, end_node, snapshot)

    if not result.found:
        return {"error": "No path found"}

    # Build detailed path info
    path_coords = []
    for node_id in result.path_nodes:
        node = graph.nodes[node_id]
        path_coords.append([node.lon, node.lat])  # GeoJSON is [lon, lat]

    # Get POI coordinates
    start_poi = graph.pois[start_poi_id]
    end_poi = graph.pois[end_poi_id]

    return {
        "start_poi": start_poi_id,
        "end_poi": end_poi_id,
        "start_node": start_node,
        "end_node": end_node,
        "path_nodes": result.path_nodes,
        "path_edges": result.path_edges,
        "path_coordinates": path_coords,
        "total_distance_m": result.total_distance_m,
        "total_distance_km": round(result.total_distance_m / 1000, 2),
        "total_time_s": round(result.total_time_s, 1),
        "total_time_min": round(result.total_time_s / 60, 1),
        "expanded_nodes": result.expanded_nodes,
        "runtime_ms": round(result.runtime_ms, 1),
        "start_coords": [start_poi["longitude"], start_poi["latitude"]],
        "end_coords": [end_poi["longitude"], end_poi["latitude"]],
        "traffic_mode": result.traffic_mode,
        "snapshot_timestamp": result.snapshot_timestamp,
        "provenance_counts": result.provenance_counts
    }


def generate_route_geojson(path_result):
    """Convert path result to GeoJSON LineString."""
    if not path_result or "path_coordinates" not in path_result:
        return None

    coords = path_result["path_coordinates"]

    return {
        "type": "Feature",
        "properties": {
            "start_poi": path_result.get("start_poi"),
            "end_poi": path_result.get("end_poi"),
            "distance_m": path_result.get("total_distance_m"),
            "distance_km": path_result.get("total_distance_km"),
            "time_s": path_result.get("total_time_s"),
            "time_min": path_result.get("total_time_min"),
            "color": "#2a78d6",
            "weight": 4
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coords
        }
    }


def generate_route_geojson_with_start_end(path_result):
    """Generate complete route GeoJSON including start/end markers and line."""
    if not path_result or "path_coordinates" not in path_result:
        return None

    features = []

    # Route line
    features.append({
        "type": "Feature",
        "properties": {
            "type": "route",
            "start_poi": path_result.get("start_poi"),
            "end_poi": path_result.get("end_poi"),
            "distance_m": path_result.get("total_distance_m"),
            "distance_km": path_result.get("total_distance_km"),
            "time_s": path_result.get("total_time_s"),
            "time_min": path_result.get("total_time_min"),
            "color": "#2a78d6",
            "weight": 4
        },
        "geometry": {
            "type": "LineString",
            "coordinates": path_result["path_coordinates"]
        }
    })

    # Start marker
    features.append({
        "type": "Feature",
        "properties": {
            "type": "start",
            "poi_id": path_result.get("start_poi"),
            "color": "#0ca30c"  # green - good/status
        },
        "geometry": {
            "type": "Point",
            "coordinates": path_result["start_coords"]
        }
    })

    # End marker
    features.append({
        "type": "Feature",
        "properties": {
            "type": "end",
            "poi_id": path_result.get("end_poi"),
            "color": "#d03b3b"  # red - critical/status
        },
        "geometry": {
            "type": "Point",
            "coordinates": path_result["end_coords"]
        }
    })

    return {
        "type": "FeatureCollection",
        "features": features
    }


def get_all_pois():
    """Get all POIs for dropdown selection."""
    graph = load_graph()
    return [
        {"poi_id": poi_id, "name": poi["name"], "category": poi.get("category", "unknown")}
        for poi_id, poi in graph.pois.items()
    ]


if __name__ == "__main__":
    # Test the functions
    print("Loading graph...")
    graph = load_graph()
    print(f"Graph loaded: {len(graph.nodes)} nodes, {len(graph.edge_index)} edges")
    print(f"POIs: {len(graph.pois)}")

    # Test POI pathfinding
    pois = get_all_pois()
    if len(pois) >= 2:
        start = pois[0]["poi_id"]
        end = pois[1]["poi_id"]
        print(f"\nFinding path from {start} to {end}...")
        result = find_path_between_pois(start, end, graph)
        print(json.dumps(result, indent=2))