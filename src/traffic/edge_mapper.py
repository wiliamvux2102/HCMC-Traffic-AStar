import math
from pathlib import Path

import pandas as pd
import geopandas as gpd

from shapely import wkt


# =========================================================
# Configuration
# =========================================================

PROJECTED_CRS = "EPSG:32648"

# OSM edge must be within this distance
# from a HERE traffic segment to be considered.
MAX_DISTANCE_M = 20.0

# At least this fraction of the OSM edge
# should lie near the HERE segment.
MIN_OVERLAP_RATIO = 0.30

# HERE direction and OSM direction should
# differ by at most this amount.
MAX_HEADING_DIFF_DEG = 45.0

# Radius used when measuring how much of an
# OSM edge overlaps the HERE segment.
OVERLAP_BUFFER_M = 10.0


# =========================================================
# Geometry helper functions
# =========================================================

def _angle_difference(a, b):
    """
    Return the smallest angular difference between
    two headings in degrees.

    Example:
        350 deg vs 10 deg -> 20 deg
        90 deg vs 270 deg -> 180 deg
    """

    diff = abs(a - b) % 360

    return min(
        diff,
        360 - diff
    )


def _line_heading(line):
    """
    Approximate the direction of a LineString using
    its first and last coordinates.

    Heading convention:

        0   = North
        90  = East
        180 = South
        270 = West

    Geometry should already be projected.
    """

    coords = list(
        line.coords
    )

    if len(coords) < 2:
        return None

    x1, y1 = coords[0]
    x2, y2 = coords[-1]

    dx = x2 - x1
    dy = y2 - y1

    if (
        abs(dx) < 1e-9
        and abs(dy) < 1e-9
    ):
        return None

    angle = math.degrees(
        math.atan2(
            dx,
            dy
        )
    )

    return (
        angle + 360
    ) % 360


def _same_direction(
    here_geom,
    osm_geom,
    max_diff_deg=MAX_HEADING_DIFF_DEG
):
    """
    Check whether HERE and OSM geometries roughly
    point in the same direction.
    """

    here_heading = _line_heading(
        here_geom
    )

    osm_heading = _line_heading(
        osm_geom
    )

    # If one direction cannot be determined,
    # do not reject automatically.
    if (
        here_heading is None
        or osm_heading is None
    ):
        return True, None, None, None

    diff = _angle_difference(
        here_heading,
        osm_heading
    )

    return (
        diff <= max_diff_deg,
        here_heading,
        osm_heading,
        diff
    )


def _overlap_ratio(
    osm_geom,
    here_geom,
    buffer_m=OVERLAP_BUFFER_M
):
    """
    Estimate how much of one OSM edge lies close
    to the HERE segment.

    Example:

        OSM edge length = 100 m
        80 m lies inside HERE buffer

        overlap ratio = 80 / 100 = 0.8
    """

    if osm_geom.length <= 0:
        return 0.0

    here_buffer = (
        here_geom.buffer(
            buffer_m
        )
    )

    intersection = (
        osm_geom.intersection(
            here_buffer
        )
    )

    overlap_length = (
        intersection.length
    )

    return (
        overlap_length
        / osm_geom.length
    )


# =========================================================
# Mapper
# =========================================================

