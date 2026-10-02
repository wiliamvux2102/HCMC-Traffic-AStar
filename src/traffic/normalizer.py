import pandas as pd
import math


MIN_SPEED_KPH = 5.0
MAX_SPEED_KPH = 100.0


def normalize_speed(
    speed
) -> float | None:

    if speed is None:
        return None

    try:
        speed = float(speed)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(speed):
        return None

    if speed <= 0:
        return None

    return max(
        MIN_SPEED_KPH,
        min(
            speed,
            MAX_SPEED_KPH
        )
    )


def classify_traffic(
    speed_kph: float,
    free_flow_speed_kph: float
) -> str:

    ratio = (
        speed_kph
        / free_flow_speed_kph
    )

    if ratio >= 0.8:
        return "LOW"

    if ratio >= 0.6:
        return "MEDIUM"

    if ratio >= 0.4:
        return "HIGH"

    return "VERY_HIGH"
