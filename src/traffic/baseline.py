import ast
import pandas as pd

from .speed_parser import parse_maxspeed


# =========================================================
# Highway priority
# =========================================================

HIGHWAY_PRIORITY = {
    "motorway": 100,
    "motorway_link": 90,

    "trunk": 80,
    "trunk_link": 70,

    "primary": 60,
    "primary_link": 55,

    "secondary": 50,
    "secondary_link": 45,

    "tertiary": 40,
    "tertiary_link": 35,

    "unclassified": 30,
    "residential": 25,

    "living_street": 20,
    "service": 15,

    "road": 10,
}


# =========================================================
# Default free-flow speed by highway type
# =========================================================

HIGHWAY_DEFAULT_SPEED = {
    "motorway": 70.0,
    "motorway_link": 50.0,

    "trunk": 60.0,
    "trunk_link": 45.0,

    "primary": 50.0,
    "primary_link": 40.0,

    "secondary": 40.0,
    "secondary_link": 35.0,

    "tertiary": 35.0,
    "tertiary_link": 30.0,

    "unclassified": 30.0,

    "residential": 25.0,

    "living_street": 15.0,

    "service": 20.0,

    "road": 25.0,
}


DEFAULT_SPEED_KPH = 30.0


# Optional engineering cap used for baseline modeling.
# Keep raw OSM maxspeed separately.
MAX_BASELINE_SPEED_KPH = 80.0


# =========================================================
# Highway normalization
# =========================================================

def choose_highway_type(values) -> str:
    """
    Choose the most important highway type
    if an OSM edge contains multiple types.

    Example:
        ["primary", "trunk"] -> "trunk"
    """

    if not values:
        return "unknown"

    return max(
        values,
        key=lambda x: HIGHWAY_PRIORITY.get(
            str(x),
            -1
        )
    )


def normalize_highway(value) -> str:
    """
    Normalize highway field.

    Examples:
        "primary"
            -> "primary"

        "['primary', 'trunk']"
            -> "trunk"
    """

    if pd.isna(value):
        return "unknown"

    if isinstance(value, str):
        value = value.strip()

        if (
            value.startswith("[")
            and value.endswith("]")
        ):
            try:
                parsed = ast.literal_eval(value)

                if (
                    isinstance(parsed, list)
                    and parsed
                ):
                    parsed = [
                        str(x).strip()
                        for x in parsed
                    ]

                    return choose_highway_type(
                        parsed
                    )

            except (ValueError, SyntaxError):
                pass

        return value

    if isinstance(value, list):
        values = [
            str(x).strip()
            for x in value
        ]

        return choose_highway_type(values)

    return str(value)


# =========================================================
# Baseline speed
# =========================================================

def get_default_speed(
    highway: str
) -> float:
    """
    Return default speed based on highway class.
    """

    return HIGHWAY_DEFAULT_SPEED.get(
        highway,
        DEFAULT_SPEED_KPH
    )


def infer_free_flow_speed(row) -> float:
    """
    Priority:

    1. Valid OSM maxspeed
    2. Default speed by highway type

    maxspeed_kph is retained separately.

    A cap is applied only to the modeled
    free_flow_speed_kph.
    """

    if pd.notna(row["maxspeed_kph"]):
        speed = float(
            row["maxspeed_kph"]
        )

    else:
        speed = get_default_speed(
            row["highway_normalized"]
        )

    # Engineering cap for the traffic model
    speed = min(
        speed,
        MAX_BASELINE_SPEED_KPH
    )

    return speed


# =========================================================
# Main enrichment pipeline
# =========================================================

def enrich_edges(
    input_path: str,
    output_path: str
) -> pd.DataFrame:

    print("Loading edges...")

    edges = pd.read_csv(
        input_path
    )

    print(
        f"Total edges: {len(edges):,}"
    )

    # -----------------------------------------
    # Validate required columns
    # -----------------------------------------

    required_columns = {
        "source",
        "target",
        "edge_key",
        "distance_m",
        "highway",
    }

    missing = (
        required_columns
        - set(edges.columns)
    )

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # -----------------------------------------
    # Basic validation
    # -----------------------------------------

    if (
        edges["distance_m"]
        .isna()
        .any()
    ):
        raise ValueError(
            "Missing distance_m detected"
        )

    if (
        edges["distance_m"]
        <= 0
    ).any():
        raise ValueError(
            "distance_m must be > 0"
        )

    duplicates = edges.duplicated(
        subset=[
            "source",
            "target",
            "edge_key",
        ]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate edge keys detected"
        )

    # -----------------------------------------
    # Normalize highway
    # -----------------------------------------

    print(
        "Normalizing highway types..."
    )

    edges[
        "highway_normalized"
    ] = (
        edges["highway"]
        .apply(normalize_highway)
    )

    # -----------------------------------------
    # Normalize maxspeed
    # -----------------------------------------

    print(
        "Parsing OSM maxspeed..."
    )

    if "maxspeed_raw" in edges.columns:

        edges[
            "maxspeed_kph"
        ] = (
            edges["maxspeed_raw"]
            .apply(parse_maxspeed)
        )

    else:

        edges[
            "maxspeed_kph"
        ] = None

    # -----------------------------------------
    # Build free-flow speed
    # -----------------------------------------

    print(
        "Building free-flow speeds..."
    )

    edges[
        "free_flow_speed_kph"
    ] = (
        edges.apply(
            infer_free_flow_speed,
            axis=1
        )
    )

    # -----------------------------------------
    # Free-flow travel time
    # -----------------------------------------

    edges[
        "free_flow_time_s"
    ] = (
        3.6
        * edges["distance_m"]
        / edges["free_flow_speed_kph"]
    )

    # -----------------------------------------
    # Convenience edge ID
    # -----------------------------------------

    edges["edge_id"] = (
        edges["source"].astype(str)
        + "_"
        + edges["target"].astype(str)
        + "_"
        + edges["edge_key"].astype(str)
    )

    # -----------------------------------------
    # Final validation
    # -----------------------------------------

    if (
        edges[
            "free_flow_speed_kph"
        ]
        <= 0
    ).any():
        raise ValueError(
            "Invalid free-flow speed detected"
        )

    if (
        edges[
            "free_flow_speed_kph"
        ]
        .isna()
        .any()
    ):
        raise ValueError(
            "Missing free-flow speed detected"
        )

    # -----------------------------------------
    # Statistics
    # -----------------------------------------

    total = len(edges)

    osm_speed_count = (
        edges["maxspeed_kph"]
        .notna()
        .sum()
    )

    inferred_count = (
        total
        - osm_speed_count
    )

    print()
    print("=== BASELINE SUMMARY ===")

    print(
        f"Total edges: {total:,}"
    )

    print(
        f"Edges using OSM maxspeed: "
        f"{osm_speed_count:,}"
    )

    print(
        f"Edges using highway fallback: "
        f"{inferred_count:,}"
    )

    print()

    print(
        "Free-flow speed distribution:"
    )

    print(
        edges[
            "free_flow_speed_kph"
        ].describe()
    )

    print()

    print(
        "Normalized highway distribution:"
    )

    print(
        edges[
            "highway_normalized"
        ]
        .value_counts()
        .head(20)
    )

    # -----------------------------------------
    # Save
    # -----------------------------------------

    edges.to_csv(
        output_path,
        index=False
    )

    print()
    print(
        f"Saved enriched edges to: "
        f"{output_path}"
    )

    return edges