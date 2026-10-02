from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Dict, Tuple

from src.traffic.time_utils import normalize_timestamp


# Một road edge trong OSMnx MultiDiGraph
# được định danh bởi (source, target, edge_key)
EdgeKey = Tuple[int, int, int]


@dataclass(frozen=True)
class TrafficSnapshot:
    """
    Trạng thái giao thông của toàn bộ road graph
    tại một thời điểm cố định.
    """

    timestamp: str

    # (u, v, k) -> speed_kph
    edge_speed: Dict[EdgeKey, float]

    # (u, v, k) -> live / replay / fallback
    provenance: Dict[EdgeKey, str]

    mode: str = ""

    def __post_init__(self):
        speeds = dict(self.edge_speed)
        provenance = dict(self.provenance)
        if not speeds:
            raise ValueError("TrafficSnapshot contains no edge speeds")
        for key, speed in speeds.items():
            if (not isinstance(key, tuple) or len(key) != 3
                    or any(not isinstance(part, int) for part in key)):
                raise ValueError(f"Invalid edge key: {key!r}")
            value = float(speed)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid speed for {key}: {speed}")
            speeds[key] = value
            if provenance.get(key) not in {"live", "replay", "fallback"}:
                raise ValueError(f"Missing or invalid provenance for {key}")
        if set(provenance) != set(speeds):
            raise ValueError("Provenance keys must match speed keys")
        mode = self.mode.upper() or ("LIVE" if "live" in provenance.values()
                                    else "REPLAY" if "replay" in provenance.values() else "FALLBACK")
        if mode not in {"LIVE", "REPLAY", "FALLBACK"}:
            raise ValueError(f"Unknown snapshot mode: {mode}")
        object.__setattr__(self, "timestamp", normalize_timestamp(self.timestamp))
        object.__setattr__(self, "edge_speed", MappingProxyType(speeds))
        object.__setattr__(self, "provenance", MappingProxyType(provenance))
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "_v_bound", max(speeds.values()))

    def speed(self, u: int, v: int, k: int) -> float:
        """
        Lấy speed của một edge.
        """
        key = (u, v, k)

        if key not in self.edge_speed:
            raise KeyError(f"Missing traffic speed for edge {key}")

        return self.edge_speed[key]

    @property
    def v_bound(self) -> float:
        """
        V_bound dùng trong heuristic A*.

        Theo technical document hiện tại:
            V_bound = max speed trong snapshot.
        """

        if not self.edge_speed:
            raise ValueError("TrafficSnapshot contains no edge speeds")

        return self._v_bound
