# src/traffic/replay_provider.py

from datetime import datetime
from pathlib import Path
import re

from src.traffic.provider import TrafficProvider
from src.traffic.snapshot import load_snapshot_csv
from src.traffic.models import TrafficSnapshot


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

    def _parse_timestamp_from_filename(self, path: Path) -> str:
        """
        Extract timestamp from snapshot filename.
        Expected format: YYYY-MM-DD/HH-MM-SS-complete.csv (or with backslashes on Windows)
        Returns ISO format string with HCMC timezone.
        """
        # Try to parse from path: data/traffic/snapshots/YYYY-MM-DD/HH-MM-SS-complete.csv
        # Handle both forward slashes and backslashes
        path_str = str(path).replace('\\', '/')
        match = re.search(r'(\d{4}-\d{2}-\d{2})/(\d{2}-\d{2}-\d{2})-complete\.csv', path_str)
        if match:
            date_str, time_str = match.groups()
            # Convert HH-MM-SS to HH:MM:SS
            time_str = time_str.replace('-', ':')
            # Assume HCMC timezone (UTC+7)
            return f"{date_str}T{time_str}+07:00"

        # Fallback: use file modification time
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return mtime.isoformat()


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

        # Parse the actual capture timestamp from the filename
        snapshot_timestamp = self._parse_timestamp_from_filename(path)

        # Load snapshot with the actual capture timestamp (not current time)
        snapshot = load_snapshot_csv(
            str(path),
            snapshot_timestamp
        )

        # Override mode to REPLAY since this is explicitly a replay provider
        # Keep the original snapshot timestamp (when data was actually captured)
        return TrafficSnapshot(
            timestamp=snapshot.timestamp,
            edge_speed=snapshot.edge_speed,
            provenance=snapshot.provenance,
            mode="REPLAY"
        )
