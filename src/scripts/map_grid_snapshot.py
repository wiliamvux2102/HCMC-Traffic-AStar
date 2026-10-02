from src.traffic.edge_mapper import (
    TrafficEdgeMapper
)


OSM_PATH = (
    "data/processed/"
    "edges_enriched.csv"
)

HERE_PATH = (
    "data/traffic/normalized/"
    "2026-10-03/"
    "00-25-14-grid-here.csv"
)

OUTPUT_PATH = (
    "data/traffic/mapping/"
    "00-25-14-grid-mapping.csv"
)


def main():

    mapper = TrafficEdgeMapper(
        osm_edges_path=OSM_PATH,
        here_segments_path=HERE_PATH
    )

    mapper.load_data()

    mapper.project_data()

    mapping_df = (
        mapper.match_all()
    )

    mapper.save_mapping(
        mapping_df,
        OUTPUT_PATH
    )


if __name__ == "__main__":
    main()