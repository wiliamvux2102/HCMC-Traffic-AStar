# src/traffic/snapshot.py

import pandas as pd
import math
from decimal import Decimal

from src.traffic.models import (
    EdgeKey,
    TrafficSnapshot
)


REQUIRED_COLUMNS = {
    "source",
    "target",
    "edge_key",
    "speed_kph",
    "provenance",
}


def dataframe_to_snapshot(
    df: pd.DataFrame,
    timestamp: str
) -> TrafficSnapshot:

    missing = (
        REQUIRED_COLUMNS
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"Missing snapshot columns: {missing}"
        )


    if df["speed_kph"].isna().any():
        raise ValueError(
            "Snapshot contains missing speed"
        )


    if (
        df["speed_kph"] <= 0
    ).any():
        raise ValueError(
            "Snapshot contains speed <= 0"
        )


    duplicated = df.duplicated(
        subset=[
            "source",
            "target",
            "edge_key"
        ]
    )

    if duplicated.any():
        raise ValueError(
            "Snapshot contains duplicated OSM edges"
        )


    edge_speed = {}

    provenance = {}


    for row in df.itertuples(
        index=False
    ):

        key: EdgeKey = (
            int(row.source),
            int(row.target),
            int(row.edge_key)
        )

        edge_speed[key] = float(
            row.speed_kph
        )

        provenance[key] = str(
            row.provenance
        )


    return TrafficSnapshot(
        timestamp=timestamp,
        edge_speed=edge_speed,
        provenance=provenance
    )


def load_snapshot_csv(
    path: str,
    timestamp: str
) -> TrafficSnapshot:

    df = pd.read_csv(
        path
    )

    return dataframe_to_snapshot(
        df,
        timestamp
    )
