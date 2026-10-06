from pathlib import Path
import hashlib

import pandas as pd

from src.traffic.normalizer import (
    normalize_here_response
)

import json


SNAPSHOT_FOLDER = Path(
    "data/traffic/raw_grid/"
    "2026-10-03/"
    "00-25-14"
)

OUTPUT = Path(
    "data/traffic/normalized/"
    "2026-10-03/"
    "00-25-14-grid-here.csv"
)


def make_segment_hash(row):
    """
    Stable-ish key for duplicate detection across cells.

    Same road segment appearing in adjacent grid cells
    should normally have same geometry.
    """

    raw = (
        str(row["description"])
        + "|"
        + str(row["geometry"])
    )

    return hashlib.sha1(
        raw.encode("utf-8")
    ).hexdigest()


def main():

    files = sorted(
        SNAPSHOT_FOLDER.glob(
            "cell_*.json"
        )
    )

    print(
        "Grid files found:",
        len(files)
    )

    if not files:
        raise RuntimeError(
            "No grid JSON files found"
        )


    frames = []

    # ==============================================
    # Normalize each raw cell
    # ==============================================

    for path in files:

        print(
            "Normalizing:",
            path.name
        )

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        df = normalize_here_response(
            data
        )

        df["grid_cell"] = (
            path.stem
        )

        frames.append(
            df
        )


    # ==============================================
    # Merge
    # ==============================================

    merged = pd.concat(
        frames,
        ignore_index=True
    )


    print()
    print(
        "Rows before dedup:",
        len(merged)
    )


    # ==============================================
    # Build geometry-based hash
    # ==============================================

    merged[
        "segment_hash"
    ] = merged.apply(
        make_segment_hash,
        axis=1
    )


    # ==============================================
    # Deduplicate
    # ==============================================

    dedup = (
        merged
        .drop_duplicates(
            subset=[
                "segment_hash"
            ],
            keep="first"
        )
        .copy()
    )


    print(
        "Rows after dedup:",
        len(dedup)
    )

    print(
        "Duplicates removed:",
        len(merged)
        - len(dedup)
    )

    dedup = dedup.reset_index(
    drop=True
)

    dedup[
        "here_segment_id"
    ] = [
        f"GRID_HERE_{i}"
        for i in range(
            len(dedup)
        )
    ]

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    dedup.to_csv(
        OUTPUT,
        index=False
    )


    print()
    print(
        "Saved:",
        OUTPUT
    )


if __name__ == "__main__":
    main()