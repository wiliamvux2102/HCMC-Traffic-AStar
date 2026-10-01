import math
import re
import ast


MPH_TO_KPH = 1.60934


def _is_missing(value) -> bool:
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
        "walk",
        "variable"
    }


def _parse_single_speed(value) -> float | None:
    """
    Parse một giá trị speed đơn.

    Examples:
        "50"       -> 50.0
        "50 km/h"  -> 50.0
        "30 mph"   -> 48.28
    """

    if _is_missing(value):
        return None

    text = str(value).strip().lower()

    match = re.search(r"(\d+(?:\.\d+)?)", text)

    if not match:
        return None

    speed = float(match.group(1))

    if "mph" in text:
        speed *= MPH_TO_KPH

    return speed


def parse_maxspeed(value) -> float | None:
    """
    Chuẩn hóa maxspeed_raw thành km/h.

    Nếu OSM chứa nhiều speed:
        ['40', '50']

    ta chọn max.

    Đây là engineering choice của project.
    """

    if _is_missing(value):
        return None

    # Nếu pandas đọc list thành string:
    # "['40', '50']"
    if isinstance(value, str):
        stripped = value.strip()

        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(stripped)

                if isinstance(parsed, list):
                    speeds = [
                        _parse_single_speed(x)
                        for x in parsed
                    ]

                    speeds = [
                        s for s in speeds
                        if s is not None
                    ]

                    return max(speeds) if speeds else None

            except (ValueError, SyntaxError):
                pass

    return _parse_single_speed(value)