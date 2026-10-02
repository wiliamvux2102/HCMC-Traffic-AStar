# src/traffic/cost.py


def travel_time_seconds(
    distance_m: float,
    speed_kph: float
) -> float:

    if distance_m < 0:
        raise ValueError(
            "distance_m must be >= 0"
        )

    if speed_kph <= 0:
        raise ValueError(
            "speed_kph must be > 0"
        )

    return (
        3.6
        * distance_m
        / speed_kph
    )