"""Contracts from appendix A of the team's technical document."""

from dataclasses import asdict, dataclass, field
from typing import List, Tuple, Dict


@dataclass
class RouteResult:
    path_edges: List[Tuple[int, int, int]]
    total_time_s: float
    total_distance_m: float
    expanded_nodes: int
    runtime_ms: float
    snapshot_timestamp: str
    traffic_mode: str
    path_nodes: List[int] = field(default_factory=list)
    found: bool = True
    provenance_counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
