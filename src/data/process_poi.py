import pandas as pd
import geopandas as gpd
from pathlib import Path


INPUT_FILE = "data/raw/poi/poi_osm_raw.pkl"
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "pois.csv"


# Number of POIs we want from each category
CATEGORY_LIMITS = {
    "university": 20,
    "hospital": 20,
    "school": 20,
    "hotel": 20,
    "park": 20,
    "supermarket": 15,
    "mall": 15,
    "tourist_attraction": 10,
    "museum": 10,
    "bus_station": 10,
}


def get_category(row):
    """
    Determine the normalized category of an OSM feature.
    """

    if row.get("amenity") == "university":
        return "university"

    if row.get("amenity") == "hospital":
        return "hospital"

    if row.get("amenity") == "school":
        return "school"

    if row.get("tourism") == "hotel":
        return "hotel"

    if row.get("leisure") == "park":
        return "park"

    if row.get("shop") == "supermarket":
        return "supermarket"

    if row.get("shop") == "mall":
        return "mall"

    if row.get("tourism") == "attraction":
        return "tourist_attraction"

    if row.get("tourism") == "museum":
        return "museum"

    if row.get("amenity") == "bus_station":
        return "bus_station"

    return None


def process_pois():

    print("Loading raw OSM POIs...")

    gdf = pd.read_pickle(INPUT_FILE)

    print(f"Raw features: {len(gdf)}")

    # --------------------------------------------------
    # 1. Keep only features with a name
    # --------------------------------------------------

    gdf = gdf[
        gdf["name"].notna()
    ].copy()

    print(
        f"Features with name: {len(gdf)}"
    )

    # --------------------------------------------------
    # 2. Convert polygon geometry to centroid correctly
    # --------------------------------------------------

    # OSM data uses WGS84 latitude/longitude.
    # Re-project to a projected CRS before calculating centroid.

    gdf = gdf.to_crs(epsg=32648)

    gdf["geometry"] = gdf.geometry.centroid

    # Convert back to WGS84 for storing latitude/longitude.
    gdf = gdf.to_crs(epsg=4326)

    # --------------------------------------------------
    # 3. Determine normalized category
    # --------------------------------------------------

    gdf["category"] = gdf.apply(
        get_category,
        axis=1
    )

    # Remove unsupported categories
    gdf = gdf[
        gdf["category"].notna()
    ].copy()

    # --------------------------------------------------
    # 4. Sample each category
    # --------------------------------------------------

    selected = []

    for category, limit in CATEGORY_LIMITS.items():

        subset = gdf[
            gdf["category"] == category
        ].copy()

        if len(subset) > limit:
            subset = subset.sample(
                n=limit,
                random_state=42
            )

        print(
            f"{category}: "
            f"{len(subset)} selected"
        )

        selected.append(subset)

    # --------------------------------------------------
    # 5. Combine
    # --------------------------------------------------

    result = pd.concat(
        selected,
        ignore_index=True
    )

    # --------------------------------------------------
    # 6. Extract coordinates
    # --------------------------------------------------

    result["longitude"] = result.geometry.x
    result["latitude"] = result.geometry.y

    # --------------------------------------------------
    # 7. Create POI IDs
    # --------------------------------------------------

    result.insert(
        0,
        "poi_id",
        [
            f"POI{i:04d}"
            for i in range(
                1,
                len(result) + 1
            )
        ]
    )

    # --------------------------------------------------
    # 8. Select final columns
    # --------------------------------------------------

    result = result[
        [
            "poi_id",
            "name",
            "category",
            "latitude",
            "longitude",
        ]
    ]

    # --------------------------------------------------
    # 9. Save
    # --------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("========== RESULT ==========")
    print(f"Total POIs: {len(result)}")
    print(f"Saved to: {OUTPUT_FILE}")

    print()
    print("========== CATEGORY COUNTS ==========")
    print(
        result["category"].value_counts()
    )


if __name__ == "__main__":
    process_pois()