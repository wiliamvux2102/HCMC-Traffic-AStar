# src/traffic/provider.py

from abc import (
    ABC,
    abstractmethod
)

from datetime import datetime

from src.traffic.models import (
    TrafficSnapshot
)


class TrafficProvider(ABC):

    @abstractmethod
    def get_snapshot(
        self,
        timestamp: datetime
    ) -> TrafficSnapshot:

        pass