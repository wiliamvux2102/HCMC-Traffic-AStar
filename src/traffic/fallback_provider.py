import pandas as pd

from .provider import TrafficProvider
from .snapshot import snapshot_from_dataframe


MIN_SPEED_KPH = 5.0


class FallbackTrafficProvider(
    TrafficProvider
):

    def __init__(
        self,
        edges_path: str
    ):
        self.edges = pd.read_csv(
            edges_path
        )

    def _get_time_period(
        self,
        timestamp: pd.Timestamp
    ) -> str:

        hour = timestamp.hour

        if 7 <= hour < 9:
            return "morning_peak"

        if 9 <= hour < 16:
            return "midday"

        if 16 <= hour < 19:
            return "evening_peak"

        if 19 <= hour < 23:
            return "evening"

        return "night"

    def _get_congestion_factor(
        self,
        highway: str,
        period: str
    ) -> float:

        # Đơn giản hóa version đầu tiên.
        # Sau này có thể thay bằng bảng chi tiết hơn.

        factors = {
            "morning_peak": 0.55,
            "midday": 0.80,
            "evening_peak": 0.50,
            "evening": 0.75,
            "night": 0.90,
        }

        return factors.get(
            period,
            0.80
        )

    def get_snapshot(
        self,
        timestamp: str
    ):

        ts = pd.Timestamp(timestamp)

        period = self._get_time_period(ts)

        df = self.edges[
            [
                "source",
                "target",
                "edge_key",
                "highway_normalized",
                "free_flow_speed_kph"
            ]
        ].copy()

        df["congestion_factor"] = (
            df["highway_normalized"]
            .apply(
                lambda highway:
                self._get_congestion_factor(
                    highway,
                    period
                )
            )
        )

        df["speed_kph"] = (
            df["free_flow_speed_kph"]
            * df["congestion_factor"]
        )

        # tránh speed quá nhỏ hoặc bằng 0
        df["speed_kph"] = (
            df["speed_kph"]
            .clip(lower=MIN_SPEED_KPH)
        )

        df["provenance"] = "fallback"

        print(df.head())

        return snapshot_from_dataframe(
            df,
            timestamp
        )