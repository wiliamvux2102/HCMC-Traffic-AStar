# src/traffic/normalizer.py

import json
from pathlib import Path
from typing import Any

import pandas as pd
from shapely.geometry import LineString


MPS_TO_KPH = 3.6


def mps_to_kph(value):
    """
    Convert m/s to km/h.
    """

    if value is None:
        return None

    return float(value) * MPS_TO_KPH


def extract_shape_points(shape: dict) -> list[tuple[float, float]]:
    """
    Convert HERE shape structure into an ordered list
    of (longitude, latitude) coordinates.

    HERE:
        shape.links[].points[].lat/lng

    Shapely:
        (x, y) = (longitude, latitude)
    """

    coordinates = []

    links = shape.get(
        "links",
        []
    )

    for link in links:

        points = link.get(
            "points",
            []
        )

        for point in points:

            lat = point.get("lat")
            lng = point.get("lng")

            if (
                lat is None
                or lng is None
            ):
                continue

            coordinate = (
                float(lng),
                float(lat)
            )

            # HERE links often share endpoint.
            # Avoid duplicate consecutive points.
            if (
                not coordinates
                or coordinates[-1] != coordinate
            ):
                coordinates.append(
                    coordinate
                )

    return coordinates


def get_functional_classes(
    shape: dict
) -> list[int]:
    """
    Collect HERE functionalClass values
    from all links in the segment.
    """

    classes = []

    for link in shape.get(
        "links",
        []
    ):

        value = link.get(
            "functionalClass"
        )

        if (
            value is not None
            and value not in classes
        ):
            classes.append(
                int(value)
            )

    return classes


def normalize_here_segment(
    segment: dict,
    segment_index: int,
    timestamp: str
) -> dict | None:
    """
    Normalize one HERE Traffic Flow segment.
    """

    location = segment.get(
        "location",
        {}
    )

    flow = segment.get(
        "currentFlow",
        {}
    )

    speed = flow.get(
        "speed"
    )

    # speed is required for our routing model
    if speed is None:
        return None

    shape = location.get(
        "shape",
        {}
    )

    coordinates = (
        extract_shape_points(
            shape
        )
    )

    # Geometry cannot be mapped to OSM
    # if fewer than 2 points exist.
    if len(coordinates) < 2:
        return None

    geometry = LineString(
        coordinates
    )

    functional_classes = (
        get_functional_classes(
            shape
        )
    )

    return {
        "here_segment_id": (
            f"HERE_{segment_index}"
        ),

        "timestamp": timestamp,

        "description": (
            location.get(
                "description"
            )
        ),

        "length_m": (
            location.get(
                "length"
            )
        ),

        "speed_kph": (
            mps_to_kph(
                speed
            )
        ),

        "speed_uncapped_kph": (
            mps_to_kph(
                flow.get(
                    "speedUncapped"
                )
            )
        ),

        "free_flow_kph": (
            mps_to_kph(
                flow.get(
                    "freeFlow"
                )
            )
        ),

        "jam_factor": (
            flow.get(
                "jamFactor"
            )
        ),

        "jam_tendency": (
            flow.get(
                "jamTendency"
            )
        ),

        "confidence": (
            flow.get(
                "confidence"
            )
        ),

        "traversability": (
            flow.get(
                "traversability"
            )
        ),

        "functional_classes": (
            json.dumps(
                functional_classes
            )
        ),

        # Save as WKT so it can be stored in CSV
        "geometry": (
            geometry.wkt
        ),

        "source": "here",
    }


def normalize_here_response(
    data: dict
) -> pd.DataFrame:
    """
    Normalize complete HERE API response.
    """

    timestamp = data.get(
        "sourceUpdated"
    )

    results = data.get(
        "results",
        []
    )

    normalized_rows = []

    for index, segment in enumerate(
        results
    ):

        row = normalize_here_segment(
            segment=segment,
            segment_index=index,
            timestamp=timestamp
        )

        if row is not None:
            normalized_rows.append(
                row
            )

    return pd.DataFrame(
        normalized_rows
    )


def normalize_here_file(
    input_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Read one saved HERE raw snapshot,
    normalize it and save as CSV.
    """

    input_path = Path(
        input_path
    )

    output_path = Path(
        output_path
    )

    with open(
        input_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    df = normalize_here_response(
        data
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        "Normalized HERE snapshot"
    )

    print(
        "Segments:",
        len(df)
    )

    print(
        "Saved to:",
        output_path
    )

    return df
