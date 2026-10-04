"""Route plotting utilities for HCMC Traffic A* - using realtime traffic infrastructure."""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd

from src.graph.loader import load_graph
from src.routing.astar import AStar
from src.routing.models import RouteResult
from src.traffic.service import TrafficService
from src.traffic.models import TrafficSnapshot
from src.traffic.snapshot import load_snapshot_csv


# Data file paths
POI_FILE = "data/processed/poi_final.csv"
EDGES_ENRICHED_FILE = "data/processed/edges_enriched.csv"
SNAPSHOTS_DIR = "data/traffic/snapshots"


# HCMC timezone (UTC+7)
HCMC_TZ = timezone(timedelta(hours=7))


def get_current_hcmc_time():
    """Get current time in HCMC timezone."""
    return datetime.now(HCMC_TZ)


def create_fallback_snapshot(graph, timestamp=None):
    """
    Create a fallback traffic snapshot using maxspeed from edges or default speed.
    This allows routing without real-time traffic data.
    """
    if timestamp is None:
        timestamp = get_current_hcmc_time()

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
        timestamp=timestamp.isoformat(),
        edge_speed=edge_speed,
        provenance=provenance,
    )


def load_traffic_snapshot(graph, timestamp=None):
    """
    Load traffic snapshot using the new TrafficService (LIVE > REPLAY > FALLBACK).
    """
    if timestamp is None:
        timestamp = get_current_hcmc_time()

    try:
        # Use the new TrafficService with LIVE > REPLAY > FALLBACK priority
        traffic_service = TrafficService(edges_path=EDGES_ENRICHED_FILE)
        snapshot = traffic_service.get_snapshot(timestamp)
        print(f"Traffic snapshot loaded: mode={snapshot.mode}, edges={len(snapshot.edge_speed)}")
        return snapshot
    except Exception as e:
        print(f"Warning: TrafficService failed, using local fallback: {e}")
        return create_fallback_snapshot(graph, timestamp)


def find_path_between_pois(start_poi_id, end_poi_id, graph=None, snapshot=None, timestamp=None):
    """
    Find the shortest path between two POIs using the existing A* implementation
    with realtime traffic data.
    Returns: dict with path info or None if failed.
    """
    # Load graph if not provided
    if graph is None:
        graph = load_graph()

    # Use current HCMC time if not provided
    if timestamp is None:
        timestamp = get_current_hcmc_time()

    # Load snapshot if not provided
    if snapshot is None:
        snapshot = load_traffic_snapshot(graph, timestamp)

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


def generate_route_geojson(path_result, graph=None, snapshot=None):
    """Convert path result to GeoJSON LineString with per-edge traffic coloring."""
    if not path_result or "path_coordinates" not in path_result:
        return None

    coords = path_result["path_coordinates"]
    path_edges = path_result.get("path_edges", [])

    # If we have graph and snapshot, color each edge segment by traffic condition
    if graph and snapshot and path_edges:
        features = []

        for i, edge_key in enumerate(path_edges):
            if i + 1 >= len(coords):
                break

            edge = graph.edge_index.get(edge_key)
            if not edge:
                continue

            # Get current speed and free-flow speed
            current_speed = snapshot.edge_speed.get(edge_key, 40.0)
            free_flow_speed_raw = edge["meta"].get("free_flow_speed_kph", 40.0)
            try:
                free_flow_speed = float(free_flow_speed_raw)
            except (ValueError, TypeError):
                free_flow_speed = 40.0

            # Determine if in traffic jam: speed < 50% of free flow OR speed < 20 km/h
            speed_ratio = current_speed / free_flow_speed if free_flow_speed > 0 else 1.0
            is_jammed = speed_ratio < 0.5 or current_speed < 20.0

            # Color: red for jammed, blue for normal
            color = "#e34948" if is_jammed else "#2a78d6"

            # Create segment coordinates (from node i to i+1)
            segment_coords = [coords[i], coords[i + 1]]

            features.append({
                "type": "Feature",
                "properties": {
                    "type": "route_segment",
                    "edge_key": edge_key,
                    "segment_index": i,
                    "current_speed_kph": round(current_speed, 1),
                    "free_flow_speed_kph": round(free_flow_speed, 1),
                    "speed_ratio": round(speed_ratio, 2),
                    "is_jammed": is_jammed,
                    "color": color,
                    "weight": 4
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": segment_coords
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    # Fallback: single line with uniform color
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


def generate_route_geojson_with_start_end(path_result, graph=None, snapshot=None):
    """Generate complete route GeoJSON including start/end markers and segmented route line with traffic coloring."""
    if not path_result or "path_coordinates" not in path_result:
        return None

    features = []

    # Get route segments with traffic coloring
    route_geojson = generate_route_geojson(path_result, graph, snapshot)

    if route_geojson and route_geojson["type"] == "FeatureCollection":
        # Add each route segment
        for segment in route_geojson["features"]:
            features.append(segment)
    elif route_geojson:
        # Fallback: single line
        features.append(route_geojson)

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