import os
import json
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("HERE_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "HERE_API_KEY not found"
    )


URL = "https://data.traffic.hereapi.com/v7/flow"


# =========================================================
# TEST REGIONS
# =========================================================

REGIONS = {
    # Old test bbox
    "small": (
        106.64,
        10.76,
        106.67,
        10.79,
    ),

    # Larger central HCMC area
    "medium": (
        106.60,
        10.72,
        106.75,
        10.85,
    ),
}


def bbox_to_string(bbox):
    west, south, east, north = bbox

    return (
        f"{west},"
        f"{south},"
        f"{east},"
        f"{north}"
    )


def fetch_region(
    region_name,
    bbox
):
    params = {
        "in": (
            "bbox:"
            + bbox_to_string(bbox)
        ),

        "locationReferencing":
            "shape",

        "apiKey":
            API_KEY,
    }

    print()
    print("=" * 70)
    print(
        f"Fetching region: "
        f"{region_name}"
    )
    print("=" * 70)

    print(
        "BBox:",
        bbox_to_string(bbox)
    )

    response = requests.get(
        URL,
        params=params,
        timeout=60
    )

    print(
        "HTTP status:",
        response.status_code
    )

    if response.status_code != 200:
        print(
            response.text[:3000]
        )

        return None

    data = response.json()

    results = data.get(
        "results",
        []
    )

    print(
        "sourceUpdated:",
        data.get("sourceUpdated")
    )

    print(
        "traffic segments:",
        len(results)
    )

    return data


def save_response(
    data,
    region_name
):
    now = datetime.now()

    folder = (
        Path("data")
        / "traffic"
        / "coverage_tests"
        / now.strftime("%Y-%m-%d")
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        folder
        / (
            f"{now:%H-%M-%S}"
            f"-{region_name}.json"
        )
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        "Saved:",
        path
    )


def main():

    # IMPORTANT:
    # Test only ONE region per run
    # to avoid unnecessary requests.

    region_name = "medium"

    bbox = REGIONS[
        region_name
    ]

    data = fetch_region(
        region_name,
        bbox
    )

    if data is None:
        return

    save_response(
        data,
        region_name
    )


if __name__ == "__main__":
    main()