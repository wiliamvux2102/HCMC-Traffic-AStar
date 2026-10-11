from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd

from map_poi_to_node import (
    get_largest_scc_nodes,
    haversine_distance,
    require_columns,
    validate_coordinates,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data/processed"

INPUT_FILE = DATA_DIR / "poi_node_mapping.csv"
OUTPUT_FILE = DATA_DIR / "poi_final.csv"
NODES_FILE = DATA_DIR / "nodes.csv"
EDGES_FILE = DATA_DIR / "edges.csv"

MAX_DISTANCE_M = 500
MIN_POIS = 100

OUTPUT_COLUMNS = [
    "poi_id",
    "name",
    "category",
    "latitude",
    "longitude",
    "nearest_node",
    "distance_to_node_m",
]

# Identify the reviewed duplicate pair by name rather than sequential POI IDs.
NOWZONE_KEEP_NAME = "Trung Tâm Mua Sắm Nowzone - Nguyễn Văn Cừ"
NOWZONE_DROP_NAME = "Trung Tâm Mua Sắm Nowzone"
NOWZONE_MAX_SEPARATION_M = 30


def normalize_name(value):
    text = unicodedata.normalize("NFC", str(value))
    return " ".join(text.casefold().split())


def remove_reviewed_duplicates(df):
    """
    Merge only the reviewed Nowzone pair.

    Different POIs sharing a road node are not automatically duplicates.
    """
    names = df["name"].map(normalize_name)

    keep_candidates = df.loc[
        (df["category"] == "mall")
        & (names == normalize_name(NOWZONE_KEEP_NAME))
    ]

    drop_candidates = df.loc[
        (df["category"] == "mall")
        & (names == normalize_name(NOWZONE_DROP_NAME))
    ]

    if keep_candidates.empty or drop_candidates.empty:
        return df.copy()

    if len(keep_candidates) != 1 or len(drop_candidates) != 1:
        raise ValueError(
            "Có nhiều bản ghi Nowzone khớp quy tắc. "
            "Cần kiểm tra trước khi gộp."
        )

    keep = keep_candidates.iloc[0]
    drop = drop_candidates.iloc[0]

    separation = float(haversine_distance(
        keep["latitude"],
        keep["longitude"],
        drop["latitude"],
        drop["longitude"],
    ))

    if (
        keep["nearest_node"] != drop["nearest_node"]
        or separation > NOWZONE_MAX_SEPARATION_M
    ):
        raise ValueError(
            "Cặp Nowzone không còn khớp điều kiện đã kiểm tra: "
            "cùng node đường và cách nhau không quá 30 m."
        )

    print()
    print("========== REVIEWED DUPLICATE ==========")
    print(f"Keep: {keep['poi_id']} - {keep['name']}")
    print(f"Remove: {drop['poi_id']} - {drop['name']}")
    print(f"POI coordinate separation: {separation:.2f} m")

    # Preserve the identifiers and order of the remaining POIs.
    return df.drop(index=drop_candidates.index).copy()


def validate_mapping():
    print("Loading POI-node mapping...")
    df = pd.read_csv(INPUT_FILE)

    require_columns(df, OUTPUT_COLUMNS, "POI mapping")
    df = df[OUTPUT_COLUMNS].copy()

    if df.isna().any().any():
        raise ValueError("POI mapping: có dữ liệu bị thiếu.")

    if df["poi_id"].duplicated().any():
        raise ValueError("POI mapping: poi_id trùng lặp.")

    validate_coordinates(df, "POI mapping")

    df["distance_to_node_m"] = pd.to_numeric(
        df["distance_to_node_m"],
        errors="coerce",
    )

    distances = df["distance_to_node_m"].to_numpy(dtype=float)

    if not np.isfinite(distances).all() or (distances < 0).any():
        raise ValueError(
            "POI mapping: khoảng cách phải hữu hạn và không âm."
        )

    print("Checking road-node references and connectivity...")
    nodes = pd.read_csv(NODES_FILE)
    edges = pd.read_csv(EDGES_FILE)

    require_columns(
        nodes,
        ["node_id", "latitude", "longitude"],
        "Nodes",
    )
    validate_coordinates(nodes, "Nodes")

    eligible_nodes = get_largest_scc_nodes(nodes, edges)

    missing_nodes = ~df["nearest_node"].isin(nodes["node_id"])
    if missing_nodes.any():
        ids = df.loc[missing_nodes, "poi_id"].tolist()
        raise ValueError(f"POI tham chiếu node không tồn tại: {ids}")

    # Membership in one strong component guarantees mutual directed reachability.
    outside_scc = ~df["nearest_node"].isin(eligible_nodes["node_id"])
    if outside_scc.any():
        ids = df.loc[outside_scc, "poi_id"].tolist()
        raise ValueError(
            f"POI chưa được gắn vào thành phần liên thông mạnh "
            f"lớn nhất: {ids}. Hãy chạy lại map_poi_to_node.py."
        )

    # Recompute distances to detect mappings inconsistent with the current nodes.
    mapped_nodes = nodes.set_index("node_id").loc[
        df["nearest_node"].to_numpy()
    ]

    actual_distances = haversine_distance(
        df["latitude"].to_numpy(),
        df["longitude"].to_numpy(),
        mapped_nodes["latitude"].to_numpy(),
        mapped_nodes["longitude"].to_numpy(),
    )

    if not np.allclose(
        distances,
        actual_distances,
        rtol=0,
        atol=0.01,
    ):
        raise ValueError(
            "Khoảng cách trong mapping không khớp tọa độ "
            "POI và node. Hãy chạy lại map_poi_to_node.py."
        )

    invalid = df.loc[
        df["distance_to_node_m"] > MAX_DISTANCE_M
    ].copy()

    valid = df.loc[
        df["distance_to_node_m"] <= MAX_DISTANCE_M
    ].copy()

    print()
    print("========== DISTANCE VALIDATION ==========")
    print(f"Total mapped POIs: {len(df)}")
    print(f"Within {MAX_DISTANCE_M} m: {len(valid)}")
    print(f"Beyond {MAX_DISTANCE_M} m: {len(invalid)}")

    if not invalid.empty:
        print(
            invalid[
                ["poi_id", "name", "distance_to_node_m"]
            ].to_string(index=False)
        )

    before_deduplication = len(valid)
    valid = remove_reviewed_duplicates(valid)

    if len(valid) < MIN_POIS:
        raise ValueError(
            f"Chỉ còn {len(valid)} POI; yêu cầu tối thiểu {MIN_POIS}."
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    valid.to_csv(OUTPUT_FILE, index=False)

    print()
    print("========== FINAL RESULT ==========")
    print(
        f"Reviewed duplicates removed: "
        f"{before_deduplication - len(valid)}"
    )
    print(f"Final POIs: {len(valid)}")
    print(f"Categories: {valid['category'].nunique()}")
    print("Directed paths exist between all retained POI nodes.")
    print(f"Saved to: {OUTPUT_FILE}")

    return valid


if __name__ == "__main__":
    validate_mapping()