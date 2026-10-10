"""Flask routes for the HCMC Traffic A* visualization with realtime traffic."""

from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, jsonify, request
import json
from src.visualization import (
    get_map_bounds,
    generate_geojson_edges,
    generate_geojson_nodes,
    generate_geojson_pois,
    get_categories,
    get_all_pois,
    find_path_between_pois,
    generate_route_geojson_with_start_end,
    load_graph,
)
from src.traffic.service import TrafficService
from src.traffic.models import TrafficSnapshot


viz_bp = Blueprint("visualization", __name__)

# Cache graph for performance (but NOT snapshot - use realtime)
_cached_graph = None
_traffic_service = None

# HCMC timezone (UTC+7)
HCMC_TZ = timezone(timedelta(hours=7))


def get_cached_graph():
    """Get or load graph (cached)."""
    global _cached_graph
    if _cached_graph is None:
        _cached_graph = load_graph()
    return _cached_graph


def get_traffic_service():
    """Get or create TrafficService (cached)."""
    global _traffic_service
    if _traffic_service is None:
        _traffic_service = TrafficService(edges_path="data/processed/edges_enriched.csv")
    return _traffic_service


def get_current_hcmc_time():
    """Get current time in HCMC timezone."""
    return datetime.now(HCMC_TZ)


@viz_bp.route("/viz")
def visualization_page():
    """Render the main visualization page."""
    categories = get_categories()
    pois = get_all_pois()
    bounds = get_map_bounds()
    return render_template(
        "visualization.html",
        categories=categories,
        pois=pois,
        bounds=bounds,
        center={"lat": 10.7769, "lon": 106.7009}
    )


@viz_bp.route("/api/map/edges")
def api_map_edges():
    """Get road edges as GeoJSON."""
    sample = request.args.get("sample", type=int)
    geojson = generate_geojson_edges(sample_size=sample)
    return jsonify(geojson)


@viz_bp.route("/api/map/nodes")
def api_map_nodes():
    """Get road nodes as GeoJSON."""
    sample = request.args.get("sample", type=int)
    geojson = generate_geojson_nodes(sample_size=sample)
    return jsonify(geojson)


@viz_bp.route("/api/map/pois")
def api_map_pois():
    """Get POIs as GeoJSON."""
    category = request.args.get("category")
    geojson = generate_geojson_pois()
    if category:
        geojson["features"] = [
            f for f in geojson["features"]
            if f["properties"]["category"] == category
        ]
    return jsonify(geojson)


@viz_bp.route("/api/map/bounds")
def api_map_bounds():
    """Get map bounds."""
    bounds = get_map_bounds()
    return jsonify(bounds)


@viz_bp.route("/api/pois")
def api_pois():
    """Get all POIs for dropdown."""
    pois = get_all_pois()
    return jsonify(pois)


@viz_bp.route(
    "/api/route",
    methods=["POST"]
)
def api_route():
    """Find route between two POIs using realtime traffic data."""

    data = request.get_json()

    start_poi = data.get(
        "start_poi"
    )

    end_poi = data.get(
        "end_poi"
    )

    if not start_poi or not end_poi:
        return jsonify({
            "error":
                "start_poi and end_poi required"
        }), 400

    if start_poi == end_poi:
        return jsonify({
            "error":
                "Start and end POI must be different"
        }), 400

    try:
        graph = get_cached_graph()

        timestamp = (
            get_current_hcmc_time()
        )

        # Reuse the SAME TrafficService instance.
        # This preserves the LIVE cache.
        service = get_traffic_service()

        snapshot = service.get_snapshot(
            timestamp
        )

        result = find_path_between_pois(
            start_poi,
            end_poi,
            graph,
            snapshot,
            timestamp
        )

        if "error" in result:
            return jsonify(
                result
            ), 404

        geojson = (
            generate_route_geojson_with_start_end(
                result,
                graph,
                snapshot
            )
        )

        return jsonify({
            "route_info": result,
            "geojson": geojson
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@viz_bp.route("/api/categories")
def api_categories():
    """Get all POI categories."""
    categories = get_categories()
    return jsonify(categories)


@viz_bp.route("/api/traffic/status")
def api_traffic_status():
    """Get current traffic service status."""
    try:
        service = get_traffic_service()
        timestamp = get_current_hcmc_time()

        # Try to get snapshot to check status
        snapshot = service.get_snapshot(timestamp)

        # Count provenance
        provenance_counts = {}
        for prov in snapshot.provenance.values():
            provenance_counts[prov] = provenance_counts.get(prov, 0) + 1

        # Use snapshot's actual timestamp (preserved from original data capture)
        # For REPLAY mode, this will be the snapshot capture time
        # For LIVE mode, this will be current time
        # For FALLBACK mode, this will be current time
        snapshot_timestamp = snapshot.timestamp

        return jsonify({
            "status": "ok",
            "mode": snapshot.mode,
            "timestamp": snapshot_timestamp,
            "edges_with_speed": len(snapshot.edge_speed),
            "v_bound_kmh": round(snapshot.v_bound, 1),
            "provenance_counts": provenance_counts,
            "fallback_available": True
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": get_current_hcmc_time().isoformat()
        }), 500