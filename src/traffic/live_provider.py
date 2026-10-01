# src/traffic/live_provider.py

from .provider import TrafficProvider


class LiveTrafficProvider(
    TrafficProvider
):

    def get_snapshot(
        self,
        timestamp: str
    ):
        raise NotImplementedError(
            "Live traffic source "
            "will be implemented later"
        )