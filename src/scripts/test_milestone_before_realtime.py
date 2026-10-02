from src.traffic.baseline import enrich_edges
from src.traffic.fallback_provider import (
    FallbackTrafficProvider
)
from src.traffic.cost import (
    travel_time_seconds
)

import pandas as pd


# ==================================
# STEP 1: enrich Member 1 edges
# ==================================

edges = enrich_edges(
    "data/processed/edges.csv",
    "data/processed/edges_enriched.csv"
)


# ==================================
# STEP 2: generate traffic snapshot
# ==================================

provider = FallbackTrafficProvider(
    "data/processed/edges_enriched.csv"
)

snapshot = provider.get_snapshot(
    "2026-10-01T17:30:00+07:00"
)


# ==================================
# STEP 3: pick one edge
# ==================================

edge = edges.iloc[0]

u = int(edge["source"])
v = int(edge["target"])
k = int(edge["edge_key"])

distance = float(
    edge["distance_m"]
)


# ==================================
# STEP 4: dynamic speed
# ==================================

speed = snapshot.speed(
    u, v, k
)


# ==================================
# STEP 5: dynamic cost
# ==================================

cost = travel_time_seconds(
    distance,
    speed
)


print("Edge:", (u, v, k))
print(
    "Highway:",
    edge["highway_normalized"]
)
print(
    "Free-flow speed:",
    edge["free_flow_speed_kph"]
)
print(
    "Snapshot speed:",
    speed
)
print(
    "Travel time:",
    cost,
    "seconds"
)

print(
    "V_bound:",
    snapshot.v_bound
)

from src.traffic.speed_parser import parse_maxspeed


test_values = [
    "50",
    "50 km/h",
    "30 mph",
    "['50', '60']",
    "['80', '50', '60']",
    None,
    "signals",
]

for value in test_values:
    print(
        value,
        "->",
        parse_maxspeed(value)
    )