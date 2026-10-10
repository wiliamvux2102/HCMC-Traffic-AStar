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

    print("Mode:", snapshot.mode)
    print("Timestamp:", snapshot.timestamp)
    print("Total edges:", snapshot.size)
    print("V_bound:", snapshot.v_bound)
    print("Provenance:", counts)


def raise_live_failure(timestamp):
    raise RuntimeError(
        "Simulated LIVE failure"
    )


def raise_replay_failure(timestamp):
    raise RuntimeError(
        "Simulated REPLAY failure"
    )


def main():

    # ==================================================
    # CASE 1:
    # LIVE fails -> REPLAY must be used
    # ==================================================

    print()
    print("=" * 70)
    print("CASE 1: LIVE FAIL -> REPLAY")
    print("=" * 70)

    service = TrafficService(
        edges_path=EDGES_PATH,
        cache_ttl_minutes=10
    )

    # Do NOT call HERE.
    service.live.get_snapshot = (
        raise_live_failure
    )

    snapshot = service.get_snapshot(
        datetime.now()
    )

    summarize(snapshot)

    assert snapshot.mode == "REPLAY"
    assert snapshot.size == 546742

    print()
    print(
        "CASE 1 PASSED:"
        " LIVE -> REPLAY"
    )


    # ==================================================
    # CASE 2:
    # LIVE fails + REPLAY fails
    # -> FALLBACK must be used
    # ==================================================

    print()
    print("=" * 70)
    print(
        "CASE 2: LIVE FAIL + REPLAY FAIL"
        " -> FALLBACK"
    )
    print("=" * 70)

    service = TrafficService(
        edges_path=EDGES_PATH,
        cache_ttl_minutes=10
    )

    service.live.get_snapshot = (
        raise_live_failure
    )

    service.replay.get_snapshot = (
        raise_replay_failure
    )

    snapshot = service.get_snapshot(
        datetime.now()
    )

    summarize(snapshot)

    assert snapshot.mode == "FALLBACK"
    assert snapshot.size == 546742

    assert all(
        speed > 0
        for speed
        in snapshot.edge_speed.values()
    )

    print()
    print(
        "CASE 2 PASSED:"
        " LIVE -> REPLAY -> FALLBACK"
    )


    print()
    print("=" * 70)
    print("ALL FAILOVER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()