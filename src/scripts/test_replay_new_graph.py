from datetime import datetime

from src.traffic.replay_provider import ReplayProvider


EDGES_PATH = "data/processed/edges_enriched.csv"


def main():
    provider = ReplayProvider(
        edges_path=EDGES_PATH
    )

    snapshot = provider.get_snapshot(
        datetime.now()
    )

    print("=" * 70)
    print("REPLAY SNAPSHOT TEST")
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

    assert snapshot.mode == "REPLAY"
    assert snapshot.size == 546742

    assert (
        counts.get("live", 0)
        +
        counts.get("fallback", 0)
        ==
        546742
    )

    print()
    print(
        "REPLAY snapshot OK."
    )


if __name__ == "__main__":
    main()