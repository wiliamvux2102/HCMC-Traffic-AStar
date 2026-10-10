from datetime import datetime

from src.traffic.live_provider import LiveProvider


EDGES_PATH = "data/processed/edges_enriched.csv"


def main():
    provider = LiveProvider(
        edges_path=EDGES_PATH,
        cache_ttl_minutes=10,
    )

    timestamp = datetime.now()

    snapshot = provider.get_snapshot(
        timestamp
    )

    print()
    print("=" * 70)
    print("LIVE SNAPSHOT TEST")
    print("=" * 70)

    print(
        "Timestamp:",
        snapshot.timestamp
    )

    print(
        "Mode:",
        snapshot.mode
    )

    print(
        "Total edges:",
        snapshot.size
    )

    print(
        "V_bound:",
        snapshot.v_bound
    )

    counts = {}

    for source in snapshot.provenance.values():
        counts[source] = (
            counts.get(source, 0)
            + 1
        )

    print(
        "Provenance:",
        counts
    )

    live_edges = counts.get(
        "live",
        0
    )

    fallback_edges = counts.get(
        "fallback",
        0
    )

    total = snapshot.size

    live_ratio = (
        live_edges
        / total
        * 100
    )

    print(
        "Live edges:",
        live_edges
    )

    print(
        "Fallback edges:",
        fallback_edges
    )

    print(
        "Live coverage:",
        f"{live_ratio:.2f}%"
    )

    assert total == 546742

    assert (
        live_edges
        +
        fallback_edges
        ==
        total
    )

    assert all(
        speed > 0
        for speed
        in snapshot.edge_speed.values()
    )

    print()
    print(
        "LIVE snapshot OK."
    )


if __name__ == "__main__":
    main()