class TrafficEdgeMapper:

    def __init__(
        self,
        osm_edges_path: str,
        here_segments_path: str
    ):
        self.osm_edges_path = Path(
            osm_edges_path
        )

        self.here_segments_path = Path(
            here_segments_path
        )

        self.osm_edges = None
        self.here_segments = None

        self.osm_projected = None
        self.here_projected = None


    # =====================================================
    # 1. Load data
    # =====================================================

    def load_data(self):
        """
        Load OSM edges and normalized HERE traffic data.

        Both files contain geometry as WKT strings.
        Convert those strings into Shapely geometries.
        """

        # -------------------------
        # OSM
        # -------------------------

        osm_df = pd.read_csv(
            self.osm_edges_path
        )

        required_osm_columns = {
            "source",
            "target",
            "edge_key",
            "geometry",
        }

        missing = (
            required_osm_columns
            - set(osm_df.columns)
        )

        if missing:
            raise ValueError(
                f"Missing OSM columns: {missing}"
            )

        osm_df["geometry"] = (
            osm_df["geometry"]
            .apply(wkt.loads)
        )

        self.osm_edges = (
            gpd.GeoDataFrame(
                osm_df,
                geometry="geometry",
                crs="EPSG:4326"
            )
        )

        # -------------------------
        # HERE
        # -------------------------

        here_df = pd.read_csv(
            self.here_segments_path
        )

        required_here_columns = {
            "here_segment_id",
            "description",
            "speed_kph",
            "geometry",
        }

        missing = (
            required_here_columns
            - set(here_df.columns)
        )

        if missing:
            raise ValueError(
                f"Missing HERE columns: {missing}"
            )

        here_df["geometry"] = (
            here_df["geometry"]
            .apply(wkt.loads)
        )

        self.here_segments = (
            gpd.GeoDataFrame(
                here_df,
                geometry="geometry",
                crs="EPSG:4326"
            )
        )

        print(
            "OSM edges:",
            len(self.osm_edges)
        )

        print(
            "HERE segments:",
            len(self.here_segments)
        )


    # =====================================================
    # 2. Project to meter-based CRS
    # =====================================================

    def project_data(self):
        """
        Convert WGS84 lat/lon geometries into a
        projected CRS where distances are measured
        in meters.
        """

        if (
            self.osm_edges is None
            or self.here_segments is None
        ):
            raise RuntimeError(
                "Call load_data() first"
            )

        self.osm_projected = (
            self.osm_edges
            .to_crs(
                PROJECTED_CRS
            )
        )

        self.here_projected = (
            self.here_segments
            .to_crs(
                PROJECTED_CRS
            )
        )

        print(
            "Projected to:",
            PROJECTED_CRS
        )


    # =====================================================
    # 3. Find nearby OSM candidates
    # =====================================================

    def find_candidates(
        self,
        here_index: int,
        max_distance_m: float = MAX_DISTANCE_M
    ):
        """
        Find OSM edges located near one HERE segment.

        Uses a spatial index, so we do not compare
        against all 200k OSM edges manually.
        """

        if (
            self.osm_projected is None
            or self.here_projected is None
        ):
            raise RuntimeError(
                "Call project_data() first"
            )

        here_row = (
            self.here_projected
            .iloc[here_index]
        )

        here_geom = (
            here_row.geometry
        )

        # Create a search area around the HERE segment.
        search_area = (
            here_geom.buffer(
                max_distance_m
            )
        )

        # Spatial index:
        # only retrieve OSM geometries intersecting
        # this small search area.
        possible_positions = list(
            self.osm_projected
            .sindex
            .query(
                search_area,
                predicate="intersects"
            )
        )

        if not possible_positions:
            return (
                self.osm_projected
                .iloc[0:0]
                .copy()
            )

        candidates = (
            self.osm_projected
            .iloc[
                possible_positions
            ]
            .copy()
        )

        candidates[
            "distance_to_here_m"
        ] = (
            candidates.geometry
            .distance(
                here_geom
            )
        )

        candidates = candidates[
            candidates[
                "distance_to_here_m"
            ] <= max_distance_m
        ]

        return candidates


    # =====================================================
    # 4. Match one HERE segment
    # =====================================================

    def match_segment(
        self,
        here_index: int
    ):
        """
        Match one HERE traffic segment to one or more
        OSM road edges.

        Filtering criteria:

            1. Distance
            2. Overlap
            3. Direction
        """

        if (
            self.osm_projected is None
            or self.here_projected is None
        ):
            raise RuntimeError(
                "Call project_data() first"
            )

        here_row = (
            self.here_projected
            .iloc[here_index]
        )

        here_geom = (
            here_row.geometry
        )

        candidates = (
            self.find_candidates(
                here_index
            )
        )

        matches = []

        for _, osm_row in (
            candidates.iterrows()
        ):

            osm_geom = (
                osm_row.geometry
            )

            # -------------------------
            # Overlap check
            # -------------------------

            overlap = (
                _overlap_ratio(
                    osm_geom,
                    here_geom
                )
            )

            if (
                overlap
                < MIN_OVERLAP_RATIO
            ):
                continue

            # -------------------------
            # Direction check
            # -------------------------

            (
                same_direction,
                here_heading,
                osm_heading,
                heading_diff
            ) = _same_direction(
                here_geom,
                osm_geom
            )

            if not same_direction:
                continue

            # -------------------------
            # Accept match
            # -------------------------

            matches.append({
                "here_segment_id":
                    here_row[
                        "here_segment_id"
                    ],

                "here_description":
                    here_row[
                        "description"
                    ],

                "here_speed_kph":
                    float(
                        here_row[
                            "speed_kph"
                        ]
                    ),

                "osm_source":
                    int(
                        osm_row[
                            "source"
                        ]
                    ),

                "osm_target":
                    int(
                        osm_row[
                            "target"
                        ]
                    ),

                "osm_edge_key":
                    int(
                        osm_row[
                            "edge_key"
                        ]
                    ),

                "distance_m":
                    float(
                        osm_row[
                            "distance_to_here_m"
                        ]
                    ),

                "overlap_ratio":
                    float(
                        overlap
                    ),

                "here_heading_deg":
                    (
                        float(
                            here_heading
                        )
                        if here_heading
                        is not None
                        else None
                    ),

                "osm_heading_deg":
                    (
                        float(
                            osm_heading
                        )
                        if osm_heading
                        is not None
                        else None
                    ),

                "heading_diff_deg":
                    (
                        float(
                            heading_diff
                        )
                        if heading_diff
                        is not None
                        else None
                    ),
            })

        return matches


    # =====================================================
    # 5. Match every HERE segment
    # =====================================================

    def match_all(self):
        """
        Match all HERE traffic segments against
        the OSM graph.
        """

        if (
            self.here_projected is None
        ):
            raise RuntimeError(
                "Call project_data() first"
            )

        all_matches = []

        total = len(
            self.here_projected
        )

        segments_with_match = 0

        for index in range(
            total
        ):

            matches = (
                self.match_segment(
                    index
                )
            )

            if matches:
                segments_with_match += 1

                all_matches.extend(
                    matches
                )

        result_df = (
            pd.DataFrame(
                all_matches
            )
        )

        print()
        print(
            "=== MAPPING SUMMARY ==="
        )

        print(
            "HERE segments:",
            total
        )

        print(
            "HERE segments matched:",
            segments_with_match
        )

        print(
            "HERE segments unmatched:",
            (
                total
                - segments_with_match
            )
        )

        print(
            "HERE -> OSM mappings:",
            len(result_df)
        )

        return result_df


    # =====================================================
    # 6. Save mapping
    # =====================================================

    def save_mapping(
        self,
        mapping_df: pd.DataFrame,
        output_path: str
    ):
        """
        Save HERE -> OSM mapping table.
        """

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        mapping_df.to_csv(
            output_path,
            index=False
        )

        print(
            "Mapping saved to:",
            output_path
        )