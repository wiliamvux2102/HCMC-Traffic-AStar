from datetime import datetime

from src.traffic.service import (
    TrafficService
)

from src.traffic.cost import (
    travel_time_seconds
)


EDGES = (
    "data/processed/"
    "edges_enriched.csv"
)


service = TrafficService(
    edges_path=EDGES,
    cache_ttl_minutes=10
)


timestamp = datetime.now()


snapshot = (
    service.get_snapshot(
        timestamp
    )
)


print()
print("=" * 70)
print("TRAFFIC SERVICE TEST")
print("=" * 70)

print(
    "Snapshot timestamp:",
    snapshot.timestamp
)

print(
    "Total edges:",
    snapshot.size
)

print(
    "V_bound:",
    snapshot.v_bound
)


live_count = sum(
    1
    for source
    in snapshot.provenance.values()
    if source == "live"
)

fallback_count = sum(
    1
    for source
    in snapshot.provenance.values()
    if source == "fallback"
)


print(
    "LIVE edges:",
    live_count
)

print(
    "FALLBACK edges:",
    fallback_count
)


edge = next(
    iter(
        snapshot.edge_speed
    )
)


speed = snapshot.speed(
    *edge
)


print()
print(
    "Example edge:",
    edge
)

print(
    "Speed:",
    speed
)

print(
    "Source:",
    snapshot.source(
        *edge
    )
)

print(
    "500m travel time:",
    travel_time_seconds(
        500,
        speed
    ),
    "seconds"
)