# scripts/build_baseline.py

from src.traffic.baseline import enrich_edges


edges = enrich_edges(
    input_path="data/processed/edges.csv",
    output_path="data/processed/edges_enriched.csv"
)

print(edges.head())

print()
print("Total edges:", len(edges))

print(
    "Edges with OSM maxspeed:",
    edges["maxspeed_kph"].notna().sum()
)

print(
    "Edges using inferred speed:",
    edges["maxspeed_kph"].isna().sum()
)