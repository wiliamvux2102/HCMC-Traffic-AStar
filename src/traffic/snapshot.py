import pandas as pd
import math
from decimal import Decimal

from .models import TrafficSnapshot


def edge_integer(value):
    number = Decimal(str(value))
    if not number.is_finite() or number != number.to_integral_value():
        raise ValueError(f"Invalid integer edge ID: {value}")
    return int(number)


def snapshot_from_dataframe(
    df: pd.DataFrame,
    timestamp: str
) -> TrafficSnapshot:
    """
        Create TrafficSnapshot from DataFrame
    """

    required = {
        "source",
        "target",
        "edge_key",
        "speed_kph",
        "provenance",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Snapshot missing columns: {missing}"
        )

    edge_speed = {}
    provenance = {}

    for row in df.itertuples(index=False):

        key = (
            edge_integer(row.source),
            edge_integer(row.target),
            edge_integer(row.edge_key),
        )

        speed = float(row.speed_kph)

        if not math.isfinite(speed) or speed <= 0:
            raise ValueError(
                f"Invalid speed {speed} for {key}"
            )

        if key in edge_speed:
            raise ValueError(f"Duplicate edge in snapshot: {key}")
        edge_speed[key] = speed

        provenance[key] = row.provenance

    return TrafficSnapshot(
        timestamp=timestamp,
        edge_speed=edge_speed,
        provenance=provenance,
    )
