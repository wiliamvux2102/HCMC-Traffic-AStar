import pandas as pd

from .provider import TrafficProvider
from .snapshot import snapshot_from_dataframe
from .normalizer import normalize_speed
from .time_utils import normalize_timestamp, parse_timestamp


class ReplayTrafficProvider(
    TrafficProvider
):

    def __init__(
        self,
        snapshot_path: str
    ):
        self.snapshot_path = (
            snapshot_path
        )

    def get_snapshot(
        self,
        timestamp: str
    ):

        df = pd.read_csv(
            self.snapshot_path
        )

        if "timestamp" not in df.columns or df.empty:
            raise ValueError("Replay CSV must retain its original snapshot timestamp")
        timestamps = df["timestamp"].map(normalize_timestamp).unique()
        if len(timestamps) != 1:
            raise ValueError("Replay CSV must contain exactly one snapshot")
        actual_timestamp = timestamps[0]
        if parse_timestamp(actual_timestamp) > parse_timestamp(timestamp):
            raise ValueError("Replay snapshot is newer than the requested departure")
        # Report REPLAY instead of labeling previously recorded data as live.
        df["provenance"] = "replay"
        df["speed_kph"] = df["speed_kph"].map(normalize_speed)
        df = df.dropna(subset=["speed_kph"])

        return snapshot_from_dataframe(
            df,
            actual_timestamp
        )
