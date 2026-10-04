from datetime import datetime

import pandas as pd

from src.traffic.snapshot_builder import (
    build_complete_edge_speeds
)


EDGES_PATH = (
    "data/processed/"
    "edges_enriched.csv"
)

LIVE_PATH = (
    "data/traffic/normalized/"
    "2026-10-02/"
    "16-57-46-live-edges.csv"
)


edges = pd.read_csv(
    EDGES_PATH
)

live = pd.read_csv(
    LIVE_PATH
)


timestamp = datetime(
    2026,
    10,
    2,
    16,
    57,
    46
)


snapshot_df = (
    build_complete_edge_speeds(
        edges_df=edges,
        live_df=live,
        timestamp=timestamp
    )
)


print(
    "Total edges:",
    len(snapshot_df)
)

print()

print(
    snapshot_df[
        "provenance"
    ].value_counts()
)

print()

print(
    snapshot_df[
        "speed_kph"
    ].describe()
)


OUTPUT = (
    "data/traffic/snapshots/"
    "2026-10-02/"
    "16-57-46-complete.csv"
)


from pathlib import Path

Path(
    OUTPUT
).parent.mkdir(
    parents=True,
    exist_ok=True
)


snapshot_df.to_csv(
    OUTPUT,
    index=False
)


print()
print(
    "Saved:",
    OUTPUT
)