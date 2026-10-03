"""Flask routes for the HCMC Traffic A* visualization."""

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
)

viz_bp = Blueprint("visualization", __name__)


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


@viz_bp.route("/api/route", methods=["POST"])
def api_route():
    """Find route between two POIs."""
    data = request.get_json()
    start_poi = data.get("start_poi")
    end_poi = data.get("end_poi")

    if not start_poi or not end_poi:
        return jsonify({"error": "start_poi and end_poi required"}), 400

    if start_poi == end_poi:
        return jsonify({"error": "Start and end POI must be different"}), 400

    result = find_path_between_pois(start_poi, end_poi)

    if "error" in result:
        return jsonify(result), 404

    geojson = generate_route_geojson_with_start_end(result)
    return jsonify({
        "route_info": result,
        "geojson": geojson
    })


@viz_bp.route("/api/categories")
def api_categories():
    """Get all POI categories."""
    categories = get_categories()
    return jsonify(categories)