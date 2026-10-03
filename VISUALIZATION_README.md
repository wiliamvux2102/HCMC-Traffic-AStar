# HCMC Traffic A* Visualization

Interactive web-based visualization for the HCMC Traffic A* project, featuring:
- **Road Network**: 86,992 nodes and 200,540 edges from OpenStreetMap
- **POIs**: 159 Points of Interest across 10 categories
- **A* Route Finding**: Uses the project's existing A* infrastructure with traffic-aware costs

## Quick Start

### 1. Install Dependencies
```bash
cd HCMC-Traffic-AStar
pip install -r requirements.txt
```

### 2. Run the Web App
```bash
python -m app.app
```

The app will start at `http://localhost:5000` (redirects to `/viz`).

### 3. Use the Visualization

1. **Select Start POI** - Choose from 159 POIs in the dropdown
2. **Select End POI** - Choose a different POI
3. **Click "Find Route"** - Computes shortest path using the project's A* algorithm
4. **View Results** - Route displayed on map with distance, time, and node count
5. **Filter POIs** - Use category filter to show specific POI types
6. **Toggle Layers** - Show/hide road network, nodes, POIs, and route

## Architecture

### Backend (Flask)
```
app/
├── app.py              # Flask entry point
├── visualization.py    # API routes for map data & routing
├── templates/
│   └── visualization.html  # Main visualization page
└── static/
    ├── css/visualization.css  # Styling (dataviz palette)
    └── js/visualization.js    # Frontend logic (Leaflet)
```

### Core Visualization Modules (using existing codebase)
```
src/visualization/
├── __init__.py         # Package exports
├── map.py              # Data loading & GeoJSON generation (uses pandas directly)
└── route_plot.py       # Route finding using existing Graph, AStar, TrafficSnapshot
```

### Existing Routing Infrastructure (reused)
```
src/
├── graph/
│   ├── loader.py       # load_graph() - loads nodes, edges, POIs from CSV
│   └── graph.py        # Graph class with nodes, edges, edge_index, POIs
├── routing/
│   ├── astar.py        # AStar class with traffic-aware search
│   ├── heuristic.py    # haversine_distance, travel_time_heuristic
│   ├── cost.py         # edge_cost using traffic.cost.travel_time_seconds
│   └── models.py       # RouteResult dataclass
└── traffic/
    ├── snapshot.py     # snapshot_from_dataframe()
    ├── models.py       # TrafficSnapshot with v_bound
    ├── cost.py         # travel_time_seconds(distance_m, speed_kph)
    └── provider.py     # TrafficProvider ABC
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/viz` | GET | Main visualization page |
| `/api/map/bounds` | GET | Map bounding box |
| `/api/map/edges` | GET | Road edges as GeoJSON (supports `?sample=N`) |
| `/api/map/nodes` | GET | Road nodes as GeoJSON (supports `?sample=N`) |
| `/api/map/pois` | GET | POIs as GeoJSON (supports `?category=X`) |
| `/api/pois` | GET | All POIs for dropdowns |
| `/api/categories` | GET | POI categories list |
| `/api/route` | POST | Find route between POIs (`{start_poi, end_poi}`) |

## Features

### Map Layers
- **Road Network**: Color-coded by highway type (major=red, secondary=orange, minor=gray)
- **Road Nodes**: Small circle markers (optional, for debugging)
- **POIs**: Category-colored markers with icons
- **Route**: Blue line with green start / red end markers

