import osmnx as ox
from pathlib import Path


# Center of Ho Chi Minh City
CENTER_POINT = (10.7769, 106.7009)

# Radius in meters
DISTANCE = 15000

# Output
RAW_DIR = Path("data/raw/osm")
GRAPH_FILE = RAW_DIR / "hcmc_drive.graphml"


def load_road_network():
    print("Downloading road network...")

    G = ox.graph.graph_from_point(
        center_point=CENTER_POINT,
        dist=DISTANCE,
        dist_type="bbox",
        network_type="drive",
        simplify=True,
        retain_all=False
    )

    print("Graph downloaded.")
    print(f"Nodes: {len(G.nodes)}")
    print(f"Edges: {len(G.edges)}")

    return G


def save_road_network(G):
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    ox.io.save_graphml(
        G,
        filepath=GRAPH_FILE
    )

    print(f"Graph saved to: {GRAPH_FILE}")


if __name__ == "__main__":
    G = load_road_network()
    save_road_network(G)