import osmnx as ox
import pandas as pd
from pathlib import Path
from shapely.geometry import box


# Same area used for the road network
CENTER_LAT = 10.7769
CENTER_LON = 106.7009
DISTANCE = 15000

OUTPUT_DIR = Path("data/raw/poi")
OUTPUT_FILE = OUTPUT_DIR / "poi_osm_raw.csv"


def create_bbox():
    """
    Create an approximate bounding box around the road network area.

    The graph was downloaded using:
        center = (10.7769, 106.7009)
        dist = 15000
        dist_type = "bbox"
    """

    # Approximate conversion:
    # 1 degree latitude ~= 111 km
    delta_lat = DISTANCE / 111000

    # Longitude degree length depends on latitude
    import math
    delta_lon = DISTANCE / (
        111000 * math.cos(math.radians(CENTER_LAT))
    )

    north = CENTER_LAT + delta_lat
    south = CENTER_LAT - delta_lat
    east = CENTER_LON + delta_lon
    west = CENTER_LON - delta_lon

    return box(
        west,
        south,
        east,
        north
    )


def download_pois():

    print("Creating query area...")

    polygon = create_bbox()

    tags = {
        "amenity": [
            "hospital",
            "school",
            "university",
            "college",
            "clinic",
            "library",
            "bus_station"
        ],

        "tourism": [
            "attraction",
            "museum",
            "gallery",
            "hotel"
        ],

        "shop": [
            "mall",
            "supermarket"
        ],

        "leisure": [
            "park",
            "sports_centre"
        ]
    }

    print("Downloading POIs from OpenStreetMap...")
    print("This may take some time...")

    gdf = ox.features.features_from_polygon(
        polygon,
        tags
    )

    print(f"Raw OSM features: {len(gdf)}")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    gdf.to_pickle(
        OUTPUT_DIR / "poi_osm_raw.pkl"
    )

    print(
        f"Raw data saved to: "
        f"{OUTPUT_DIR / 'poi_osm_raw.pkl'}"
    )


if __name__ == "__main__":
    download_pois()