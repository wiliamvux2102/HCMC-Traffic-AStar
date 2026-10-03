/**
 * HCMC Traffic A* Visualization - Main JavaScript
 * Interactive map with road network, POIs, and A* routing
 */

(function() {
    'use strict';

    // ============================================================
    // State Management
    // ============================================================

    const state = {
        map: null,
        layers: {
            edges: null,
            nodes: null,
            pois: null,
            route: null
        },
        data: {
            bounds: null,
            center: null,
            categories: [],
            pois: [],
            currentRoute: null
        },
        ui: {
            startPoiSelect: null,
            endPoiSelect: null,
            categorySelect: null,
            findRouteBtn: null,
            clearRouteBtn: null,
            layerToggles: {},
            routeInfo: null,
            routePlaceholder: null,
            legend: null,
            loadingEl: null
        }
    };

    // ============================================================
    // Category Color Mapping (from dataviz palette)
    // ============================================================

    const CATEGORY_COLORS = {
        university: '#2a78d6',
        hospital: '#e34948',
        school: '#1baf7a',
        hotel: '#eda100',
        park: '#008300',
        supermarket: '#e87ba4',
        mall: '#4a3aa7',
        tourist_attraction: '#eb6834',
        museum: '#e34948',
        bus_station: '#2a78d6'
    };

    const CATEGORY_ICONS = {
        university: '🏫',
        hospital: '🏥',
        school: '🏫',
        hotel: '🏨',
        park: '🌳',
        supermarket: '🛒',
        mall: '🏬',
        tourist_attraction: '🏛️',
        museum: '🏛️',
        bus_station: '🚌'
    };

    const CATEGORY_LABELS = {
        university: 'University',
        hospital: 'Hospital',
        school: 'School',
        hotel: 'Hotel',
        park: 'Park',
        supermarket: 'Supermarket',
        mall: 'Mall',
        tourist_attraction: 'Tourist Attraction',
        museum: 'Museum',
        bus_station: 'Bus Station'
    };

    // ============================================================
    // Initialization
    // ============================================================

    document.addEventListener('DOMContentLoaded', async () => {
        initializeUI();
        loadInitialData();
        await initializeMap();
        setupEventListeners();
        populatePOIDropdowns();
        populateCategoryFilter();
        renderLegend();
        hideLoading();
    });

    function initializeUI() {
        state.ui.startPoiSelect = document.getElementById('start-poi');
        state.ui.endPoiSelect = document.getElementById('end-poi');
        state.ui.categorySelect = document.getElementById('poi-category');
        state.ui.findRouteBtn = document.getElementById('find-route-btn');
        state.ui.clearRouteBtn = document.getElementById('clear-route-btn');
        state.ui.routeInfo = document.getElementById('route-info');
        state.ui.routePlaceholder = document.getElementById('route-placeholder');
        state.ui.legend = document.getElementById('legend');
        state.ui.loadingEl = document.getElementById('map-loading');

        state.ui.layerToggles = {
            edges: document.getElementById('layer-edges'),
            nodes: document.getElementById('layer-nodes'),
            pois: document.getElementById('layer-pois'),
            route: document.getElementById('layer-route')
        };
    }

    function loadInitialData() {
        const script = document.getElementById('initial-data');
        if (script) {
            const data = JSON.parse(script.textContent);
            state.data.bounds = data.bounds;
            state.data.center = data.center;
            state.data.categories = data.categories;
            state.data.pois = data.pois;
        }
    }

    // ============================================================
    // Map Initialization (Leaflet)
    // ============================================================

    async function initializeMap() {
        // Load Leaflet dynamically
        await loadLeaflet();

        const center = state.data.center || { lat: 10.7769, lon: 106.7009 };

        state.map = L.map('map', {
            center: [center.lat, center.lon],
            zoom: 13,
            zoomControl: true,
            attributionControl: true,
            preferCanvas: true // Better performance for many features
        });

        // Add basemap (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(state.map);

        // Fit to bounds if available
        if (state.data.bounds) {
            const bounds = state.data.bounds;
            state.map.fitBounds([
                [bounds.min_lat, bounds.min_lon],
                [bounds.max_lat, bounds.max_lon]
            ], { padding: [20, 20] });
        }

        // Load map layers
        await loadEdgesLayer();
        await loadNodesLayer();
        await loadPOIsLayer();

        // Initialize empty route layer
        state.layers.route = L.featureGroup().addTo(state.map);
    }

    function loadLeaflet() {
        return new Promise((resolve, reject) => {
            if (window.L) {
                resolve();
                return;
            }

            // Load Leaflet CSS
            const cssLink = document.createElement('link');
            cssLink.rel = 'stylesheet';
            cssLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css';
            cssLink.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
            cssLink.crossOrigin = 'anonymous';
            document.head.appendChild(cssLink);

            // Load Leaflet JS
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js';
            script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
            script.crossOrigin = 'anonymous';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    // ============================================================
    // Layer Loading
    // ============================================================

    async function loadEdgesLayer(sampleSize = 5000) {
        try {
            const response = await fetch(`/api/map/edges?sample=${sampleSize}`);
            const geojson = await response.json();

            state.layers.edges = L.geoJSON(geojson, {
                style: (feature) => ({
                    color: feature.properties.color || '#898781',
                    weight: feature.properties.weight || 1,
                    opacity: 0.7,
                    lineCap: 'round',
                    lineJoin: 'round'
                }),
                onEachFeature: (feature, layer) => {
                    const props = feature.properties;
                    layer.bindPopup(createEdgePopup(props));
                }
            }).addTo(state.map);

            updateLayerVisibility('edges', true);
        } catch (error) {
            console.error('Failed to load edges:', error);
        }
    }

    async function loadNodesLayer(sampleSize = 2000) {
        try {
            const response = await fetch(`/api/map/nodes?sample=${sampleSize}`);
            const geojson = await response.json();

            state.layers.nodes = L.geoJSON(geojson, {
                pointToLayer: (feature, latlng) => {
                    return L.circleMarker(latlng, {
                        radius: 2,
                        fillColor: '#898781',
                        color: '#ffffff',
                        weight: 1,
                        opacity: 0.8,
                        fillOpacity: 0.6
                    });
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`Node ID: ${feature.properties.node_id}`);
                }
            });

            updateLayerVisibility('nodes', false);
        } catch (error) {
            console.error('Failed to load nodes:', error);
        }
    }

    async function loadPOIsLayer(category = null) {
        try {
            const url = category ? `/api/map/pois?category=${category}` : '/api/map/pois';
            const response = await fetch(url);
            const geojson = await response.json();

            // Remove existing POI layer
            if (state.layers.pois) {
                state.map.removeLayer(state.layers.pois);
            }

            state.layers.pois = L.geoJSON(geojson, {
                pointToLayer: (feature, latlng) => {
                    const props = feature.properties;
                    const color = props.color || '#898781';
                    const icon = props.icon || '📍';

                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'poi-marker',
                            html: `<div class="poi-marker-icon" style="background: ${color}; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">${icon}</div>`,
                            iconSize: [28, 28],
                            iconAnchor: [14, 14]
                        })
                    });
                },
                onEachFeature: (feature, layer) => {
                    const props = feature.properties;
                    layer.bindPopup(createPOIPopup(props));
                }
            }).addTo(state.map);

            updateLayerVisibility('pois', true);
        } catch (error) {
            console.error('Failed to load POIs:', error);
        }
    }

    // ============================================================
    // Popup Content Creators
    // ============================================================

    function createEdgePopup(props) {
        const highway = props.highway || 'unknown';
        const distance = props.distance_m ? `${Math.round(props.distance_m)} m` : 'N/A';
        const oneway = props.oneway ? 'Yes' : 'No';

        return `
            <div class="popup-content">
                <strong>Road Segment</strong>
                <table class="popup-table">
                    <tr><th>Type</th><td>${highway}</td></tr>
                    <tr><th>Distance</th><td>${distance}</td></tr>
                    <tr><th>One-way</th><td>${oneway}</td></tr>
                    <tr><th>Source</th><td>${props.source}</td></tr>
                    <tr><th>Target</th><td>${props.target}</td></tr>
                </table>
            </div>
        `;
    }

    function createPOIPopup(props) {
        const categoryLabel = CATEGORY_LABELS[props.category] || props.category;
        const distance = props.distance_to_node_m ? `${Math.round(props.distance_to_node_m)} m` : 'N/A';

        return `
            <div class="popup-content">
                <strong>${escapeHtml(props.name)}</strong>
                <table class="popup-table">
                    <tr><th>Category</th><td><span class="category-badge" style="background: ${props.color}">${categoryLabel}</span></td></tr>
                    <tr><th>POI ID</th><td>${props.poi_id}</td></tr>
                    <tr><th>Nearest Node</th><td>${props.nearest_node || 'N/A'}</td></tr>
                    <tr><th>Distance to Node</th><td>${distance}</td></tr>
                </table>
            </div>
        `;
    }

    function createRoutePopup(props) {
        const distance = props.distance_km ? `${props.distance_km} km` : 'N/A';

        return `
            <div class="popup-content">
                <strong>Route</strong>
                <table class="popup-table">
                    <tr><th>From</th><td>${escapeHtml(props.start_poi)}</td></tr>
                    <tr><th>To</th><td>${escapeHtml(props.end_poi)}</td></tr>
                    <tr><th>Distance</th><td>${distance}</td></tr>
                    <tr><th>Nodes</th><td>${props.path_nodes ? props.path_nodes.length : 'N/A'}</td></tr>
                </table>
            </div>
        `;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ============================================================
    // Route Finding
    // ============================================================

    async function findRoute() {
        const startPoi = state.ui.startPoiSelect.value;
        const endPoi = state.ui.endPoiSelect.value;

        if (!startPoi || !endPoi) {
            alert('Please select both start and end POIs');
            return;
        }

        if (startPoi === endPoi) {
            alert('Start and end POI must be different');
            return;
        }

        setLoadingState(true);

        try {
            const response = await fetch('/api/route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start_poi: startPoi, end_poi: endPoi })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to find route');
            }

            displayRoute(result.geojson, result.route_info);
            showRouteInfo(result.route_info);
            state.ui.clearRouteBtn.hidden = false;

        } catch (error) {
            console.error('Route finding error:', error);
            alert(`Error finding route: ${error.message}`);
        } finally {
            setLoadingState(false);
        }
    }

    function displayRoute(geojson, routeInfo) {
        // Clear existing route
        if (state.layers.route) {
            state.layers.route.clearLayers();
        }

        // Add route line
        const routeFeature = geojson.features.find(f => f.properties.type === 'route');
        if (routeFeature) {
            const routeLayer = L.geoJSON(routeFeature, {
                style: {
                    color: '#2a78d6',
                    weight: 4,
                    opacity: 0.9,
                    lineCap: 'round',
                    lineJoin: 'round',
                    className: 'route-line'
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(createRoutePopup(feature.properties));
                }
            });
            state.layers.route.addLayer(routeLayer);
        }

        // Add start marker
        const startFeature = geojson.features.find(f => f.properties.type === 'start');
        if (startFeature) {
            const startLayer = L.geoJSON(startFeature, {
                pointToLayer: (feature, latlng) => {
                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'route-marker',
                            html: `<div class="route-marker-icon start" style="width: 24px; height: 24px; border-radius: 50%; border: 3px solid var(--surface-3); background: #0ca30c; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>`,
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        })
                    });
                }
            });
            state.layers.route.addLayer(startLayer);
        }

        // Add end marker
        const endFeature = geojson.features.find(f => f.properties.type === 'end');
        if (endFeature) {
            const endLayer = L.geoJSON(endFeature, {
                pointToLayer: (feature, latlng) => {
                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'route-marker',
                            html: `<div class="route-marker-icon end" style="width: 24px; height: 24px; border-radius: 50%; border: 3px solid var(--surface-3); background: #d03b3b; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>`,
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        })
                    });
                }
            });
            state.layers.route.addLayer(endLayer);
        }

        // Fit map to route
        if (state.layers.route.getLayers().length > 0) {
            const bounds = state.layers.route.getBounds();
            state.map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
        }

        updateLayerVisibility('route', true);
        state.data.currentRoute = routeInfo;
    }

    function clearRoute() {
        if (state.layers.route) {
            state.layers.route.clearLayers();
        }
        state.data.currentRoute = null;
        state.ui.routeInfo.hidden = true;
        state.ui.routePlaceholder.hidden = false;
        state.ui.clearRouteBtn.hidden = true;
        updateLayerVisibility('route', false);
    }

    function showRouteInfo(info) {
        document.getElementById('route-distance').textContent = `${info.total_distance_km} km`;
        document.getElementById('route-nodes').textContent = info.path_nodes ? info.path_nodes.length : '—';
        document.getElementById('route-start').textContent = info.start_poi;
        document.getElementById('route-end').textContent = info.end_poi;

        state.ui.routeInfo.hidden = false;
        state.ui.routePlaceholder.hidden = true;
    }

    function setLoadingState(loading) {
        state.ui.findRouteBtn.disabled = loading;
        state.ui.findRouteBtn.querySelector('.btn-text').hidden = loading;
        state.ui.findRouteBtn.querySelector('.btn-loading').hidden = !loading;
    }

    function hideLoading() {
        if (state.ui.loadingEl) {
            state.ui.loadingEl.classList.add('hidden');
        }
    }

    // ============================================================
    // UI Population
    // ============================================================

    function populatePOIDropdowns() {
        const pois = state.data.pois;

        [state.ui.startPoiSelect, state.ui.endPoiSelect].forEach(select => {
            // Clear existing options except first
            while (select.options.length > 1) {
                select.remove(1);
            }

            pois.forEach(poi => {
                const option = document.createElement('option');
                option.value = poi.poi_id;
                option.textContent = `${poi.poi_id} - ${poi.name} (${CATEGORY_LABELS[poi.category] || poi.category})`;
                select.appendChild(option);
            });
        });

        updateRouteButtonState();
    }

    function populateCategoryFilter() {
        const select = state.ui.categorySelect;
        state.data.categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = CATEGORY_LABELS[cat] || cat;
            select.appendChild(option);
        });
    }

    function renderLegend() {
        const legend = state.ui.legend;
        legend.innerHTML = '';

        // Route legend items
        const routeItems = [
            { label: 'Route', color: '#2a78d6', class: 'route' },
            { label: 'Start', color: '#0ca30c', class: 'start' },
            { label: 'End', color: '#d03b3b', class: 'end' }
        ];

        routeItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'legend-item';
            div.innerHTML = `
                <span class="legend-swatch ${item.class}" style="background: ${item.color}"></span>
                <span>${item.label}</span>
            `;
            legend.appendChild(div);
        });

        // Category legend items (only those present in data)
        const presentCategories = [...new Set(state.data.pois.map(p => p.category))];
        presentCategories.forEach(cat => {
            const color = CATEGORY_COLORS[cat] || '#898781';
            const label = CATEGORY_LABELS[cat] || cat;

            const div = document.createElement('div');
            div.className = 'legend-item';
            div.innerHTML = `
                <span class="legend-swatch" style="background: ${color}; border-radius: 50%"></span>
                <span>${label}</span>
            `;
            legend.appendChild(div);
        });
    }

    // ============================================================
    // Layer Visibility
    // ============================================================

    function updateLayerVisibility(layerName, visible) {
        const layer = state.layers[layerName];
        const toggle = state.ui.layerToggles[layerName];

        if (layer && toggle) {
            if (visible) {
                if (!state.map.hasLayer(layer)) {
                    state.map.addLayer(layer);
                }
            } else {
                if (state.map.hasLayer(layer)) {
                    state.map.removeLayer(layer);
                }
            }
            toggle.checked = visible;
        }
    }

    // ============================================================
    // Event Listeners
    // ============================================================

    function setupEventListeners() {
        // Route finding
        state.ui.findRouteBtn.addEventListener('click', findRoute);
        state.ui.clearRouteBtn.addEventListener('click', clearRoute);

        // POI selection changes
        state.ui.startPoiSelect.addEventListener('change', updateRouteButtonState);
        state.ui.endPoiSelect.addEventListener('change', updateRouteButtonState);

        // Category filter
        state.ui.categorySelect.addEventListener('change', (e) => {
            loadPOIsLayer(e.target.value || null);
        });

        // Layer toggles
        Object.entries(state.ui.layerToggles).forEach(([name, toggle]) => {
            toggle.addEventListener('change', (e) => {
                updateLayerVisibility(name, e.target.checked);
            });
        });

        // Prevent same POI selection
        [state.ui.startPoiSelect, state.ui.endPoiSelect].forEach(select => {
            select.addEventListener('change', () => {
                const otherSelect = select === state.ui.startPoiSelect ? state.ui.endPoiSelect : state.ui.startPoiSelect;
                const selectedValue = select.value;

                // Disable the selected option in the other dropdown
                Array.from(otherSelect.options).forEach(opt => {
                    opt.disabled = opt.value === selectedValue && opt.value !== '';
                });

                // If other select has the now-disabled value, clear it
                if (otherSelect.value === selectedValue) {
                    otherSelect.value = '';
                }

                updateRouteButtonState();
            });
        });
    }

    function updateRouteButtonState() {
        const hasStart = state.ui.startPoiSelect.value !== '';
        const hasEnd = state.ui.endPoiSelect.value !== '';
        const different = hasStart && hasEnd && state.ui.startPoiSelect.value !== state.ui.endPoiSelect.value;

        state.ui.findRouteBtn.disabled = !different;
    }

})();