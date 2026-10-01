import ast
import pandas as pd

from .speed_parser import parse_maxspeed


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

    "residential": 25.0,

    "service": 20.0,

    "living_street": 15.0,

    "unclassified": 30.0,
}

DEFAULT_SPEED_KPH = 30.0


def normalize_highway(value) -> str:
    """
    Chuẩn hóa OSM highway attribute.

    Example:
        "primary"
        "['primary', 'secondary']"

    Nếu có nhiều loại, tạm chọn phần tử đầu tiên.
    """

    if pd.isna(value):
        return "unknown"

    if isinstance(value, str):
        value = value.strip()

        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = ast.literal_eval(value)

                if isinstance(parsed, list) and parsed:
                    return str(parsed[0])

            except (ValueError, SyntaxError):
                pass

        return value

    if isinstance(value, list) and value:
        return str(value[0])

    return str(value)


def get_default_speed(highway: str) -> float:
    return HIGHWAY_DEFAULT_SPEED.get(
        highway,
        DEFAULT_SPEED_KPH
    )


def infer_free_flow_speed(row) -> float:
    """
    Priority:

    1. maxspeed từ OSM
    2. highway default
    """

    if pd.notna(row["maxspeed_kph"]):
        return float(row["maxspeed_kph"])

    return get_default_speed(
        row["highway_normalized"]
    )


def enrich_edges(
    input_path: str,
    output_path: str
) -> pd.DataFrame:

    edges = pd.read_csv(input_path)

    required_columns = {
        "source",
        "target",
        "edge_key",
        "distance_m",
        "highway",
    }

    missing = required_columns - set(edges.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # ------------------------
    # Normalize highway
    # ------------------------

    edges["highway_normalized"] = (
        edges["highway"]
        .apply(normalize_highway)
    )

    # ------------------------
    # Normalize maxspeed
    # ------------------------

    if "maxspeed_raw" in edges.columns:
        edges["maxspeed_kph"] = (
            edges["maxspeed_raw"]
            .apply(parse_maxspeed)
        )

    else:
        edges["maxspeed_kph"] = None

    # ------------------------
    # Free-flow speed
    # ------------------------

    edges["free_flow_speed_kph"] = (
        edges.apply(
            infer_free_flow_speed,
            axis=1
        )
    )

    # ------------------------
    # Free-flow time
    # ------------------------

    edges["free_flow_time_s"] = (
        3.6
        * edges["distance_m"]
        / edges["free_flow_speed_kph"]
    )

    # Validation
    if (edges["free_flow_speed_kph"] <= 0).any():
        raise ValueError(
            "Invalid free-flow speed detected"
        )

    if (edges["distance_m"] <= 0).any():
        raise ValueError(
            "Invalid edge distance detected"
        )

    edges.to_csv(
        output_path,
        index=False
    )

    return edges