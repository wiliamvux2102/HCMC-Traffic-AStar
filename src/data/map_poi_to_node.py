import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from pathlib import Path


NODES_FILE = "data/processed/nodes.csv"
POIS_FILE = "data/processed/pois.csv"

OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "poi_node_mapping.csv"


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using Haversine formula.
    Result is in meters.
    """

    R = 6371000  # Earth radius in meters

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)

    dlat = lat2 - lat1
    dlon = np.radians(lon2 - lon1)

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    return 2 * R * np.arcsin(np.sqrt(a))


def map_pois_to_nodes():

    print("Loading road nodes...")
    nodes = pd.read_csv(NODES_FILE)

    print(f"Road nodes: {len(nodes)}")

    print("Loading POIs...")
    pois = pd.read_csv(POIS_FILE)

    print(f"POIs: {len(pois)}")

    # --------------------------------------------------
    # Build KDTree
    # --------------------------------------------------

    # KDTree uses:
    # [longitude, latitude]

    node_coordinates = nodes[
        ["longitude", "latitude"]
    ].to_numpy()

    tree = cKDTree(node_coordinates)

    # --------------------------------------------------
    # Find nearest node for every POI
    # --------------------------------------------------

    poi_coordinates = pois[
        ["longitude", "latitude"]
    ].to_numpy()

    distances, indices = tree.query(
        poi_coordinates,
        k=1
    )

    # --------------------------------------------------
    # Create result
    # --------------------------------------------------

    result = pois[
        [
            "poi_id",
            "name",
            "category",
            "latitude",
            "longitude"
        ]
    ].copy()

    result["nearest_node"] = nodes.iloc[
        indices
    ]["node_id"].to_numpy()

    # --------------------------------------------------
    # Calculate real distance in meters
    # --------------------------------------------------

    nearest_nodes = nodes.iloc[
        indices
    ]

    result["distance_to_node_m"] = haversine_distance(
        result["latitude"].to_numpy(),
        result["longitude"].to_numpy(),
        nearest_nodes["latitude"].to_numpy(),
        nearest_nodes["longitude"].to_numpy()
    )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    print()
    print("========== RESULT ==========")

    print(
        f"Mapped POIs: {len(result)}"
    )

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

    print()
    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    map_pois_to_nodes()