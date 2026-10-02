# src/traffic/speed_parser.py

import ast
import math
import re
from typing import Optional


MPH_TO_KPH = 1.60934


def _is_missing(value) -> bool:
    """
    Check whether a raw OSM maxspeed value is missing
    or unusable.
    """

    if value is None:
        return True

    if isinstance(value, float) and math.isnan(value):
        return True

    text = str(value).strip().lower()

    return text in {
        "",
        "nan",
        "none",
        "signals",
        "variable",
        "walk",
    }


def _parse_single_speed(value) -> Optional[float]:
    """
    Parse one speed value into km/h.

    Examples:
        "50"       -> 50.0
        "50 km/h"  -> 50.0
        "30 mph"   -> 48.28
    """

    if _is_missing(value):
        return None

    text = str(value).strip().lower()

    match = re.search(
        r"(\d+(?:\.\d+)?)",
        text
    )

    if not match:
        return None

    speed = float(match.group(1))

    if "mph" in text:
        speed *= MPH_TO_KPH

    return speed


def parse_maxspeed(value) -> Optional[float]:
    """
    Normalize OSM maxspeed_raw into km/h.

    OSM may store multiple speed values:
        "['50', '60']"

    Project rule:
        choose the maximum valid speed.

    Examples:
        "50"               -> 50.0
        "50 km/h"          -> 50.0
        "30 mph"           -> 48.28
        "['50', '60']"     -> 60.0
        None               -> None
    """

    if _is_missing(value):
        return None

    # Handle string representation of a Python list
    if isinstance(value, str):
        stripped = value.strip()

        if (
            stripped.startswith("[")
            and stripped.endswith("]")
        ):
            try:
                parsed = ast.literal_eval(stripped)

                if isinstance(parsed, list):
                    speeds = []

                    for item in parsed:
                        speed = _parse_single_speed(item)

                        if speed is not None:
                            speeds.append(speed)

                    if speeds:
                        return max(speeds)

                    return None

            except (ValueError, SyntaxError):
                pass

    return _parse_single_speed(value)