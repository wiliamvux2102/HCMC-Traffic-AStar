import pandas as pd


POI_FILE = "data/raw/poi/poi_raw.csv"

REQUIRED_COLUMNS = [
    "poi_id",
    "name",
    "category",
    "latitude",
    "longitude",
    "address"
]


def load_pois():
    print("Loading POI data...")

    df = pd.read_csv(POI_FILE)

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if df["poi_id"].duplicated().any():
        duplicates = df[
            df["poi_id"].duplicated(keep=False)
        ]

        raise ValueError(
            f"Duplicate POI IDs:\n{duplicates}"
        )

    invalid_latitude = ~df["latitude"].between(-90, 90)
    invalid_longitude = ~df["longitude"].between(-180, 180)

    if invalid_latitude.any():
        raise ValueError("Invalid latitude found.")

    if invalid_longitude.any():
        raise ValueError("Invalid longitude found.")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Missing values found in POI data.")

    print("POI data is valid.")
    print(f"Number of POIs: {len(df)}")

    return df


if __name__ == "__main__":
    pois = load_pois()

    print()
    print(pois.head())