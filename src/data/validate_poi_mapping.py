import pandas as pd
from pathlib import Path


INPUT_FILE = "data/processed/poi_node_mapping.csv"
OUTPUT_FILE = "data/processed/poi_final.csv"

MAX_DISTANCE_M = 500


def validate_mapping():

    print("Loading POI-node mapping...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Total mapped POIs: {len(df)}")

    # Find invalid mappings
    invalid = df[
        df["distance_to_node_m"] > MAX_DISTANCE_M
    ].copy()

    valid = df[
        df["distance_to_node_m"] <= MAX_DISTANCE_M
    ].copy()

    print()
    print("========== VALIDATION ==========")
    print(f"Valid POIs:   {len(valid)}")
    print(f"Invalid POIs: {len(invalid)}")

    if len(invalid) > 0:
        print()
        print("Invalid POIs:")
        print(
            invalid[
                [
                    "poi_id",
                    "name",
                    "category",
                    "distance_to_node_m"
                ]
            ].to_string(index=False)
        )

    # Save final dataset
    Path("data/processed").mkdir(
        parents=True,
        exist_ok=True
    )

    valid.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(f"Final POI dataset saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    validate_mapping()