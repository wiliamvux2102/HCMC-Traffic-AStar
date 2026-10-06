# src/traffic/fallback_provider.py

from datetime import datetime

import pandas as pd

from src.traffic.provider import (
    TrafficProvider
)

from src.traffic.snapshot import (
    dataframe_to_snapshot
)


MIN_SPEED_KPH = 5.0


def get_time_factor(
    timestamp: datetime
) -> float:

    hour = (
        timestamp.hour
        + timestamp.minute / 60.0
    )

    if 7.0 <= hour < 9.0:
        return 0.55

    if 9.0 <= hour < 16.0:
        return 0.80

    if 16.0 <= hour < 19.0:
        return 0.50

    if 19.0 <= hour < 22.0:
        return 0.75

    return 0.90


def build_fallback_speeds(
    edges_df: pd.DataFrame,
    timestamp: datetime
) -> pd.DataFrame:

    fallback = edges_df[
        [
            "source",
            "target",
            "edge_key",
            "free_flow_speed_kph",
        ]
    ].copy()

    factor = get_time_factor(
        timestamp
    )

    fallback["speed_kph"] = (
        fallback[
            "free_flow_speed_kph"
        ]
        * factor
    ).clip(
        lower=MIN_SPEED_KPH
    )

    fallback["provenance"] = (
        "fallback"
    )

    return fallback[
        [
            "source",
            "target",
            "edge_key",
            "speed_kph",
            "provenance",
        ]
    ]


class FallbackProvider(
    TrafficProvider
):

    def __init__(
        self,
        edges_path: str
    ):

        self.edges = pd.read_csv(
            edges_path
        )


    def get_snapshot(
        self,
        timestamp: datetime
    ):

        df = build_fallback_speeds(
            self.edges,
            timestamp
        )

        return dataframe_to_snapshot(
            df,
            timestamp.isoformat()
        )
