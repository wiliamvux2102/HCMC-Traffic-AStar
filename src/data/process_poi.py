from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data/raw/poi/poi_osm_raw.pkl"
OUTPUT_DIR = PROJECT_ROOT / "data/processed"
OUTPUT_FILE = OUTPUT_DIR / "pois.csv"

# Verified in the raw OSM data:
# Trường Đại học Bách khoa, ĐHQG TP.HCM
# 268 Lý Thường Kiệt
HCMUT_CS1_OSM_ID = ("way", 237665212)

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

CATEGORY_RULES = [
    ("amenity", "university", "university"),
    ("amenity", "hospital", "hospital"),
    ("amenity", "school", "school"),
    ("tourism", "hotel", "hotel"),
    ("leisure", "park", "park"),
    ("shop", "supermarket", "supermarket"),
    ("shop", "mall", "mall"),
    ("tourism", "attraction", "tourist_attraction"),
    ("tourism", "museum", "museum"),
    ("amenity", "bus_station", "bus_station"),
]


def get_category(row):
    """Determine the normalized category of an OSM feature."""
    for tag, expected_value, category in CATEGORY_RULES:
        value = row.get(tag)

        if pd.notna(value) and value == expected_value:
            return category

    return None


def process_pois():
    print("Loading raw OSM POIs...")
    gdf = pd.read_pickle(INPUT_FILE)

    print(f"Raw features: {len(gdf)}")

    # --------------------------------------------------
    # 1. Validate the raw data needed by this script.
    # --------------------------------------------------
    if "name" not in gdf.columns:
        raise ValueError("Raw POI data is missing the name column.")

    if not isinstance(gdf.index, pd.MultiIndex):
        raise ValueError(
            "Raw POI data must have an OSM (element, id) MultiIndex."
        )

    if gdf.index.nlevels != 2 or not gdf.index.is_unique:
        raise ValueError(
            "Raw POI data must have a unique two-level OSM index."
        )

    if HCMUT_CS1_OSM_ID not in gdf.index:
        raise ValueError(
            "Raw POI data does not contain HCMUT CS1: "
            "way/237665212."
        )

    if gdf.crs is None:
        raise ValueError("Raw POI data is missing its CRS.")

    # --------------------------------------------------
    # 2. Keep only features with a name.
    # --------------------------------------------------
    gdf = gdf[gdf["name"].notna()].copy()

    print(f"Features with name: {len(gdf)}")

    if HCMUT_CS1_OSM_ID not in gdf.index:
        raise ValueError("HCMUT CS1 is missing its name.")

    campus_geometry = gdf.loc[
        [HCMUT_CS1_OSM_ID]
    ].geometry.iloc[0]

    if (
        campus_geometry is None
        or campus_geometry.is_empty
        or not campus_geometry.is_valid
        or campus_geometry.geom_type not in ("Polygon", "MultiPolygon")
    ):
        raise ValueError(
            "HCMUT CS1 must have a valid campus polygon."
        )

    # --------------------------------------------------
    # 3. Calculate centroids in a projected CRS.
    # --------------------------------------------------
    gdf = gdf.to_crs(epsg=32648)
    gdf["geometry"] = gdf.geometry.centroid
    gdf = gdf.to_crs(epsg=4326)

    # --------------------------------------------------
    # 4. Determine normalized categories.
    # --------------------------------------------------
    gdf["category"] = gdf.apply(get_category, axis=1)
    gdf = gdf[gdf["category"].notna()].copy()

    if HCMUT_CS1_OSM_ID not in gdf.index:
        raise ValueError("HCMUT CS1 has no supported category.")

    campus = gdf.loc[[HCMUT_CS1_OSM_ID]]

    if campus["category"].iloc[0] != "university":
        raise ValueError(
            "HCMUT CS1 must belong to the university category."
        )

    # --------------------------------------------------
    # 5. Sample each category.
    #    Ensure HCMUT CS1 is included in university.
    # --------------------------------------------------
    selected = []

    for category, limit in CATEGORY_LIMITS.items():
        subset = gdf[gdf["category"] == category].copy()

        if len(subset) > limit:
            subset = subset.sample(
                n=limit,
                random_state=42,
            )

        if category == "university":
            if HCMUT_CS1_OSM_ID not in subset.index:
                # Preserve the first 19 sampled universities.
                # Replace the last slot with HCMUT CS1.
                subset = pd.concat([
                    subset.iloc[:limit - 1],
                    campus,
                ])

                print(
                    "Included HCMUT CS1 by replacing the "
                    "last sampled university."
                )

        print(f"{category}: {len(subset)} selected")
        selected.append(subset)

    # Preserve OSM indices until mandatory-POI verification.
    result = pd.concat(selected)

    campus_mask = result.index.isin([HCMUT_CS1_OSM_ID])

    if campus_mask.sum() != 1:
        raise ValueError(
            "The selected POIs must contain HCMUT CS1 exactly once."
        )

    result = result.reset_index(drop=True)

    # --------------------------------------------------
    # 6. Extract coordinates.
    # --------------------------------------------------
    result["longitude"] = result.geometry.x
    result["latitude"] = result.geometry.y

    # --------------------------------------------------
    # 7. Create POI IDs.
    # --------------------------------------------------
    result.insert(
        0,
        "poi_id",
        [
            f"POI{i:04d}"
            for i in range(1, len(result) + 1)
        ],
    )

    print()
    print("========== HCMUT CS1 ==========")
    print(
        result.loc[
            campus_mask,
            ["poi_id", "name", "latitude", "longitude"],
        ].to_string(index=False)
    )

    # --------------------------------------------------
    # 8. Preserve the original output schema.
    # --------------------------------------------------
    result = result[
        [
            "poi_id",
            "name",
            "category",
            "latitude",
            "longitude",
        ]
    ].copy()

    # --------------------------------------------------
    # 9. Save.
    # --------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print()
    print("========== RESULT ==========")
    print(f"Total POIs: {len(result)}")
    print(f"Saved to: {OUTPUT_FILE}")

    print()
    print("========== CATEGORY COUNTS ==========")
    print(result["category"].value_counts())

    return result


if __name__ == "__main__":
    process_pois()