### POI Categories (with colors)
| Category | Color | Icon |
|----------|-------|------|
| University | Blue (#2a78d6) | 🏫 |
| Hospital | Red (#e34948) | 🏥 |
| School | Aqua (#1baf7a) | 🏫 |
| Hotel | Yellow (#eda100) | 🏨 |
| Park | Green (#008300) | 🌳 |
| Supermarket | Magenta (#e87ba4) | 🛒 |
| Mall | Violet (#4a3aa7) | 🏬 |
| Tourist Attraction | Orange (#eb6834) | 🏛️ |
| Museum | Red (#e34948) | 🏛️ |
| Bus Station | Blue (#2a78d6) | 🚌 |

### A* Pathfinding (uses existing implementation)
- **Algorithm**: `src.routing.astar.AStar` class
- **Heuristic**: `travel_time_heuristic` using `v_bound` (max speed in snapshot)
- **Cost Function**: `edge_cost` → `travel_time_seconds` = 3.6 × distance_m / speed_kph
- **Traffic Modes**: LIVE, REPLAY, FALLBACK (default uses maxspeed from edges or highway-type defaults)
- **Performance**: ~170ms for cross-city routes, expands ~14K nodes
- **Returns**: RouteResult with path_nodes, path_edges, total_time_s, total_distance_m, provenance_counts

## Design System

The visualization uses the **dataviz reference palette** for consistent, accessible colors:
- Validated for colorblind safety (CVD Delta E ≥ 8)
- Light/dark mode support via CSS custom properties
- Semantic color roles (not hardcoded hex values)

### CSS Tokens (in `visualization.css`)
```css
:root {
  --series-1: #2a78d6;   /* blue */
  --series-2: #eb6834;   /* orange */
  --series-3: #1baf7a;   /* aqua */
  --series-4: #eda100;   /* yellow */
  --series-5: #e87ba4;   /* magenta */
  --series-6: #008300;   /* green */
  --series-7: #4a3aa7;   /* violet */
  --series-8: #e34948;   /* red */
  --route-color: #2a78d6;
  --route-start-color: #0ca30c;  /* status good */
  --route-end-color: #d03b3b;    /* status critical */
}
```

## Testing

### Run Component Tests
```bash
python test_visualization.py
```

Tests cover:
- Data loading (nodes, edges, POIs)
- GeoJSON generation
- Graph and TrafficSnapshot loading
- Route finding (using existing A*)

### Test API Endpoints
```bash
python -c "
from app.app import app
with app.test_client() as client:
    print(client.get('/viz').status_code)
    print(client.get('/api/map/bounds').status_code)
    print(client.post('/api/route', json={'start_poi':'POI0001','end_poi':'POI0002'}).status_code)
"
```

### Run Existing Routing Tests
```bash
python -m unittest tests.test_routing -v
```

## Performance Notes

- **Graph Caching**: Graph and TrafficSnapshot loaded once at startup
- **Edge sampling**: `/api/map/edges?sample=5000` loads 5K edges (default) instead of 200K
- **Node sampling**: `/api/map/nodes?sample=2000` loads 2K nodes
- **Leaflet Canvas renderer**: Used for better performance with many features
- **Lazy loading**: POIs filtered by category on demand

## Traffic Data Integration

The visualization automatically creates a **fallback traffic snapshot** using:
1. `maxspeed_raw` from edges.csv if available
2. Highway-type defaults (motorway=80, primary=60, tertiary=50, residential=40 km/h)

To use real traffic data:
1. Create `data/processed/traffic_snapshot.csv` with columns: `source, target, edge_key, speed_kph, provenance`
2. The `snapshot_from_dataframe()` function will load it automatically

### Traffic Snapshot Format
```csv
source,target,edge_key,speed_kph,provenance
366224272,4883839119,0,60,replay
366224272,7952136568,0,40,replay
...
```

## Customization

### Add New POI Categories
1. Add color to `CATEGORY_COLORS` in `visualization.js`
2. Add icon to `CATEGORY_ICONS` in `visualization.js`
3. Add label to `CATEGORY_LABELS` in `visualization.js`
4. Add CSS variable in `visualization.css` if needed

### Modify Route Styling
Edit route styles in `visualization.js`:
```javascript
style: {
    color: '#2a78d6',      // route color
    weight: 4,             // line thickness
    opacity: 0.9
}
```

### Change Basemap
In `visualization.js`, replace the tile layer URL:
```javascript
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {...})
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Map not loading | Check browser console for Leaflet load errors |
| Route not found | POIs may not be connected in road graph |
| Slow performance | Reduce `sample` parameter for edges/nodes |
| Dark mode issues | Ensure CSS custom properties are properly defined |
| "Incomplete snapshot" error | Ensure all edges have speeds (fallback handles this) |

## Data Sources

- **Road Network**: OpenStreetMap via OSMnx (15km radius around HCMC center)
- **POIs**: OpenStreetMap (amenity, tourism, shop, leisure tags)
- **Processing**: KD-Tree nearest node mapping with Haversine validation (≤500m)
- **Traffic**: Fallback speeds from edge maxspeed or highway-type defaults

## License

Part of the HCMC Traffic A* project.