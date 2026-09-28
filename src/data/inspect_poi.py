import pandas as pd


FILE = "data/raw/poi/poi_osm_raw.pkl"


def inspect_poi():
    gdf = pd.read_pickle(FILE)

    print("========== BASIC INFO ==========")
    print(f"Total features: {len(gdf)}")
    print(f"Columns: {list(gdf.columns)}")

    print()
    print("========== SAMPLE ==========")
    print(
        gdf[
            [col for col in ["name", "amenity", "tourism", "shop", "leisure"]
             if col in gdf.columns]
        ].head(20)
    )

    print()
    print("========== GEOMETRY TYPES ==========")
    print(gdf.geometry.geom_type.value_counts())

    print()
    print("========== AVAILABLE TAGS ==========")

    for column in ["amenity", "tourism", "shop", "leisure"]:
        if column in gdf.columns:
            print(f"\n--- {column} ---")
            print(gdf[column].value_counts().head(20))


if __name__ == "__main__":
    inspect_poi()