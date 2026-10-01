def travel_time_seconds(
    distance_m: float,
    speed_kph: float
) -> float:
    """
    Calculate travel time in seconds.

    Formula:
        time = 3.6 * distance_m / speed_kph
    """

    if distance_m < 0:
        raise ValueError(
            "distance_m cannot be negative"
        )

    if speed_kph <= 0:
        raise ValueError(
            "speed_kph must be > 0"
        )

    return 3.6 * distance_m / speed_kph