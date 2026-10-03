"""Route plotting utilities for HCMC Traffic A*."""

import json
import os
import heapq
from pathlib import Path
import pandas as pd
import math


# Data file paths
NODES_FILE = "data/processed/nodes.csv"
EDGES_FILE = "data/processed/edges.csv"
POI_FILE = "data/processed/poi_final.csv"


def load_graph():
    """
    Load the road network as an adjacency list for A* pathfinding.
    Returns: (adjacency_list, node_coords)
    """
    nodes_df = pd.read_csv(NODES_FILE)
    edges_df = pd.read_csv(EDGES_FILE)

    # Build node coordinate lookup
    node_coords = {}
    for _, row in nodes_df.iterrows():
        node_coords[row["node_id"]] = (row["latitude"], row["longitude"])

    # Build adjacency list
    adj = {}
    for _, edge in edges_df.iterrows():
        source = edge["source"]
        target = edge["target"]
        distance = edge["distance_m"]
        oneway = edge.get("oneway", False)

        if source not in adj:
            adj[source] = []
        adj[source].append((target, distance))

        # If not oneway, add reverse edge
        if not oneway:
            if target not in adj:
                adj[target] = []
            adj[target].append((source, distance))

    return adj, node_coords


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate Haversine distance between two points in meters."""
    R = 6371000  # Earth radius in meters

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlat = lat2 - lat1
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def heuristic(node_id, goal_id, node_coords):
    """Heuristic function for A* (straight-line distance)."""
    if node_id in node_coords and goal_id in node_coords:
        lat1, lon1 = node_coords[node_id]
        lat2, lon2 = node_coords[goal_id]
        return haversine_distance(lat1, lon1, lat2, lon2)
    return 0


def a_star(start_node, goal_node, adj, node_coords, max_iterations=100000):
    """
    A* pathfinding algorithm.
    Returns: (path, total_distance) or (None, None) if no path found.
    """
    if start_node not in adj or goal_node not in adj:
        return None, None

    # Priority queue: (f_score, g_score, node_id, path)
    open_set = []
    heapq.heappush(open_set, (0, 0, start_node, [start_node]))

    g_scores = {start_node: 0}
    iterations = 0

    while open_set and iterations < max_iterations:
        iterations += 1
        f_score, g_score, current, path = heapq.heappop(open_set)

        if current == goal_node:
            return path, g_score

        # Skip if we've found a better path to this node
        if g_score > g_scores.get(current, float('inf')):
            continue

        for neighbor, distance in adj.get(current, []):
            tentative_g = g_score + distance

            if tentative_g < g_scores.get(neighbor, float('inf')):
                g_scores[neighbor] = tentative_g
                h = heuristic(neighbor, goal_node, node_coords)
                f = tentative_g + h
                heapq.heappush(open_set, (f, tentative_g, neighbor, path + [neighbor]))

    return None, None


def find_path_between_pois(start_poi_id, end_poi_id):
    """
    Find the shortest path between two POIs.
    Returns: dict with path info or None if failed.
    """
    # Load POIs to get their nearest nodes
    pois_df = pd.read_csv(POI_FILE)

    start_poi = pois_df[pois_df["poi_id"] == start_poi_id]
    end_poi = pois_df[pois_df["poi_id"] == end_poi_id]

    if start_poi.empty or end_poi.empty:
        return {"error": "POI not found"}

    start_node = int(start_poi.iloc[0]["nearest_node"])
    end_node = int(end_poi.iloc[0]["nearest_node"])

    # Load graph
    adj, node_coords = load_graph()

    # Run A*
    path, distance = a_star(start_node, end_node, adj, node_coords)

    if path is None:
        return {"error": "No path found"}

    # Build detailed path info
    path_coords = []
    for node_id in path:
        if node_id in node_coords:
            lat, lon = node_coords[node_id]
            path_coords.append([lon, lat])  # GeoJSON is [lon, lat]

    # Get POI coordinates
    start_lat = start_poi.iloc[0]["latitude"]
    start_lon = start_poi.iloc[0]["longitude"]
    end_lat = end_poi.iloc[0]["latitude"]
    end_lon = end_poi.iloc[0]["longitude"]

    return {
        "start_poi": start_poi_id,
        "end_poi": end_poi_id,
        "start_node": start_node,
        "end_node": end_node,
        "path_nodes": path,
        "path_coordinates": path_coords,
        "total_distance_m": distance,
        "total_distance_km": round(distance / 1000, 2),
        "start_coords": [start_lon, start_lat],
        "end_coords": [end_lon, end_lat]
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
    pois_df = pd.read_csv(POI_FILE)
    return pois_df[["poi_id", "name", "category"]].to_dict("records")


if __name__ == "__main__":
    # Test the functions
    print("Loading graph...")
    adj, node_coords = load_graph()
    print(f"Graph loaded: {len(adj)} nodes with edges")
    print(f"Node coords: {len(node_coords)}")

    # Test POI pathfinding
    pois = get_all_pois()
    if len(pois) >= 2:
        start = pois[0]["poi_id"]
        end = pois[1]["poi_id"]
        print(f"\nFinding path from {start} to {end}...")
        result = find_path_between_pois(start, end)
        print(json.dumps(result, indent=2))