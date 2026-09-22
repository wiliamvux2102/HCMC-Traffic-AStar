"""Heuristic functions for routing."""


def euclidean_heuristic(a, b):
    """Return the straight-line distance between two points."""
    if a is None or b is None:
        return 0
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
