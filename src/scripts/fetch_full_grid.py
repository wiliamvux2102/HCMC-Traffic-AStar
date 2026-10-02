from src.traffic.grid_fetcher import (
    fetch_grid_snapshot
)


def main():

    fetch_grid_snapshot(max_requests=16)


if __name__ == "__main__":
    main()