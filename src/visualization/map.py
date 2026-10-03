"""Map visualization utilities for HCMC Traffic A*."""

import json
import os
from pathlib import Path
import pandas as pd


# Data file paths
NODES_FILE = "data/processed/nodes.csv"
EDGES_FILE = "data/processed/edges.csv"
POI_FILE = "data/processed/poi_final.csv"

# HCMC center coordinates
HCMC_CENTER = {"lat": 10.7769, "lon": 106.7009}


def load_nodes():
    """Load road nodes from CSV."""
    if not os.path.exists(NODES_FILE):
        return []
    df = pd.read_csv(NODES_FILE)
    return df[["node_id", "longitude", "latitude"]].to_dict("records")


def load_edges():
    """Load road edges from CSV."""
    if not os.path.exists(EDGES_FILE):
        return []
    df = pd.read_csv(EDGES_FILE)
    return df[["source", "target", "edge_key", "distance_m", "highway", "oneway", "geometry"]].to_dict("records")


def load_pois():
    """Load POIs from CSV."""
    if not os.path.exists(POI_FILE):
        return []
    df = pd.read_csv(POI_FILE)
    return df[["poi_id", "name", "category", "latitude", "longitude", "nearest_node", "distance_to_node_m"]].to_dict("records")


def get_map_bounds():
    """Get the bounding box of the road network."""
    nodes = load_nodes()
    if not nodes:
        return {"min_lat": 10.5, "max_lat": 11.0, "min_lon": 106.5, "max_lon": 107.0}

    lats = [n["latitude"] for n in nodes]
    lons = [n["longitude"] for n in nodes]

    return {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lon": min(lons),
        "max_lon": max(lons)
    }


def generate_geojson_edges(sample_size=None):
    """
    Generate GeoJSON LineString features for edges.
    For performance, can sample a subset of edges.
    """
    edges = load_edges()
    nodes = load_nodes()

    # Create node lookup
    node_lookup = {n["node_id"]: (n["longitude"], n["latitude"]) for n in nodes}

    features = []

    # Sample if requested
    if sample_size and len(edges) > sample_size:
        import random
        random.seed(42)
        edges = random.sample(edges, sample_size)

    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]

        if source_id in node_lookup and target_id in node_lookup:
            source_coords = node_lookup[source_id]
            target_coords = node_lookup[target_id]

            # Determine color based on highway type
            highway = edge.get("highway", "residential")
            if highway in ["motorway", "trunk", "primary"]:
                color = "#e34948"  # red - major roads
                weight = 2
            elif highway in ["secondary", "tertiary"]:
                color = "#eb6834"  # orange - secondary roads
                weight = 1.5
            else:
                color = "#898781"  # muted - minor roads
                weight = 1

            features.append({
                "type": "Feature",
                "properties": {
                    "source": source_id,
                    "target": target_id,
                    "edge_key": edge.get("edge_key", 0),
                    "distance_m": edge.get("distance_m", 0),
                    "highway": highway,
                    "oneway": edge.get("oneway", False),
                    "color": color,
                    "weight": weight
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [source_coords, target_coords]
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }


def generate_geojson_nodes(sample_size=None):
    """Generate GeoJSON Point features for nodes."""
    nodes = load_nodes()

    features = []

    if sample_size and len(nodes) > sample_size:
        import random
        random.seed(42)
        nodes = random.sample(nodes, sample_size)

    for node in nodes:
        features.append({
            "type": "Feature",
            "properties": {
                "node_id": node["node_id"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [node["longitude"], node["latitude"]]
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


def generate_geojson_pois():
    """Generate GeoJSON Point features for POIs with category styling."""
    pois = load_pois()

    # Category colors from the dataviz palette
    category_colors = {
        "university": "#2a78d6",      # blue
        "hospital": "#e34948",        # red
        "school": "#1baf7a",          # aqua
        "hotel": "#eda100",           # yellow
        "park": "#008300",            # green
        "supermarket": "#e87ba4",     # magenta
        "mall": "#4a3aa7",            # violet
        "tourist_attraction": "#eb6834",  # orange
        "museum": "#e34948",          # red
        "bus_station": "#2a78d6"      # blue
    }

    category_icons = {
        "university": "🏫",
        "hospital": "🏥",
        "school": "🏫",
        "hotel": "🏨",
        "park": "🌳",
        "supermarket": "🛒",
        "mall": "🏬",
        "tourist_attraction": "🏛️",
        "museum": "🏛️",
        "bus_station": "🚌"
    }

    features = []
    for poi in pois:
        category = poi.get("category", "unknown")
        features.append({
            "type": "Feature",
            "properties": {
                "poi_id": poi["poi_id"],
                "name": poi["name"],
                "category": category,
                "nearest_node": poi.get("nearest_node"),
                "distance_to_node_m": poi.get("distance_to_node_m", 0),
                "color": category_colors.get(category, "#898781"),
                "icon": category_icons.get(category, "📍")
            },
            "geometry": {
                "type": "Point",
                "coordinates": [poi["longitude"], poi["latitude"]]
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }


def get_categories():
    """Get list of unique POI categories."""
    pois = load_pois()
    categories = sorted(set(p.get("category", "") for p in pois if p.get("category")))
    return categories


def get_poi_by_id(poi_id):
    """Get a specific POI by ID."""
    pois = load_pois()
    for poi in pois:
        if poi["poi_id"] == poi_id:
            return poi
    return None


if __name__ == "__main__":
    # Test the functions
    print("Loading data...")
    nodes = load_nodes()
    edges = load_edges()
    pois = load_pois()

    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    print(f"POIs: {len(pois)}")
    print(f"Categories: {get_categories()}")
    print(f"Bounds: {get_map_bounds()}")