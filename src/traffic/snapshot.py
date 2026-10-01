import pandas as pd

from .models import TrafficSnapshot


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
            int(row.source),
            int(row.target),
            int(row.edge_key),
        )

        speed = float(row.speed_kph)

        if speed <= 0:
            raise ValueError(
                f"Invalid speed {speed} for {key}"
            )

        edge_speed[key] = speed

        provenance[key] = row.provenance

    return TrafficSnapshot(
        timestamp=timestamp,
        edge_speed=edge_speed,
        provenance=provenance,
    )