# src/traffic/models.py

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Dict, Tuple

from src.traffic.time_utils import normalize_timestamp


EdgeKey = Tuple[int, int, int]


@dataclass(frozen=True)
class TrafficSnapshot:
    timestamp: str

    edge_speed: Dict[
        EdgeKey,
        float
    ]

    provenance: Dict[
        EdgeKey,
        str
    ]

    def speed(
        self,
        u: int,
        v: int,
        k: int
    ) -> float:

        key = (
            int(u),
            int(v),
            int(k)
        )

        if key not in self.edge_speed:
            raise KeyError(
                f"No traffic speed for edge {key}"
            )

        return self.edge_speed[key]


    def source(
        self,
        u: int,
        v: int,
        k: int
    ) -> str:

        key = (
            int(u),
            int(v),
            int(k)
        )

        if key not in self.provenance:
            raise KeyError(
                f"No provenance for edge {key}"
            )

        return self.provenance[key]


    @property
    def v_bound(self) -> float:

        if not self.edge_speed:
            raise ValueError(
                "TrafficSnapshot is empty"
            )

        return max(
            self.edge_speed.values()
        )


    @property
    def size(self) -> int:

        return len(
            self.edge_speed
        )
