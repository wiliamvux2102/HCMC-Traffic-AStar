# src/traffic/grid_fetcher.py

import json
import os
import time

from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


# =========================================================
# HERE configuration
# =========================================================

HERE_FLOW_URL = (
    "https://data.traffic.hereapi.com/v7/flow"
)


# =========================================================
# Safety configuration
# =========================================================

GRID_ROWS = 4
GRID_COLS = 4

# Maximum number of API calls allowed by ONE execution
MAX_REQUESTS_PER_RUN = 16

# Small delay so we do not fire all requests simultaneously
REQUEST_DELAY_SECONDS = 0.5

REQUEST_TIMEOUT_SECONDS = 60


# =========================================================
# Graph bounds
# =========================================================

GRAPH_WEST = 106.563583
GRAPH_SOUTH = 10.6420077

GRAPH_EAST = 106.8382111
GRAPH_NORTH = 10.9117895


# =========================================================
# API key
# =========================================================

load_dotenv()

HERE_API_KEY = os.getenv(
    "HERE_API_KEY"
)

if not HERE_API_KEY:
    raise RuntimeError(
        "HERE_API_KEY not found in .env"
    )


# =========================================================
# Generate grid
# =========================================================

def generate_grid(
    west=GRAPH_WEST,
    south=GRAPH_SOUTH,
    east=GRAPH_EAST,
    north=GRAPH_NORTH,
    rows=GRID_ROWS,
    cols=GRID_COLS
):
    """
    Split the graph bounding box into a regular grid.

    Returns:
        [
            {
                "row": 0,
                "col": 0,
                "cell_id": "cell_0_0",
                "bbox": (...)
            },
            ...
        ]
    """

    lon_step = (
        east - west
    ) / cols

    lat_step = (
        north - south
    ) / rows

    cells = []

    for row in range(rows):

        for col in range(cols):

            cell_west = (
                west
                + col * lon_step
            )

            cell_east = (
                west
                + (col + 1)
                * lon_step
            )

            cell_south = (
                south
                + row * lat_step
            )

            cell_north = (
                south
                + (row + 1)
                * lat_step
            )

            cells.append({
                "row": row,
                "col": col,

                "cell_id":
                    f"cell_{row}_{col}",

                "bbox": (
                    cell_west,
                    cell_south,
                    cell_east,
                    cell_north
                )
            })

    return cells


# =========================================================
# BBox -> HERE string
# =========================================================

def bbox_to_string(
    bbox
):
    west, south, east, north = bbox

    return (
        f"{west},"
        f"{south},"
        f"{east},"
        f"{north}"
    )


# =========================================================
# Fetch one grid cell
# =========================================================

def fetch_cell(
    cell
):
    """
    Fetch traffic flow for exactly one grid cell.
    """

    bbox_string = bbox_to_string(
        cell["bbox"]
    )

    params = {
        "in":
            f"bbox:{bbox_string}",

        "locationReferencing":
            "shape",

        "apiKey":
            HERE_API_KEY,
    }

    response = requests.get(
        HERE_FLOW_URL,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS
    )

    if response.status_code != 200:

        raise RuntimeError(
            f"HERE request failed for "
            f"{cell['cell_id']} "
            f"with status "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    return response.json()


# =========================================================
# Save raw cell
# =========================================================

def save_cell(
    data,
    cell,
    snapshot_folder
):
    """
    Save one cell response as raw JSON.
    """

    path = (
        snapshot_folder
        / f"{cell['cell_id']}.json"
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

    return path


# =========================================================
# Fetch full grid snapshot
# =========================================================

def fetch_grid_snapshot(
    snapshot_folder=None,
    max_requests=MAX_REQUESTS_PER_RUN
):
    """
    Fetch traffic for all grid cells.

    Important properties:

    - hard request budget
    - save each cell immediately
    - skip already downloaded cells
    - can resume after failure
    """

    cells = generate_grid()

    if snapshot_folder is None:

        now = datetime.now()

        snapshot_folder = (
            Path("data")
            / "traffic"
            / "raw_grid"
            / now.strftime("%Y-%m-%d")
            / now.strftime("%H-%M-%S")
        )

    else:

        snapshot_folder = Path(
            snapshot_folder
        )

    snapshot_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 70)
    print("HERE GRID TRAFFIC FETCH")
    print("=" * 70)

    print(
        "Grid:",
        f"{GRID_ROWS} x {GRID_COLS}"
    )

    print(
        "Cells:",
        len(cells)
    )

    print(
        "Request budget:",
        max_requests
    )

    print(
        "Output:",
        snapshot_folder
    )

    print()

    request_count = 0

    successful_cells = 0
    skipped_cells = 0
    failed_cells = []

    for index, cell in enumerate(
        cells,
        start=1
    ):

        output_file = (
            snapshot_folder
            / f"{cell['cell_id']}.json"
        )

        # ---------------------------------------------
        # Resume support:
        # never request a cell already saved
        # ---------------------------------------------

        if output_file.exists():

            print(
                f"[{index}/{len(cells)}] "
                f"{cell['cell_id']} "
                f"already exists -> SKIP"
            )

            skipped_cells += 1

            continue

        # ---------------------------------------------
        # Hard safety budget
        # ---------------------------------------------

        if request_count >= max_requests:

            print()
            print(
                "Request budget reached."
            )

            print(
                "Stopping safely."
            )

            break

        print(
            f"[{index}/{len(cells)}] "
            f"Fetching "
            f"{cell['cell_id']}..."
        )

        print(
            "  bbox:",
            bbox_to_string(
                cell["bbox"]
            )
        )

        try:

            data = fetch_cell(
                cell
            )

            request_count += 1

            results = data.get(
                "results",
                []
            )

            path = save_cell(
                data,
                cell,
                snapshot_folder
            )

            successful_cells += 1

            print(
                "  traffic segments:",
                len(results)
            )

            print(
                "  saved:",
                path
            )

        except Exception as exc:

            request_count += 1

            failed_cells.append(
                cell["cell_id"]
            )

            print(
                "  FAILED:",
                exc
            )

        # ---------------------------------------------
        # Gentle rate limiting
        # ---------------------------------------------

        time.sleep(
            REQUEST_DELAY_SECONDS
        )

    print()
    print("=" * 70)
    print("FETCH SUMMARY")
    print("=" * 70)

    print(
        "API requests used:",
        request_count
    )

    print(
        "Successful cells:",
        successful_cells
    )

    print(
        "Skipped cached cells:",
        skipped_cells
    )

    print(
        "Failed cells:",
        len(failed_cells)
    )

    if failed_cells:

        print(
            "Failed cell IDs:",
            failed_cells
        )

    print(
        "Snapshot folder:",
        snapshot_folder
    )

    return snapshot_folder