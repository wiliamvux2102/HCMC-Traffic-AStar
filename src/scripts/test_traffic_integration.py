from datetime import datetime

from src.traffic.replay_provider import (
    ReplayProvider
)

from src.traffic.cost import (
    travel_time_seconds
)


provider = ReplayProvider(
    "data/traffic/snapshots/"
    "2026-10-02/"
    "16-57-46-complete.csv"
)


timestamp = datetime(
    2026,
    10,
    2,
    16,
    57,
    46
)


snapshot = (
    provider.get_snapshot(
        timestamp
    )
)


print(
    "Edges:",
    snapshot.size
)

print(
    "V_bound:",
    snapshot.v_bound
)


edge = next(
    iter(
        snapshot.edge_speed
    )
)


speed = snapshot.speed(
    *edge
)


print(
    "Example edge:",
    edge
)

print(
    "Speed:",
    speed
)

print(
    "Provenance:",
    snapshot.source(
        *edge
    )
)


cost = travel_time_seconds(
    distance_m=500,
    speed_kph=speed
)


print(
    "Travel time for 500m:",
    cost,
    "seconds"
)