import osmnx as ox
from pathlib import Path


GRAPH_FILE = "data/raw/osm/hcmc_drive.graphml"
OUTPUT_DIR = Path("data/processed")


def export_graph():
    print("Loading graph...")

    # Load graph 
    G = ox.io.load_graphml(GRAPH_FILE)

    print(f"Nodes in graph: {len(G.nodes)}")
    print(f"Edges in graph: {len(G.edges)}")

    # NetworkX -> GeoDataFrame
    nodes, edges = ox.convert.graph_to_gdfs(
        G,
        nodes=True,
        edges=True
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # =========================
    # Export nodes
    # =========================

    nodes_df = nodes.reset_index()

    nodes_df = nodes_df[
        ["osmid", "x", "y"]
    ]

    nodes_df = nodes_df.rename(
        columns={
            "osmid": "node_id",
            "x": "longitude",
            "y": "latitude"
        }
    )

    nodes_df.to_csv(
        OUTPUT_DIR / "nodes.csv",
        index=False
    )

    # =========================
    # Export edges
    # =========================

    edges_df = edges.reset_index()

    wanted_columns = [
        "u",
        "v",
        "key",
        "length",
        "highway",
        "oneway",
        "maxspeed",
        "geometry"
    ]

    # Chỉ lấy những cột thực sự tồn tại trong graph
    available_columns = [
        col for col in wanted_columns
        if col in edges_df.columns
    ]

    edges_df = edges_df[available_columns]

    edges_df = edges_df.rename(
    columns={
        "u": "source",
        "v": "target",
        "key": "edge_key",
        "length": "distance_m",
        "maxspeed": "maxspeed_raw"
    }
)

    edges_df.to_csv(
        OUTPUT_DIR / "edges.csv",
        index=False
    )

    print()
    print("Export completed!")
    print(f"Nodes saved: {OUTPUT_DIR / 'nodes.csv'}")
    print(f"Edges saved: {OUTPUT_DIR / 'edges.csv'}")


if __name__ == "__main__":
    export_graph()