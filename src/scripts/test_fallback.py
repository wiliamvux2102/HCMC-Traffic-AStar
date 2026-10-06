from src.traffic.fallback_provider import (
    FallbackTrafficProvider
)


provider = FallbackTrafficProvider(
    "data/processed/edges_enriched.csv"
)

snapshot = provider.get_snapshot(
    "2026-10-01T17:30:00+07:00"
)

print(
    "Edges in snapshot:",
    len(snapshot.edge_speed)
)

print(
    "V_bound:",
    snapshot.v_bound
)

key = next(
    iter(snapshot.edge_speed)
)

print(key)
print(snapshot.edge_speed[key])
print(snapshot.provenance[key])


import pandas as pd

from src.traffic.cost import (
    travel_time_seconds
)


edges = pd.read_csv(
    "data/processed/edges_enriched.csv"
)

row = edges.iloc[0]

u = int(row["source"])
v = int(row["target"])
k = int(row["edge_key"])

distance = float(
    row["distance_m"]
)

speed = snapshot.speed(
    u, v, k
)

cost = travel_time_seconds(
    distance,
    speed
)

print("Edge:", (u, v, k))
print("Distance:", distance)
print("Speed:", speed)
print("Cost:", cost, "seconds")