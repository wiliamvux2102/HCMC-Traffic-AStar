from dataclasses import dataclass
from typing import Dict, Tuple


# Một road edge trong OSMnx MultiDiGraph
# được định danh bởi (source, target, edge_key)
EdgeKey = Tuple[int, int, int]


@dataclass
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

        return max(self.edge_speed.values())