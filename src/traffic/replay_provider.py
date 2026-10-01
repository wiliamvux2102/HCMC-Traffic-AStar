import pandas as pd

from .provider import TrafficProvider
from .snapshot import snapshot_from_dataframe


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

        if "provenance" not in df.columns:
            df["provenance"] = "replay"

        return snapshot_from_dataframe(
            df,
            timestamp
        )