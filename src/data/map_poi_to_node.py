from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data/processed"

NODES_FILE = DATA_DIR / "nodes.csv"
EDGES_FILE = DATA_DIR / "edges.csv"
POIS_FILE = DATA_DIR / "pois.csv"
OUTPUT_FILE = DATA_DIR / "poi_node_mapping.csv"

EARTH_RADIUS_M = 6_371_000

POI_COLUMNS = [
    "poi_id",
    "name",
    "category",
    "latitude",
    "longitude",
]


def require_columns(df, columns, label):
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{label}: thiếu cột {missing}.")

    if df.empty:
        raise ValueError(f"{label}: dữ liệu rỗng.")


def validate_coordinates(df, label):
    for column in ["latitude", "longitude"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    coordinates = df[["latitude", "longitude"]].to_numpy(dtype=float)

    valid = (
        np.isfinite(coordinates).all(axis=1)
        & df["latitude"].between(-90, 90).to_numpy()
        & df["longitude"].between(-180, 180).to_numpy()
    )

    if not valid.all():
        lines = (np.flatnonzero(~valid) + 2).tolist()
        raise ValueError(
            f"{label}: tọa độ không hợp lệ tại dòng CSV {lines[:10]}."
        )


def get_largest_scc_nodes(nodes, edges):
    """
    Return nodes in the largest strongly connected component.

    Each CSV edge is directed from source to target.
    Do not automatically add reverse edges.
    """
    require_columns(
        nodes,
        ["node_id", "latitude", "longitude"],
        "Nodes",
    )
    require_columns(edges, ["source", "target"], "Edges")

    if nodes["node_id"].isna().any():
        raise ValueError("Nodes: node_id bị thiếu.")

    if nodes["node_id"].duplicated().any():
        raise ValueError("Nodes: node_id trùng lặp.")

    node_index = pd.Index(nodes["node_id"])

    source_positions = node_index.get_indexer(edges["source"])
    target_positions = node_index.get_indexer(edges["target"])

    if (source_positions < 0).any() or (target_positions < 0).any():
        raise ValueError(
            "Edges: có source hoặc target không tồn tại trong nodes.csv."
        )

    adjacency = csr_matrix(
        (
            np.ones(len(edges), dtype=np.float64),
            (source_positions, target_positions),
        ),
        shape=(len(nodes), len(nodes)),
    )

    component_count, labels = connected_components(
        adjacency,
        directed=True,
        connection="strong",
    )

    component_sizes = np.bincount(labels)
    largest_label = int(component_sizes.argmax())

    eligible_nodes = nodes.loc[labels == largest_label].copy()

    print(f"Strongly connected components: {component_count}")
    print(f"Nodes eligible for POI mapping: {len(eligible_nodes)}")

    return eligible_nodes


def latlon_to_unit_xyz(latitudes, longitudes):
    lat = np.radians(np.asarray(latitudes, dtype=float))
    lon = np.radians(np.asarray(longitudes, dtype=float))

    return np.column_stack((
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ))


def haversine_distance(lat1, lon1, lat2, lon2):
    lat1 = np.radians(np.asarray(lat1, dtype=float))
    lon1 = np.radians(np.asarray(lon1, dtype=float))
    lat2 = np.radians(np.asarray(lat2, dtype=float))
    lon2 = np.radians(np.asarray(lon2, dtype=float))

    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin((lon2 - lon1) / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_M
        * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    )


def map_pois_to_nodes():
    print("Loading road nodes and edges...")
    nodes = pd.read_csv(NODES_FILE)
    edges = pd.read_csv(EDGES_FILE)

    require_columns(
        nodes,
        ["node_id", "latitude", "longitude"],
        "Nodes",
    )
    validate_coordinates(nodes, "Nodes")

    print(f"Road nodes: {len(nodes)}")
    print(f"Road edges: {len(edges)}")

    eligible_nodes = get_largest_scc_nodes(nodes, edges)

    print("Loading POIs...")
    pois = pd.read_csv(POIS_FILE)

    require_columns(pois, POI_COLUMNS, "POIs")
    validate_coordinates(pois, "POIs")

    if pois[POI_COLUMNS].isna().any().any():
        raise ValueError("POIs: có dữ liệu bắt buộc bị thiếu.")

    if pois["poi_id"].duplicated().any():
        raise ValueError("POIs: poi_id trùng lặp.")

    node_xyz = latlon_to_unit_xyz(
        eligible_nodes["latitude"],
        eligible_nodes["longitude"],
    )
    poi_xyz = latlon_to_unit_xyz(
        pois["latitude"],
        pois["longitude"],
    )

    tree = cKDTree(node_xyz)
    _, indices = tree.query(poi_xyz, k=1)

    nearest_nodes = eligible_nodes.iloc[indices]

    # Preserve the original seven-column output schema.
    result = pois[POI_COLUMNS].copy()

    result["nearest_node"] = nearest_nodes["node_id"].to_numpy()
    result["distance_to_node_m"] = haversine_distance(
        result["latitude"].to_numpy(),
        result["longitude"].to_numpy(),
        nearest_nodes["latitude"].to_numpy(),
        nearest_nodes["longitude"].to_numpy(),
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print()
    print("========== RESULT ==========")
    print(f"Mapped POIs: {len(result)}")
    print(
        f"Average distance: "
        f"{result['distance_to_node_m'].mean():.2f} m"
    )
    print(
        f"Maximum distance: "
        f"{result['distance_to_node_m'].max():.2f} m"
    )
    print(
        f"Minimum distance: "
        f"{result['distance_to_node_m'].min():.2f} m"
    )
    print(f"Saved to: {OUTPUT_FILE}")

    return result


if __name__ == "__main__":
    map_pois_to_nodes()