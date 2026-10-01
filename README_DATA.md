# Data Pipeline

## 1. Overview

The data pipeline prepares road network and POI data for the HCMC Traffic A* project.

The pipeline consists of:

1. Download road network from OpenStreetMap
2. Download POIs from OpenStreetMap
3. Process and filter POIs
4. Map each POI to the nearest road node
5. Validate POI-to-road-node mapping

---

## 2. Data Sources

### Road Network

Road network data is obtained from OpenStreetMap using OSMnx.

The road network is filtered for drivable roads.

Output:

- `data/raw/osm/hcmc_drive.graphml`
- `data/processed/nodes.csv`
- `data/processed/edges.csv`

Current dataset:

- Nodes: 86,992
- Edges: 200,540

---

### Points of Interest

POI data is obtained from OpenStreetMap.

Raw data:

- 3,786 OSM features
- 2,820 features with names

After category filtering:

- 160 POIs

Categories:

| Category | Count |
|---|---:|
| university | 20 |
| hospital | 20 |
| school | 20 |
| hotel | 20 |
| park | 20 |
| supermarket | 15 |
| mall | 15 |
| tourist_attraction | 10 |
| museum | 10 |
| bus_station | 10 |

---

## 3. POI Processing

The POI processing step:

1. Loads raw OSM POIs
2. Keeps features with names
3. Converts polygon geometries to centroids
4. Reprojects geometries to a projected CRS before centroid calculation
5. Converts the result back to WGS84
6. Assigns normalized POI categories
7. Saves the processed POIs

Output:

`data/processed/pois.csv`

---

## 4. POI to Road Node Mapping

Each POI must be connected to the road network so that the A* algorithm can use POIs as start or destination locations.

The mapping process:

1. Load road nodes
2. Load processed POIs
3. Build a KD-tree using road node coordinates
4. Find the nearest road node for each POI
5. Calculate the POI-to-node distance using the Haversine formula
6. Save the mapping

Output:

`data/processed/poi_node_mapping.csv`

Current result:

- POIs mapped: 160
- Average distance: 71.83 m
- Minimum distance: 2.99 m
- Maximum distance: 1460.82 m

---

## 5. POI Mapping Validation

A POI is considered valid when its nearest road node is within 500 meters.

Current validation:

- Total mapped POIs: 160
- Valid POIs: 159
- Invalid POIs: 1

The invalid POI was:

`POI0037`

Distance to nearest road node:

`1460.82 m`

This POI was excluded from the final dataset.

Output:

`data/processed/poi_final.csv`

Final dataset:

- 159 POIs
- 10 categories

---

## 6. Final Data Used by A*

The A* implementation should use:

### `nodes.csv`

Contains:

- `node_id`
- `longitude`
- `latitude`

### `edges.csv`

Contains:

- `source`
- `target`
- `edge_key`
- `distance`

### `poi_final.csv`

Contains:

- `poi_id`
- `name`
- `category`
- `latitude`
- `longitude`
- `nearest_node`
- `distance_to_node_m`

The `nearest_node` field is used to connect POIs to the road graph.

---

## 7. Running the Pipeline

From the project root:

```bash
python src/data/run_pipeline.py