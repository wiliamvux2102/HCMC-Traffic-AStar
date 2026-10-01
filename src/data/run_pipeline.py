import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


STEPS = [
    ("Load road network", "src/data/load_road.py"),
    ("Export road graph to CSV", "src/data/export_graph.py"),
    ("Download POIs", "src/data/download_poi.py"),
    ("Process POIs", "src/data/process_poi.py"),
    ("Map POIs to road nodes", "src/data/map_poi_to_node.py"),
    ("Validate POI mapping", "src/data/validate_poi_mapping.py"),
]

def run_step(name, script):
    print()
    print("=" * 60)
    print(f"STEP: {name}")
    print("=" * 60)

    script_path = PROJECT_ROOT / script

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        print()
        print(f"ERROR: {name} failed.")
        print(f"Script: {script}")
        sys.exit(result.returncode)

    print()
    print(f"{name} completed successfully.")


def main():
    print("=" * 60)
    print("HCMC TRAFFIC A* - DATA PIPELINE")
    print("=" * 60)

    for name, script in STEPS:
        run_step(name, script)

    print()
    print("=" * 60)
    print("DATA PIPELINE COMPLETED")
    print("=" * 60)

    print()
    print("Processed files:")

    files = [
        "data/processed/nodes.csv",
        "data/processed/edges.csv",
        "data/processed/pois.csv",
        "data/processed/poi_node_mapping.csv",
        "data/processed/poi_final.csv",
    ]

    for file in files:
        path = PROJECT_ROOT / file

        if path.exists():
            print(f"  {file}")
        else:
            print(f"  {file} NOT FOUND")


if __name__ == "__main__":
    main()