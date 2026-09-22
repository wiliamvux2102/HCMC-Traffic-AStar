"""Graph representation for the road network."""


class Graph:
    """Simple graph container for road network data."""

    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id, node):
        self.nodes[node_id] = node

    def add_edge(self, source, target, weight=1.0, **meta):
        if source not in self.edges:
            self.edges[source] = []
        self.edges[source].append({
            "target": target,
            "weight": weight,
            "meta": meta,
        })
