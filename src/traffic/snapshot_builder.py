# src/traffic/snapshot_builder.py

from datetime import datetime

import pandas as pd

from src.traffic.fallback_provider import (
    build_fallback_speeds
)


EDGE_KEY_COLUMNS = [
    "source",
    "target",
    "edge_key",
]


def build_complete_edge_speeds(
    edges_df: pd.DataFrame,
    live_df: pd.DataFrame,
    timestamp: datetime
) -> pd.DataFrame:
    """
    Build one complete traffic state.

    Priority:
        LIVE > FALLBACK
    """

    # -----------------------------------------------------
    # 1. Build fallback for every edge
    # -----------------------------------------------------

    fallback = (
        build_fallback_speeds(
            edges_df,
            timestamp
        )
    )

    fallback = fallback.rename(
        columns={
            "speed_kph":
                "fallback_speed_kph"
        }
    )

    # -----------------------------------------------------
    # 2. Prepare live data
    # -----------------------------------------------------

    live = live_df[
        [
            "source",
            "target",
            "edge_key",
            "speed_kph",
        ]
    ].copy()

    live = live.rename(
        columns={
            "speed_kph":
                "live_speed_kph"
        }
    )

    # -----------------------------------------------------
    # 3. LEFT JOIN
    # -----------------------------------------------------

    result = fallback.merge(
        live,
        on=EDGE_KEY_COLUMNS,
        how="left"
    )

    # -----------------------------------------------------
    # 4. LIVE wins if available
    # -----------------------------------------------------

    has_live = (
        result[
            "live_speed_kph"
        ]
        .notna()
    )

    result["speed_kph"] = (
        result[
            "fallback_speed_kph"
        ]
    )

    result.loc[
        has_live,
        "speed_kph"
    ] = result.loc[
        has_live,
        "live_speed_kph"
    ]

    result["provenance"] = (
        "fallback"
    )

    result.loc[
        has_live,
        "provenance"
    ] = "live"

    # -----------------------------------------------------
    # 5. Validate
    # -----------------------------------------------------

    if result[
        "speed_kph"
    ].isna().any():

        raise ValueError(
            "Some edges have missing speed"
        )

    if (
        result[
            "speed_kph"
        ] <= 0
    ).any():

        raise ValueError(
            "Some edges have invalid speed <= 0"
        )

    return result[
        [
            "source",
            "target",
            "edge_key",
            "speed_kph",
            "provenance",
        ]
    ]