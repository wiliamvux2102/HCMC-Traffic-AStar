# HCMC Traffic A* Visualization

Interactive web-based visualization for the HCMC Traffic A* project, featuring:
- **Road Network**: 86,992 nodes and 200,540 edges from OpenStreetMap
- **POIs**: 159 Points of Interest across 10 categories
- **A* Route Finding**: Uses the project's existing A* infrastructure with traffic-aware costs
- **Traffic-Aware Route Coloring**: Route segments colored by realtime traffic conditions (red = jammed, blue = normal)
- **Collapsible Dashboard**: Hide/show control panel for full-screen map view

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
3. **Click "Find Route"** - Computes shortest path using the project's A* algorithm with realtime traffic
4. **View Results** - Route displayed with traffic-aware coloring:
   - 🔵 **Blue segments** = Normal traffic flow
   - 🔴 **Red segments** = Traffic jam (speed < 50% of free-flow or < 20 km/h)
5. **Traffic Status Panel** - Shows current traffic mode (LIVE/REPLAY/FALLBACK), max speed, edge count
6. **Toggle Dashboard** - Click the grid icon (or press `Ctrl+D`) to hide/show the control panel
7. **Filter POIs** - Use category filter to show specific POI types
8. **Toggle Layers** - Show/hide road network, nodes, POIs, and route

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
└── route_plot.py       # Route finding using existing Graph, AStar, TrafficSnapshot with traffic coloring
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
    ├── service.py      # TrafficService (LIVE > REPLAY > FALLBACK)
    ├── live_provider.py    # HERE API live traffic
    ├── replay_provider.py  # Replay from saved snapshots
    ├── fallback_provider.py # Time-of-day adjusted speeds
    ├── snapshot.py     # snapshot_from_dataframe()
    ├── models.py       # TrafficSnapshot with v_bound & mode
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
| `/api/traffic/status` | GET | Current traffic service status |

## Features

