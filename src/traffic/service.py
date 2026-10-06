# src/traffic/service.py

from datetime import datetime

from src.traffic.live_provider import (
    LiveProvider
)

from src.traffic.replay_provider import (
    ReplayProvider
)

from src.traffic.fallback_provider import (
    FallbackProvider
)

from src.traffic.models import (
    TrafficSnapshot
)


class TrafficService:

    def __init__(
        self,
        edges_path: str,
        cache_ttl_minutes: int = 10
    ):

        self.live = LiveProvider(
            edges_path=edges_path,
            cache_ttl_minutes=
                cache_ttl_minutes
        )

        self.replay = ReplayProvider()

        self.fallback = FallbackProvider(
            edges_path=edges_path
        )


    def get_snapshot(
        self,
        timestamp: datetime
    ) -> TrafficSnapshot:

        # =============================================
        # Priority 1: LIVE
        # =============================================

        try:

            return (
                self.live
                .get_snapshot(
                    timestamp
                )
            )

        except Exception as exc:

            print(
                "LIVE traffic failed:",
                exc
            )

        # =============================================
        # Priority 2: REPLAY
        # =============================================

        try:

            return (
                self.replay
                .get_snapshot(
                    timestamp
                )
            )

        except Exception as exc:

            print(
                "REPLAY traffic failed:",
                exc
            )

        # =============================================
        # Priority 3: FALLBACK
        # =============================================

        print(
            "Using FALLBACK traffic model"
        )

        return (
            self.fallback
            .get_snapshot(
                timestamp
            )
        )