"""Use the shared traffic cost function; never mix meters and seconds."""

from src.traffic.cost import travel_time_seconds


def edge_cost(graph, snapshot, key):
    return travel_time_seconds(graph.edge_index[key]["meta"]["distance_m"],
                               snapshot.speed(*key))
