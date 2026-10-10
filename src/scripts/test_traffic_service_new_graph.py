from datetime import datetime

from src.traffic.service import TrafficService


EDGES_PATH = "data/processed/edges_enriched.csv"


def summarize(snapshot):
    counts = {}

    for source in snapshot.provenance.values():
        counts[source] = (
            counts.get(source, 0)
            + 1
        )

    print(
        "Mode:",
        snapshot.mode
    )

    print(
        "Timestamp:",
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

    print(
        "Provenance:",
        counts
    )


def main():
    service = TrafficService(
        edges_path=EDGES_PATH,
        cache_ttl_minutes=10
    )

    print(
        "=" * 70
    )
    print(
        "TRAFFIC SERVICE TEST"
    )
    print(
        "=" * 70
    )

    snapshot = service.get_snapshot(
        datetime.now()
    )

    summarize(
        snapshot
    )

    assert (
        snapshot.size
        ==
        546742
    )

    assert all(
        speed > 0
        for speed
        in snapshot.edge_speed.values()
    )

    print()
    print(
        "TrafficService snapshot OK."
    )


if __name__ == "__main__":
    main()