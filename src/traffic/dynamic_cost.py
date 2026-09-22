"""Dynamic travel cost calculations based on traffic conditions."""


def dynamic_cost(base_cost, traffic_level=1.0):
    """Apply a multiplier derived from traffic intensity."""
    return base_cost * max(traffic_level, 0.1)
