from datetime import datetime
from pathlib import Path
import re

import pandas as pd

from src.traffic.provider import TrafficProvider
from src.traffic.snapshot import load_snapshot_csv
from src.traffic.models import TrafficSnapshot


EDGE_KEY_COLUMNS = [
    "source",
    "target",
    "edge_key",
]


class ReplayProvider(TrafficProvider):

    def __init__(
        self,
        edges_path: str,
        snapshot_root: str = "data/traffic/snapshots",
    ):
        self.snapshot_root = Path(
            snapshot_root
        )

        expected = pd.read_csv(
            edges_path,
            usecols=EDGE_KEY_COLUMNS,
        )

        if expected.duplicated(
            EDGE_KEY_COLUMNS
        ).any():
            raise ValueError(
                "Current edges file contains "
                "duplicated edge keys"
            )

        self.expected_count = len(
            expected
        )

        self.expected_keys = set(
            zip(
                expected["source"].astype(int),
                expected["target"].astype(int),
                expected["edge_key"].astype(int),
            )
        )

    def _snapshot_is_compatible(
        self,
        path: Path,
    ) -> bool:

        try:
            keys = pd.read_csv(
                path,
                usecols=EDGE_KEY_COLUMNS,
            )

        except Exception:
            return False

        if len(keys) != self.expected_count:
            return False

        if keys.duplicated(
            EDGE_KEY_COLUMNS
        ).any():
            return False

        actual_keys = set(
            zip(
                keys["source"].astype(int),
                keys["target"].astype(int),
                keys["edge_key"].astype(int),
            )
        )

        return (
            actual_keys
            ==
            self.expected_keys
        )

    def _find_latest_snapshot(
        self,
    ) -> Path:

        files = sorted(
            self.snapshot_root.glob(
                "**/*-complete.csv"
            ),
            key=lambda p:
                p.stat().st_mtime,
            reverse=True,
        )

        if not files:
            raise FileNotFoundError(
                "No replay snapshots available"
            )

        for path in files:

            if self._snapshot_is_compatible(
                path
            ):
                return path

            print(
                "Skipping incompatible "
                "replay snapshot:",
                path,
            )

        raise FileNotFoundError(
            "No replay snapshot matches "
            "the current graph"
        )

    def _parse_timestamp_from_filename(
        self,
        path: Path,
    ) -> str:

        path_str = str(
            path
        ).replace(
            "\\",
            "/",
        )

        match = re.search(
            r"(\d{4}-\d{2}-\d{2})/"
            r"(\d{2}-\d{2}-\d{2})"
            r"-complete\.csv",
            path_str,
        )

        if match:
            date_str, time_str = (
                match.groups()
            )

            time_str = (
                time_str.replace(
                    "-",
                    ":",
                )
            )

            return (
                f"{date_str}"
                f"T{time_str}"
                f"+07:00"
            )

        mtime = datetime.fromtimestamp(
            path.stat().st_mtime
        )

        return mtime.isoformat()

    def get_snapshot(
        self,
        timestamp: datetime,
    ) -> TrafficSnapshot:

        path = (
            self._find_latest_snapshot()
        )

        print(
            "Using replay snapshot:",
            path,
        )

        snapshot_timestamp = (
            self._parse_timestamp_from_filename(
                path
            )
        )

        snapshot = load_snapshot_csv(
            str(path),
            snapshot_timestamp,
        )

        return TrafficSnapshot(
            timestamp=snapshot.timestamp,
            edge_speed=snapshot.edge_speed,
            provenance=snapshot.provenance,
            mode="REPLAY",
        )