"""Section 8: Haversine distance / maximum normalized snapshot speed."""

import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """Return distance in meters for geographic coordinates in degrees."""
    coords = (lat1, lon1, lat2, lon2)
    if any(value is None or not math.isfinite(value) for value in coords):
        raise ValueError("Coordinates must be finite")
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90
            and -180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise ValueError("Coordinates are outside latitude/longitude bounds")
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = phi2 - phi1, math.radians(lon2 - lon1)
    term = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * 6371000.0 * math.asin(math.sqrt(max(0.0, min(1.0, term))))


def travel_time_heuristic(node, goal, v_bound):
    """h = 3.6 * great-circle meters / V_bound(km/h), in seconds."""
    if not math.isfinite(v_bound) or v_bound <= 0:
        raise ValueError("V_bound must be finite and positive")
    return 3.6 * haversine_distance(node.lat, node.lon, goal.lat, goal.lon) / v_bound
