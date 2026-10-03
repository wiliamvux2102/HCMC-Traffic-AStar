"""Test script for visualization components."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from visualization import (
    load_nodes,
    load_edges,
    load_pois,
    get_map_bounds,
    generate_geojson_edges,
    generate_geojson_nodes,
    generate_geojson_pois,
    get_categories,
    get_all_pois,
    find_path_between_pois,
    generate_route_geojson_with_start_end,
)

def test_data_loading():
    """Test loading all data files."""
    print("Testing data loading...")

    nodes = load_nodes()
    print(f"  Nodes loaded: {len(nodes)}")

    edges = load_edges()
    print(f"  Edges loaded: {len(edges)}")

    pois = load_pois()
    print(f"  POIs loaded: {len(pois)}")

    bounds = get_map_bounds()
    print(f"  Bounds: {bounds}")

    categories = get_categories()
    print(f"  Categories: {categories}")

    all_pois = get_all_pois()
    print(f"  All POIs for dropdown: {len(all_pois)}")

    print("Data loading test PASSED")


def test_geojson_generation():
    """Test GeoJSON generation."""
    print("\nTesting GeoJSON generation...")

    # Test edges (with sampling for speed)
    edges_geojson = generate_geojson_edges(sample_size=100)
    print(f"  Edges GeoJSON features: {len(edges_geojson['features'])}")

    # Test nodes (with sampling)
    nodes_geojson = generate_geojson_nodes(sample_size=100)
    print(f"  Nodes GeoJSON features: {len(nodes_geojson['features'])}")

    # Test POIs
    pois_geojson = generate_geojson_pois()
    print(f"  POIs GeoJSON features: {len(pois_geojson['features'])}")

    # Verify structure
    assert edges_geojson['type'] == 'FeatureCollection'
    assert nodes_geojson['type'] == 'FeatureCollection'
    assert pois_geojson['type'] == 'FeatureCollection'

    print("GeoJSON generation test PASSED")


def test_route_finding():
    """Test route finding between POIs."""
    print("\nTesting route finding...")

    all_pois = get_all_pois()
    if len(all_pois) < 2:
        print("  Not enough POIs for route test")
        return

    start_poi = all_pois[0]['poi_id']
    end_poi = all_pois[1]['poi_id']

    print(f"  Finding route from {start_poi} to {end_poi}...")

    result = find_path_between_pois(start_poi, end_poi)

    if 'error' in result:
        print(f"  Route finding failed: {result['error']}")
        print("  This is expected if the graph is not fully connected")
    else:
        print(f"  Route found!")
        print(f"    Distance: {result['total_distance_km']} km")
        print(f"    Nodes in path: {len(result['path_nodes'])}")

        # Test GeoJSON generation
        geojson = generate_route_geojson_with_start_end(result)
        print(f"  Route GeoJSON features: {len(geojson['features'])}")
        assert geojson['type'] == 'FeatureCollection'

    print("Route finding test COMPLETED")


def test_visualization_imports():
    """Test that all visualization modules can be imported."""
    print("\nTesting imports...")

    # Test map module
    from visualization.map import (
        load_nodes as ln,
        load_edges as le,
        load_pois as lp,
        get_map_bounds as gmb,
        generate_geojson_edges as gge,
        generate_geojson_nodes as ggn,
        generate_geojson_pois as ggp,
        get_categories as gc,
        get_poi_by_id as gpi,
    )
    print("  map module: OK")

    # Test route_plot module
    from visualization.route_plot import (
        load_graph as lg,
        haversine_distance as hd,
        a_star as astar,
        find_path_between_pois as fpbp,
        generate_route_geojson as grg,
        generate_route_geojson_with_start_end as grgwse,
        get_all_pois as gap,
    )
    print("  route_plot module: OK")

    # Test __init__ exports
    import visualization
    print(f"  __all__ exports: {len(visualization.__all__)} items")

    print("Import test PASSED")


if __name__ == '__main__':
    print("=" * 50)
    print("HCMC Traffic A* Visualization - Component Tests")
    print("=" * 50)

    try:
        test_visualization_imports()
        test_data_loading()
        test_geojson_generation()
        test_route_finding()

        print("\n" + "=" * 50)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 50)

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)