import pandas as pd


MAPPING_PATH = (
    "data/traffic/mapping/"
    "00-25-14-grid-mapping.csv"
)


def main():
    df = pd.read_csv(
        MAPPING_PATH
    )

    print("=" * 70)
    print("MAPPING QUALITY CHECK")
    print("=" * 70)

    print()
    print("Total mapping rows:")
    print(len(df))

    # -----------------------------------------------------
    # Unique HERE segments
    # -----------------------------------------------------

    unique_here = (
        df["here_segment_id"]
        .nunique()
    )

    print()
    print("Unique HERE segments matched:")
    print(unique_here)

    # -----------------------------------------------------
    # Unique OSM edges
    # -----------------------------------------------------

    unique_osm = (
        df[
            [
                "osm_source",
                "osm_target",
                "osm_edge_key",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )

    print()
    print("Unique OSM edges matched:")
    print(unique_osm)

    # -----------------------------------------------------
    # Distance statistics
    # -----------------------------------------------------

    print()
    print("=== DISTANCE ===")

    print(
        df["distance_m"]
        .describe()
    )

    # -----------------------------------------------------
    # Overlap statistics
    # -----------------------------------------------------

    print()
    print("=== OVERLAP ===")

    print(
        df["overlap_ratio"]
        .describe()
    )

    # -----------------------------------------------------
    # Heading statistics
    # -----------------------------------------------------

    print()
    print("=== HEADING DIFFERENCE ===")

    print(
        df["heading_diff_deg"]
        .describe()
    )

    # -----------------------------------------------------
    # Match quality buckets
    # -----------------------------------------------------

    print()
    print("=== OVERLAP QUALITY ===")

    high_overlap = (
        df["overlap_ratio"]
        >= 0.70
    ).sum()

    medium_overlap = (
        (
            df["overlap_ratio"]
            >= 0.50
        )
        &
        (
            df["overlap_ratio"]
            < 0.70
        )
    ).sum()

    low_overlap = (
        (
            df["overlap_ratio"]
            >= 0.30
        )
        &
        (
            df["overlap_ratio"]
            < 0.50
        )
    ).sum()

    print(
        "High overlap >= 0.70:",
        high_overlap
    )

    print(
        "Medium overlap 0.50-0.70:",
        medium_overlap
    )

    print(
        "Low overlap 0.30-0.50:",
        low_overlap
    )

    # -----------------------------------------------------
    # HERE -> number of OSM edges
    # -----------------------------------------------------

    print()
    print("=== OSM EDGES PER HERE SEGMENT ===")

    edges_per_here = (
        df.groupby(
            "here_segment_id"
        )
        .size()
    )

    print(
        edges_per_here.describe()
    )

    print()
    print(
        "HERE segments mapped to >1 OSM edge:"
    )

    print(
        (
            edges_per_here > 1
        ).sum()
    )

    # -----------------------------------------------------
    # OSM edge receives multiple HERE segments
    # -----------------------------------------------------

    print()
    print(
        "=== MULTIPLE HERE SEGMENTS PER OSM EDGE ==="
    )

    here_per_osm = (
        df.groupby(
            [
                "osm_source",
                "osm_target",
                "osm_edge_key",
            ]
        )[
            "here_segment_id"
        ]
        .nunique()
    )

    conflicts = (
        here_per_osm[
            here_per_osm > 1
        ]
    )

    print(
        "OSM edges matched by multiple HERE segments:",
        len(conflicts)
    )

    # -----------------------------------------------------
    # Suspicious matches
    # -----------------------------------------------------

    print()
    print("=== SUSPICIOUS MATCHES ===")

    suspicious = df[
        (
            df["overlap_ratio"]
            < 0.40
        )
        |
        (
            df["distance_m"]
            > 15
        )
        |
        (
            df["heading_diff_deg"]
            > 30
        )
    ]

    print(
        "Suspicious rows:",
        len(suspicious)
    )

    if not suspicious.empty:
        print()
        print(
            suspicious[
                [
                    "here_segment_id",
                    "here_description",
                    "osm_source",
                    "osm_target",
                    "osm_edge_key",
                    "distance_m",
                    "overlap_ratio",
                    "heading_diff_deg",
                ]
            ]
            .head(20)
        )


if __name__ == "__main__":
    main()