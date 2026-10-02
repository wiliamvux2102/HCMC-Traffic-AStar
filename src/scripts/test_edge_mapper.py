from src.traffic.edge_mapper import (
    TrafficEdgeMapper
)


mapper = TrafficEdgeMapper(
    osm_edges_path=(
        "data/processed/"
        "edges_enriched.csv"
    ),

    here_segments_path=(
        "data/traffic/"
        "normalized/"
        "2026-10-02/"
        "16-57-46-here.csv"
    )
)


mapper.load_data()

mapper.project_data()


# =========================================================
# Test one segment first
# =========================================================

matches = mapper.match_segment(
    0
)

print()
print(
    "=== HERE_0 MATCHES ==="
)

print(
    "Number of matches:",
    len(matches)
)

for match in matches:
    print(match)


# =========================================================
# Batch mapping
# =========================================================

mapping_df = (
    mapper.match_all()
)

print()
print(
    mapping_df.head(20)
)


mapper.save_mapping(
    mapping_df,
    (
        "data/traffic/mapping/"
        "here_osm_mapping.csv"
    )
)