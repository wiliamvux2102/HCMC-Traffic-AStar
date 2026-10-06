# testAPI.py

import os
import json
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv


# =========================================================
# 1. Load API key
# =========================================================

load_dotenv()

API_KEY = os.getenv("HERE_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "HERE_API_KEY not found in .env"
    )


# =========================================================
# 2. HERE Traffic API configuration
# =========================================================

URL = "https://data.traffic.hereapi.com/v7/flow"

# Small bbox around HCMC/HCMUT area for testing
BBOX = "106.64,10.76,106.67,10.79"

params = {
    "in": f"bbox:{BBOX}",
    "locationReferencing": "shape",
    "apiKey": API_KEY,
}


# =========================================================
# 3. Helper: save raw snapshot
# =========================================================

def save_raw_response(data):
    """
    Save the complete HERE API response locally.

    This allows us to develop normalizer/mapper offline
    without calling the API repeatedly.
    """

    now = datetime.now()

    folder = (
        Path("data")
        / "traffic"
        / "raw"
        / now.strftime("%Y-%m-%d")
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = (
        folder
        / f"{now:%H-%M-%S}-here.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    return file_path


# =========================================================
# 4. Helper: inspect one traffic segment
# =========================================================

def inspect_segment(segment, index):
    """
    Print important information from one HERE traffic segment.
    """

    print()
    print("=" * 70)
    print(f"SEGMENT #{index}")
    print("=" * 70)

    # Print all top-level keys
    print("Top-level keys:")
    print(list(segment.keys()))

    location = segment.get(
        "location",
        {}
    )

    current_flow = segment.get(
        "currentFlow",
        {}
    )

    print()
    print("Location keys:")
    print(list(location.keys()))

    print()
    print("CurrentFlow keys:")
    print(list(current_flow.keys()))

    print()

    # -----------------------------------------------------
    # Traffic values
    # -----------------------------------------------------

    speed_mps = current_flow.get(
        "speed"
    )

    free_flow_mps = current_flow.get(
        "freeFlow"
    )

    jam_factor = current_flow.get(
        "jamFactor"
    )

    speed_kph = (
        speed_mps * 3.6
        if speed_mps is not None
        else None
    )

    free_flow_kph = (
        free_flow_mps * 3.6
        if free_flow_mps is not None
        else None
    )

    print("Traffic values:")

    print(
        f"  speed raw (m/s): "
        f"{speed_mps}"
    )

    print(
        f"  speed converted (km/h): "
        f"{speed_kph}"
    )

    print(
        f"  freeFlow raw (m/s): "
        f"{free_flow_mps}"
    )

    print(
        f"  freeFlow converted (km/h): "
        f"{free_flow_kph}"
    )

    print(
        f"  jamFactor: "
        f"{jam_factor}"
    )

    # -----------------------------------------------------
    # Location / geometry
    # -----------------------------------------------------

    print()
    print("Location information:")

    print(
        "  description:",
        location.get("description")
    )

    print(
        "  length:",
        location.get("length")
    )

    print(
        "  shape exists:",
        "shape" in location
    )

    if "shape" in location:
        print()
        print("Shape:")
        print(
            json.dumps(
                location["shape"],
                indent=2,
                ensure_ascii=False
            )
        )

    # -----------------------------------------------------
    # Full segment JSON
    # -----------------------------------------------------

    print()
    print("Full segment JSON:")

    print(
        json.dumps(
            segment,
            indent=2,
            ensure_ascii=False
        )
    )


# =========================================================
# 5. Main API test
# =========================================================

def main():

    print("=" * 70)
    print("HERE TRAFFIC API TEST")
    print("=" * 70)

    print()
    print("Request bbox:")
    print(BBOX)

    print()
    print("Calling HERE Traffic API once...")

    try:
        response = requests.get(
            URL,
            params=params,
            timeout=30
        )

    except requests.RequestException as e:
        print(
            "Request failed:",
            e
        )
        return

    print()
    print(
        "HTTP status:",
        response.status_code
    )

    # -----------------------------------------------------
    # Stop immediately if request fails
    # -----------------------------------------------------

    if response.status_code != 200:

        print()
        print("HERE API error response:")

        print(
            response.text[:3000]
        )

        return

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:
        data = response.json()

    except ValueError:

        print(
            "Response is not valid JSON"
        )

        print(
            response.text[:3000]
        )

        return

    # -----------------------------------------------------
    # Basic response information
    # -----------------------------------------------------

    results = data.get(
        "results",
        []
    )

    print()
    print(
        "sourceUpdated:",
        data.get("sourceUpdated")
    )

    print(
        "Number of traffic segments:",
        len(results)
    )

    print()
    print(
        "Top-level response keys:"
    )

    print(
        list(data.keys())
    )

    # -----------------------------------------------------
    # Save snapshot immediately
    # -----------------------------------------------------

    file_path = save_raw_response(
        data
    )

    print()
    print(
        "Raw snapshot saved to:"
    )

    print(file_path)

    # -----------------------------------------------------
    # Stop if no traffic data
    # -----------------------------------------------------

    if not results:

        print()
        print(
            "No traffic flow segments "
            "returned for this bbox."
        )

        return

    # -----------------------------------------------------
    # Inspect first few segments
    # -----------------------------------------------------

    number_to_inspect = min(
        3,
        len(results)
    )

    print()
    print(
        f"Inspecting first "
        f"{number_to_inspect} segments..."
    )

    for i in range(
        number_to_inspect
    ):
        inspect_segment(
            results[i],
            i
        )

    # -----------------------------------------------------
    # Quick statistics
    # -----------------------------------------------------

    speeds = []
    free_flows = []
    jam_factors = []

    segments_with_shape = 0
    segments_without_speed = 0

    for segment in results:

        flow = segment.get(
            "currentFlow",
            {}
        )

        location = segment.get(
            "location",
            {}
        )

        speed = flow.get(
            "speed"
        )

        free_flow = flow.get(
            "freeFlow"
        )

        jam_factor = flow.get(
            "jamFactor"
        )

        if speed is not None:
            speeds.append(
                speed * 3.6
            )
        else:
            segments_without_speed += 1

        if free_flow is not None:
            free_flows.append(
                free_flow * 3.6
            )

        if jam_factor is not None:
            jam_factors.append(
                jam_factor
            )

        if "shape" in location:
            segments_with_shape += 1

    print()
    print("=" * 70)
    print("QUICK SUMMARY")
    print("=" * 70)

    print(
        "Total segments:",
        len(results)
    )

    print(
        "Segments with shape:",
        segments_with_shape
    )

    print(
        "Segments without speed:",
        segments_without_speed
    )

    if speeds:
        print()
        print(
            "Speed km/h:"
        )

        print(
            "  min:",
            min(speeds)
        )

        print(
            "  max:",
            max(speeds)
        )

        print(
            "  avg:",
            sum(speeds)
            / len(speeds)
        )

    if free_flows:
        print()
        print(
            "Free-flow speed km/h:"
        )

        print(
            "  min:",
            min(free_flows)
        )

        print(
            "  max:",
            max(free_flows)
        )

        print(
            "  avg:",
            sum(free_flows)
            / len(free_flows)
        )

    if jam_factors:
        print()
        print(
            "Jam factor:"
        )

        print(
            "  min:",
            min(jam_factors)
        )

        print(
            "  max:",
            max(jam_factors)
        )

        print(
            "  avg:",
            sum(jam_factors)
            / len(jam_factors)
        )

    print()
    print(
        "Test finished successfully."
    )

    print(
        "Do not call the API again "
        "for normalizer development."
    )

    print(
        "Use the saved JSON snapshot "
        "for the next steps."
    )


if __name__ == "__main__":
    main()