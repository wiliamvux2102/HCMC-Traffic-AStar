"""Node definition for the graph."""


class Node:
    """Represents a node in the road network."""

    def __init__(self, node_id, lat=None, lon=None, **kwargs):
        self.id = node_id
        self.lat = lat
        self.lon = lon
        self.meta = kwargs
