# src/traffic/replay_provider.py

from datetime import datetime
from pathlib import Path

from src.traffic.provider import TrafficProvider
from src.traffic.snapshot import load_snapshot_csv


class ReplayProvider(TrafficProvider):

    def __init__(
        self,
        snapshot_root: str
        = "data/traffic/snapshots"
    ):
        self.snapshot_root = Path(
            snapshot_root
        )


    def _find_latest_snapshot(
        self
    ) -> Path:

        files = list(
            self.snapshot_root.glob(
                "**/*-complete.csv"
            )
        )

        if not files:
            raise FileNotFoundError(
                "No replay snapshots available"
            )

        return max(
            files,
            key=lambda p:
                p.stat().st_mtime
        )


    def get_snapshot(
        self,
        timestamp: datetime
    ):

        path = (
            self._find_latest_snapshot()
        )

        print(
            "Using replay snapshot:",
            path
        )

        return load_snapshot_csv(
            str(path),
            timestamp.isoformat()
        )
