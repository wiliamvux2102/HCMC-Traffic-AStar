import pandas as pd


EDGES = (
    "data/processed/"
    "edges_enriched.csv"
)

LIVE = (
    "data/traffic/normalized/"
    "2026-10-03/"
    "00-25-14-grid-live-edges.csv"
)


def main():

    edges = pd.read_csv(
        EDGES
    )

    live = pd.read_csv(
        LIVE
    )


    key_cols = [
        "source",
        "target",
        "edge_key"
    ]


    live_keys = live[
        key_cols
    ].drop_duplicates()


    merged = edges.merge(
        live_keys.assign(
            has_live=True
        ),
        on=key_cols,
        how="left"
    )

    merged[
        "has_live"
    ] = (
        merged[
            "has_live"
        ]
        .fillna(False)
    )


    print(
        "Total OSM edges:",
        len(merged)
    )

    print(
        "Live edges:",
        merged[
            "has_live"
        ].sum()
    )

    print(
        "Overall coverage:",
        (
            merged[
                "has_live"
            ].mean()
            * 100
        )
    )


    highway_col = (
        "highway_normalized"
        if "highway_normalized"
        in merged.columns
        else "highway"
    )


    stats = (
        merged.groupby(
            highway_col
        )
        ["has_live"]
        .agg(
            total="size",
            live="sum"
        )
        .reset_index()
    )


    stats[
        "coverage_pct"
    ] = (
        stats["live"]
        / stats["total"]
        * 100
    )


    stats = (
        stats.sort_values(
            "total",
            ascending=False
        )
    )


    print()
    print(stats.to_string(
        index=False
    ))


if __name__ == "__main__":
    main()