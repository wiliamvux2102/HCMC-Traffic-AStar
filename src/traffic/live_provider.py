# src/traffic/live_provider.py

from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json

import pandas as pd

from src.traffic.provider import TrafficProvider
from src.traffic.normalizer import normalize_here_response
from src.traffic.edge_mapper import TrafficEdgeMapper
from src.traffic.mapping_resolver import (
    resolve_osm_conflicts,
    build_live_edge_speeds,
)
from src.traffic.snapshot_builder import (
    build_complete_edge_speeds,
)
from src.traffic.snapshot import dataframe_to_snapshot
from src.traffic.models import TrafficSnapshot

# Lazy import to avoid HERE_API_KEY requirement at module load
_fetch_grid_snapshot = None


def _get_grid_fetcher():
    global _fetch_grid_snapshot
    if _fetch_grid_snapshot is None:
        from src.traffic.grid_fetcher import fetch_grid_snapshot
        _fetch_grid_snapshot = fetch_grid_snapshot
    return _fetch_grid_snapshot


class LiveProvider(TrafficProvider):

    def __init__(
        self,
        edges_path: str,
        cache_ttl_minutes: int = 10,
        snapshot_output_dir: str = "data/traffic/snapshots",
    ):
        self.edges_path = edges_path

        self.edges_df = pd.read_csv(
            edges_path
        )

        self.cache_ttl = timedelta(
            minutes=cache_ttl_minutes
        )

        self.snapshot_output_dir = Path(
            snapshot_output_dir
        )

        self._cached_snapshot: TrafficSnapshot | None = None
        self._cached_at: datetime | None = None


    # =====================================================
    # Cache
    # =====================================================

    def _cache_valid(
        self,
        now: datetime
    ) -> bool:

        if (
            self._cached_snapshot is None
            or self._cached_at is None
        ):
            return False

        age = now - self._cached_at

        return age < self.cache_ttl


    # =====================================================
    # Normalize + merge all grid cells
    # =====================================================

    def _merge_grid_files(
        self,
        folder: Path
    ) -> pd.DataFrame:

        frames = []

        files = sorted(
            folder.glob(
                "cell_*.json"
            )
        )

        if not files:
            raise RuntimeError(
                f"No grid files found in {folder}"
            )

        for path in files:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            df = normalize_here_response(
                data
            )

            df["grid_cell"] = (
                path.stem
            )

            frames.append(
                df
            )

        merged = pd.concat(
            frames,
            ignore_index=True
        )

        def segment_hash(row):

            raw = (
                str(row["description"])
                + "|"
                + str(row["geometry"])
            )

            return hashlib.sha1(
                raw.encode("utf-8")
            ).hexdigest()

        merged[
            "segment_hash"
        ] = merged.apply(
            segment_hash,
            axis=1
        )

        merged = (
            merged
            .drop_duplicates(
                subset=[
                    "segment_hash"
                ]
            )
            .reset_index(
                drop=True
            )
        )

        merged[
            "here_segment_id"
        ] = [
            f"GRID_HERE_{i}"
            for i in range(
                len(merged)
            )
        ]

        return merged


    # =====================================================
    # Save complete snapshot for replay
    # =====================================================

    def _save_complete_snapshot(
        self,
        df: pd.DataFrame,
        timestamp: datetime
    ) -> Path:

        folder = (
            self.snapshot_output_dir
            / timestamp.strftime(
                "%Y-%m-%d"
            )
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        path = (
            folder
            / (
                timestamp.strftime(
                    "%H-%M-%S"
                )
                + "-complete.csv"
            )
        )

        df.to_csv(
            path,
            index=False
        )

        return path


    # =====================================================
    # Main public method
    # =====================================================

    def get_snapshot(
        self,
        timestamp: datetime
    ) -> TrafficSnapshot:

        # ---------------------------------------------
        # 1. Reuse cache
        # ---------------------------------------------

        if self._cache_valid(
            timestamp
        ):

            print(
                "Using cached LIVE snapshot"
            )

            return self._cached_snapshot

        print(
            "Fetching new LIVE traffic snapshot..."
        )

        # ---------------------------------------------
        # 2. Fetch full HERE grid
        # ---------------------------------------------

        fetch_grid = _get_grid_fetcher()
        raw_folder = (
            fetch_grid()
        )

        # ---------------------------------------------
        # 3. Normalize + merge
        # ---------------------------------------------

        here_df = (
            self._merge_grid_files(
                raw_folder
            )
        )

        runtime_dir = Path(
            "data/traffic/runtime"
        )

        runtime_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        here_path = (
            runtime_dir
            / "current_here.csv"
        )

        here_df.to_csv(
            here_path,
            index=False
        )

        # ---------------------------------------------
        # 4. HERE -> OSM
        # ---------------------------------------------

        mapper = TrafficEdgeMapper(
            osm_edges_path=
                self.edges_path,

            here_segments_path=
                str(here_path)
        )

        mapper.load_data()
        mapper.project_data()

        mapping_df = (
            mapper.match_all()
        )

        if mapping_df.empty:
            raise RuntimeError(
                "No HERE segments mapped to OSM"
            )

        # ---------------------------------------------
        # 5. Resolve conflicts
        # ---------------------------------------------

        resolved = (
            resolve_osm_conflicts(
                mapping_df
            )
        )

        live_df = (
            build_live_edge_speeds(
                resolved
            )
        )

        # ---------------------------------------------
        # 6. LIVE + FALLBACK
        # ---------------------------------------------

        complete_df = (
            build_complete_edge_speeds(
                edges_df=
                    self.edges_df,

                live_df=
                    live_df,

                timestamp=
                    timestamp
            )
        )

        # ---------------------------------------------
        # 7. Save replay snapshot
        # ---------------------------------------------

        saved_path = (
            self._save_complete_snapshot(
                complete_df,
                timestamp
            )
        )

        print(
            "Complete snapshot saved:",
            saved_path
        )

        # ---------------------------------------------
        # 8. Convert to object
        # ---------------------------------------------

        snapshot = (
            dataframe_to_snapshot(
                complete_df,
                timestamp.isoformat()
            )
        )

        # ---------------------------------------------
        # 9. Update cache
        # ---------------------------------------------

        self._cached_snapshot = snapshot
        self._cached_at = timestamp

        return snapshot