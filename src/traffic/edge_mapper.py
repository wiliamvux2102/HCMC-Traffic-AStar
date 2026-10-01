# src/traffic/edge_mapper.py


class TrafficEdgeMapper:

    def __init__(self, edges_path):
        self.edges_path = edges_path

    def build_mapping(self):
        raise NotImplementedError(
            "Implemented in realtime phase"
        )