### Map Layers
- **Road Network**: Color-coded by highway type (major=red, secondary=orange, minor=gray)
- **Road Nodes**: Small circle markers (optional, for debugging)
- **POIs**: Category-colored markers with icons
- **Route**: Segmented line with traffic-aware coloring:
  - 🔵 **Blue (#2a78d6)** = Normal flow (speed ≥ 50% of free-flow AND ≥ 20 km/h)
  - 🔴 **Red (#e34948)** = Traffic jam (speed < 50% of free-flow OR < 20 km/h)
  - 🟢 **Green start marker** / 🔴 **Red end marker**

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

### Traffic-Aware Routing
- **Algorithm**: `src.routing.astar.AStar` class
- **Heuristic**: `travel_time_heuristic` using `v_bound` (max speed in snapshot)
- **Cost Function**: `edge_cost` → `travel_time_seconds` = 3.6 × distance_m / speed_kph
- **Traffic Modes** (priority order):
  1. **LIVE** - Real-time HERE API traffic (requires `HERE_API_KEY` in `.env`)
  2. **REPLAY** - Latest saved snapshot from `data/traffic/snapshots/`
  3. **FALLBACK** - Time-of-day adjusted speeds from `edges_enriched.csv`
- **Jam Detection**: Segment is "jammed" if speed < 50% of free-flow speed OR speed < 20 km/h
- **Performance**: ~170ms for cross-city routes, expands ~14K nodes
- **Returns**: RouteResult with segmented GeoJSON, traffic mode, provenance counts

### Dashboard Controls
- **Collapsible Sidebar**: Click the grid icon (☰) in header or press `Ctrl+D` to toggle
- **Traffic Status Panel**: Shows mode, timestamp, edge count, max speed with color coding
- **Route Finder**: Start/End POI selection with validation
- **Layer Toggles**: Road Network, Road Nodes, POIs, Route
- **POI Category Filter**: Filter POIs by category
- **Route Info Panel**: Distance, time, start/end POI
- **Legend**: Route status, POI categories

## Design System

The visualization uses the **dataviz reference palette** for consistent, accessible colors:
- Validated for colorblind safety (CVD Delta E ≥ 8)
- Light/dark mode support via CSS custom properties
- Semantic color roles (not hardcoded hex values)

### CSS Tokens (in `visualization.css`)
```css
:root {
  --series-1: #2a78d6;   /* blue - route normal */
  --series-2: #eb6834;   /* orange */
  --series-3: #1baf7a;   /* aqua */
  --series-4: #eda100;   /* yellow */
  --series-5: #e87ba4;   /* magenta */
  --series-6: #008300;   /* green - start marker */
  --series-7: #4a3aa7;   /* violet */
  --series-8: #e34948;   /* red - route jammed, hospital */
  --status-good: #0ca30c;      /* green - normal traffic */
  --status-warning: #fab219;   /* yellow */
  --status-serious: #ec835a;   /* orange */
  --status-critical: #d03b3b;  /* red - jammed traffic */
  --route-color: #2a78d6;
  --route-start-color: #0ca30c;
  --route-end-color: #d03b3b;
}
```

## Testing

### Run Component Tests
```bash
python -c "
import sys; sys.path.insert(0, 'src')
from visualization import load_graph, load_traffic_snapshot, find_path_between_pois, generate_route_geojson_with_start_end
graph = load_graph()
snapshot = load_traffic_snapshot(graph)
result = find_path_between_pois('POI0001', 'POI0002', graph, snapshot)
geojson = generate_route_geojson_with_start_end(result, graph, snapshot)
print(f'Features: {len(geojson[\"features\"])}')
jammed = sum(1 for f in geojson['features'] if f['properties'].get('is_jammed'))
print(f'Jammed: {jammed}')
"
```

### Test API Endpoints
```bash
python -c "
from app.app import app
with app.test_client() as client:
    print(client.get('/viz').status_code)
    print(client.get('/api/map/bounds').status_code)
    print(client.get('/api/traffic/status').status_code)
    resp = client.post('/api/route', json={'start_poi':'POI0001','end_poi':'POI0002'})
    print(resp.status_code)
    data = resp.get_json()
    geojson = data['geojson']
    jammed = sum(1 for f in geojson['features'] if f['properties'].get('is_jammed'))
    print(f'Jammed segments: {jammed}')
"
```

### Run Existing Routing Tests
```bash
python -m unittest tests.test_routing -v
```

## Performance Notes

- **Graph Caching**: Graph loaded once at startup
- **Traffic Snapshot**: Fresh snapshot fetched per route request (with 10-min cache for LIVE)
- **Edge sampling**: `/api/map/edges?sample=5000` loads 5K edges (default) instead of 200K
- **Node sampling**: `/api/map/nodes?sample=2000` loads 2K nodes
- **Leaflet Canvas renderer**: Used for better performance with many features
- **Lazy loading**: POIs filtered by category on demand

## Traffic Data Integration

### Traffic Service Priority Chain
The `TrafficService` automatically selects the best available source:
1. **LIVE** - Fetches from HERE API via grid-based queries (requires `HERE_API_KEY` in `.env`)
2. **REPLAY** - Loads latest snapshot from `data/traffic/snapshots/YYYY-MM-DD/HH-MM-SS-complete.csv`
3. **FALLBACK** - Time-of-day adjusted speeds from `edges_enriched.csv` using `free_flow_speed_kph`

### Fallback Speed Model
- Uses `free_flow_speed_kph` from `edges_enriched.csv` (derived from highway type & maxspeed)
- Time-of-day factors:
  - Morning peak (7-9): 55% of free-flow
  - Midday (9-16): 80% of free-flow
  - Evening peak (16-19): 50% of free-flow
  - Evening (19-22): 75% of free-flow
  - Night (22-7): 90% of free-flow
- Minimum speed: 5 km/h

### Replay Snapshots
Pre-recorded traffic snapshots stored in:
```
data/traffic/snapshots/
├── 2026-10-02/16-57-46-complete.csv
└── 2026-10-03/00-44-52-complete.csv
```

Each snapshot contains 200,540 edges with `source,target,edge_key,speed_kph,provenance`.

## Customization

### Add New POI Categories
1. Add color to `CATEGORY_COLORS` in `visualization.js`
2. Add icon to `CATEGORY_ICONS` in `visualization.js`
3. Add label to `CATEGORY_LABELS` in `visualization.js`
4. Add CSS variable in `visualization.css` if needed

### Modify Jam Detection Thresholds
Edit in `src/visualization/route_plot.py`:
```python
# Current thresholds
is_jammed = speed_ratio < 0.5 or current_speed < 20.0
```

### Change Route Colors
Edit CSS variables in `visualization.css`:
```css
--route-color: #2a78d6;      /* normal */
--status-critical: #d03b3b;  /* jammed */
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
| "Incomplete snapshot" error | TrafficService fallback handles this automatically |
| No LIVE traffic | Add `HERE_API_KEY` to `.env` file |
| Dashboard toggle not working | Check browser console for JS errors |

## Data Sources

- **Road Network**: OpenStreetMap via OSMnx (15km radius around HCMC center: 10.7769, 106.7009)
- **POIs**: OpenStreetMap (amenity, tourism, shop, leisure tags)
- **Processing**: KD-Tree nearest node mapping with Haversine validation (≤500m)
- **Traffic**: HERE API (LIVE), saved snapshots (REPLAY), highway-type time-of-day model (FALLBACK)
- **Enriched Edges**: `edges_enriched.csv` with `free_flow_speed_kph`, `highway_normalized`, `edge_id`

## License

Part of the HCMC Traffic A* project.