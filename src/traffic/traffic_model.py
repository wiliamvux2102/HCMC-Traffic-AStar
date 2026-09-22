"""Traffic model definitions."""


class TrafficModel:
    """Base traffic model container."""

    def __init__(self):
        self.traffic_data = {}

    def update(self, data):
        self.traffic_data.update(data)
