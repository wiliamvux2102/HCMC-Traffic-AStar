from datetime import datetime

from src.traffic.fallback_provider import FallbackProvider


EDGES_PATH = "data/processed/edges_enriched.csv"


def main():
    provider = FallbackProvider(
        edges_path=EDGES_PATH
    )

    timestamp = datetime.now()

    snapshot = provider.get_snapshot(
        timestamp
    )

    print("=" * 60)
    print("FALLBACK SNAPSHOT TEST")
    print("=" * 60)

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

    # provenance statistics
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

    # basic checks
    assert snapshot.size == 546742

    assert all(
        speed > 0
        for speed
        in snapshot.edge_speed.values()
    )

    print()
    print("Fallback snapshot OK.")


if __name__ == "__main__":
    main()