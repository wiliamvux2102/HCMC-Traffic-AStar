import pandas as pd

from src.traffic.mapping_resolver import (
    resolve_osm_conflicts,
    build_live_edge_speeds
)


mapping = pd.read_csv(
    "data/traffic/mapping/"
    "00-25-14-grid-mapping.csv"
)


resolved = (
    resolve_osm_conflicts(
        mapping
    )
)


print(
    "Original mapping rows:",
    len(mapping)
)

print(
    "Resolved OSM edges:",
    len(resolved)
)


live = (
    build_live_edge_speeds(
        resolved
    )
)


print()
print(live.head())


OUTPUT = (
    "data/traffic/normalized/"
    "2026-10-03/"
    "00-25-14-grid-live-edges.csv"
)


live.to_csv(
    OUTPUT,
    index=False
)


print()
print(
    "Saved:",
    OUTPUT
)