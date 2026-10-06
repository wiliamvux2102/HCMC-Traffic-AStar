"""Graph representation for the road network."""


class Graph:
    """Simple graph container for road network data."""

    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.edge_index = {}
        self.pois = {}
        self.poi_to_node = {}

    def add_node(self, node_id, node):
        self.nodes[node_id] = node

    def add_edge(self, source, target, weight=1.0, **meta):
        key = (source, target, int(meta.get("edge_key", 0)))
        if key in self.edge_index:
            raise ValueError(f"Duplicate directed edge: {key}")
        meta["edge_key"] = key[2]
        meta.setdefault("distance_m", weight)
        if source not in self.edges:
            self.edges[source] = []
        edge = {
            "target": target,
            "weight": weight,
            "meta": meta,
        }
        self.edges[source].append(edge)
        self.edge_index[key] = edge

    def add_poi(self, poi_id, poi, nearest_node):
        if nearest_node not in self.nodes:
            raise ValueError(f"POI {poi_id} references unknown road node {nearest_node}")
        if poi_id in self.pois:
            raise ValueError(f"Duplicate POI ID: {poi_id}")
        self.pois[poi_id] = poi
        self.poi_to_node[poi_id] = nearest_node
