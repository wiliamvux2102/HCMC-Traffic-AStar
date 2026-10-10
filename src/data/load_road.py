from pathlib import Path

import osmnx as ox


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CENTER_POINT = (10.7769, 106.7009)

# Distance from the center to each side of the bounding box.
DISTANCE = 15000

RAW_DIR = PROJECT_ROOT / "data/raw/osm"
GRAPH_FILE = RAW_DIR / "hcmc_drive.graphml"


def load_road_network():
    print("Loading road network from OpenStreetMap...")
    print(f"Center: {CENTER_POINT}")
    print(f"Distance to each side: {DISTANCE} m")
    print("Simplification: disabled")
    print("Intermediate OSM road nodes will be retained.")

    graph = ox.graph.graph_from_point(
        center_point=CENTER_POINT,
        dist=DISTANCE,
        dist_type="bbox",
        network_type="drive",
        simplify=False,
        retain_all=False,
    )

    print()
    print("Road network loaded.")
    print(f"Nodes: {len(graph.nodes)}")
    print(f"Edges: {len(graph.edges)}")

    return graph


def save_road_network(graph):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Replace the existing graph only after saving succeeds.
    temporary_file = RAW_DIR / "hcmc_drive.pending.graphml"

    ox.io.save_graphml(
        graph,
        filepath=temporary_file,
    )

    temporary_file.replace(GRAPH_FILE)

    print(f"Graph saved to: {GRAPH_FILE}")


if __name__ == "__main__":
    graph = load_road_network()
    save_road_network(graph)