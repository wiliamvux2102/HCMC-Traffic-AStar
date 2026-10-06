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

    mode: str = ""

    def __post_init__(self):
        # Infer mode from provenance if not provided
        if not self.mode:
            provenance_values = list(self.provenance.values())
            if provenance_values:
                # Count each provenance type
                from collections import Counter
                counts = Counter(provenance_values)
                # Use majority provenance as mode
                majority = counts.most_common(1)[0][0]
                if majority == "live":
                    object.__setattr__(self, "mode", "LIVE")
                elif majority == "replay":
                    object.__setattr__(self, "mode", "REPLAY")
                else:
                    object.__setattr__(self, "mode", "FALLBACK")
            else:
                object.__setattr__(self, "mode", "FALLBACK")
        elif self.mode not in {"LIVE", "REPLAY", "FALLBACK"}:
            raise ValueError(f"Unknown snapshot mode: {self.mode}")

        # Validate speeds and create immutable copies
        speeds = dict(self.edge_speed)
        provenance = dict(self.provenance)
        for key, speed in speeds.items():
            if not isinstance(key, tuple) or len(key) != 3:
                raise ValueError(f"Invalid edge key: {key!r}")
            if not math.isfinite(speed) or speed <= 0:
                raise ValueError(f"Invalid speed for {key}: {speed}")
        object.__setattr__(self, "edge_speed", MappingProxyType(speeds))
        object.__setattr__(self, "provenance", MappingProxyType(provenance))

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