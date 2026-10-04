import pandas as pd


MAX_DISTANCE_M = 20.0
MAX_HEADING_DIFF_DEG = 45.0


def calculate_mapping_score(df):
    """
    Calculate confidence score for each
    HERE -> OSM mapping row.
    """

    df = df.copy()

    df["heading_score"] = (
        1.0
        -
        df["heading_diff_deg"]
        / MAX_HEADING_DIFF_DEG
    ).clip(
        lower=0.0,
        upper=1.0
    )

    df["distance_score"] = (
        1.0
        -
        df["distance_m"]
        / MAX_DISTANCE_M
    ).clip(
        lower=0.0,
        upper=1.0
    )

    df["mapping_score"] = (
        0.60
        * df["overlap_ratio"]
        +
        0.30
        * df["heading_score"]
        +
        0.10
        * df["distance_score"]
    )

    return df

def resolve_osm_conflicts(
    mapping_df
):
    """
    If multiple HERE segments map to the same
    OSM edge, keep the geometrically best match.
    """

    scored = (
        calculate_mapping_score(
            mapping_df
        )
    )

    scored = scored.sort_values(
        "mapping_score",
        ascending=False
    )

    resolved = (
        scored
        .drop_duplicates(
            subset=[
                "osm_source",
                "osm_target",
                "osm_edge_key"
            ],
            keep="first"
        )
        .copy()
    )

    return resolved


def build_live_edge_speeds(
    resolved_df
):
    """
    Convert resolved HERE mappings into
    the format expected by TrafficSnapshot.
    """

    live = resolved_df[
        [
            "osm_source",
            "osm_target",
            "osm_edge_key",
            "here_speed_kph",
            "mapping_score"
        ]
    ].copy()

    live = live.rename(
        columns={
            "osm_source":
                "source",

            "osm_target":
                "target",

            "osm_edge_key":
                "edge_key",

            "here_speed_kph":
                "speed_kph"
        }
    )

    live["provenance"] = "live"

    return live