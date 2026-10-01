from abc import ABC, abstractmethod

from .models import TrafficSnapshot


class TrafficProvider(ABC):

    """
        FallbackProvider
        ReplayProvider
        LiveProvider
    """

    @abstractmethod
    def get_snapshot(
        self,
        timestamp: str
    ) -> TrafficSnapshot:
        pass