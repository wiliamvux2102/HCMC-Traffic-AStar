from pathlib import Path

from src.traffic.edge_mapper import TrafficEdgeMapper


EDGES_PATH = (
    "data/processed/edges_enriched.csv"
)

HERE_PATH = (
    "data/traffic/runtime/current_here.csv"
)

OUTPUT_PATH = (
    "data/traffic/mapping/"
    "2026-10-11/"
    "03-57-24-mapping.csv"
)


def main():

    print("=" * 70)
    print("REBUILD HERE -> OSM MAPPING")
    print("=" * 70)

    if not Path(HERE_PATH).exists():
        raise FileNotFoundError(
            f"HERE runtime file not found: {HERE_PATH}"
        )

    mapper = TrafficEdgeMapper(
        osm_edges_path=EDGES_PATH,
        here_segments_path=HERE_PATH,
    )

    mapper.load_data()
    mapper.project_data()

    mapping_df = mapper.match_all()

    if mapping_df.empty:
        raise RuntimeError(
            "No HERE segments mapped to OSM."
        )

    mapper.save_mapping(
        mapping_df,
        OUTPUT_PATH,
    )

    print()
    print("Mapping rows:", len(mapping_df))

    print(
        "Unique HERE segments:",
        mapping_df[
            "here_segment_id"
        ].nunique()
    )

    unique_osm = (
        mapping_df[
            [
                "osm_source",
                "osm_target",
                "osm_edge_key",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )

    print(
        "Unique OSM edges before resolution:",
        unique_osm,
    )

    print()
    print(
        "Mapping rebuild completed."
    )


if __name__ == "__main__":
    main()