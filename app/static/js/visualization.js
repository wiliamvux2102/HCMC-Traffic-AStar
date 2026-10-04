/**
 * HCMC Traffic A* Visualization - Google Maps Theme JavaScript
 * Interactive map with road network, POIs, realtime traffic, and A* routing
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
            swapPoiBtn: null,
            categorySelect: null,
            findRouteBtn: null,
            clearRouteBtn: null,
            layerToggles: {},
            routeInfo: null,
            routePlaceholder: null,
            routeTimeVal: null,
            routeTrafficLabel: null,
            routeTrafficBar: null,
            routeDistance: null,
            routeNodes: null,
            routeStart: null,
            routeEnd: null,
            routeModeBadge: null,
            legend: null,
            loadingEl: null,
            sidebarWrapper: null,
            controlsPanel: null,
            panelToggle: null,
            trafficModeEl: null,
            trafficTimestampEl: null,
            trafficEdgesEl: null,
            trafficVBoundEl: null,
            refreshTrafficBtn: null,
            headerTrafficBadge: null,
            headerTrafficText: null
        }
    };

    // ============================================================
    // Category Colors (Google Maps / Material Palette)
    // ============================================================

    const CATEGORY_COLORS = {
        university: '#1a73e8',          // Blue
        hospital: '#d93025',            // Red
        school: '#00838f',              // Cyan / Teal
        hotel: '#f29900',               // Amber
        park: '#188038',                // Green
        supermarket: '#e37400',         // Orange
        mall: '#9334e6',                // Purple
        tourist_attraction: '#e52592',   // Pink / Magenta
        museum: '#d93025',              // Brick Red
        bus_station: '#1a73e8'          // Transit Blue
    };

    const CATEGORY_ICONS = {
        university: '🎓',
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
        mall: 'Shopping Mall',
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
        await loadTrafficStatus();
        hideLoading();
    });

    function initializeUI() {
        state.ui.startPoiSelect = document.getElementById('start-poi');
        state.ui.endPoiSelect = document.getElementById('end-poi');
        state.ui.swapPoiBtn = document.getElementById('swap-poi-btn');
        state.ui.categorySelect = document.getElementById('poi-category');
        state.ui.findRouteBtn = document.getElementById('find-route-btn');
        state.ui.clearRouteBtn = document.getElementById('clear-route-btn');
        state.ui.routeInfo = document.getElementById('route-info');
        state.ui.routePlaceholder = document.getElementById('route-placeholder');
        state.ui.routeTimeVal = document.getElementById('route-time-val');
        state.ui.routeTrafficLabel = document.getElementById('route-traffic-label');
        state.ui.routeTrafficBar = document.getElementById('route-traffic-bar');
        state.ui.routeDistance = document.getElementById('route-distance');
        state.ui.routeNodes = document.getElementById('route-nodes');
        state.ui.routeStart = document.getElementById('route-start');
        state.ui.routeEnd = document.getElementById('route-end');
        state.ui.routeModeBadge = document.getElementById('route-mode-badge');
        state.ui.legend = document.getElementById('legend');
        state.ui.loadingEl = document.getElementById('map-loading');

        state.ui.layerToggles = {
            edges: document.getElementById('layer-edges'),
            nodes: document.getElementById('layer-nodes'),
            pois: document.getElementById('layer-pois'),
            route: document.getElementById('layer-route')
        };

        // Sidebar & Panel elements
        state.ui.sidebarWrapper = document.getElementById('sidebar-wrapper');
        state.ui.controlsPanel = document.querySelector('.controls-panel');
        state.ui.panelToggle = document.getElementById('panel-toggle');

        // Traffic status elements
        state.ui.trafficModeEl = document.getElementById('traffic-mode');
        state.ui.trafficTimestampEl = document.getElementById('traffic-timestamp');
        state.ui.trafficEdgesEl = document.getElementById('traffic-edges');
        state.ui.trafficVBoundEl = document.getElementById('traffic-vbound');
        state.ui.refreshTrafficBtn = document.getElementById('refresh-traffic-btn');
        state.ui.headerTrafficBadge = document.getElementById('header-traffic-badge');
        state.ui.headerTrafficText = document.getElementById('header-traffic-text');
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
    // Map Initialization (Leaflet with Google Maps style controls)
    // ============================================================

    async function initializeMap() {
        await loadLeaflet();

        const center = state.data.center || { lat: 10.7769, lon: 106.7009 };

        state.map = L.map('map', {
            center: [center.lat, center.lon],
            zoom: 13,
            zoomControl: false, // Positioned at bottomright like Google Maps
            attributionControl: true,
            preferCanvas: true
        });

        // Add Google Maps style bottom-right zoom control
        L.control.zoom({ position: 'bottomright' }).addTo(state.map);

        // Add OpenStreetMap tile layer with neutral look
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
            ], { padding: [30, 30] });
        }

        // Initialize layers (Roads & Nodes hidden by default, POIs shown)
        await loadEdgesLayer();
        await loadNodesLayer();
        await loadPOIsLayer();

        state.layers.route = L.featureGroup().addTo(state.map);
    }

    function loadLeaflet() {
        return new Promise((resolve, reject) => {
            if (window.L) {
                resolve();
                return;
            }

            const cssLink = document.createElement('link');
            cssLink.rel = 'stylesheet';
            cssLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css';
            cssLink.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
            cssLink.crossOrigin = 'anonymous';
            document.head.appendChild(cssLink);

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

    async function loadEdgesLayer(sampleSize = null) {
        try {
            const response = await fetch(`/api/map/edges?sample=${sampleSize}`);
            const geojson = await response.json();

            state.layers.edges = L.geoJSON(geojson, {
                style: (feature) => ({
                    color: feature.properties.color || '#9aa0a6',
                    weight: feature.properties.weight || 1.2,
                    opacity: 0.65,
                    lineCap: 'round',
                    lineJoin: 'round'
                }),
                onEachFeature: (feature, layer) => {
                    const props = feature.properties;
                    layer.bindPopup(createEdgePopup(props));
                }
            });

            // Turned off by default as requested
            updateLayerVisibility('edges', false);
        } catch (error) {
            console.error('Failed to load edges:', error);
        }
    }

    async function loadNodesLayer(sampleSize = null) {
        try {
            const response = await fetch(`/api/map/nodes?sample=${sampleSize}`);
            const geojson = await response.json();

            state.layers.nodes = L.geoJSON(geojson, {
                pointToLayer: (feature, latlng) => {
                    return L.circleMarker(latlng, {
                        radius: 2.5,
                        fillColor: '#1a73e8',
                        color: '#ffffff',
                        weight: 1,
                        opacity: 0.8,
                        fillOpacity: 0.6
                    });
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(`<div class="popup-title">Road Node</div>Node ID: ${feature.properties.node_id}`);
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

            if (state.layers.pois) {
                state.map.removeLayer(state.layers.pois);
            }

            state.layers.pois = L.geoJSON(geojson, {
                pointToLayer: (feature, latlng) => {
                    const props = feature.properties;
                    const color = props.color || '#1a73e8';
                    const icon = props.icon || '📍';

                    return L.marker(latlng, {
                        icon: L.divIcon({
                            className: 'poi-marker',
                            html: `<div class="gm-poi-pin" style="--pin-color: ${color};" title="${escapeHtml(props.name)}">
                                <span>${icon}</span>
                            </div>`,
                            iconSize: [26, 26],
                            iconAnchor: [13, 13]
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
    // Popups (Google Maps Style)
    // ============================================================

    function createEdgePopup(props) {
        const highway = props.highway || 'unknown';
        const distance = props.distance_m ? `${Math.round(props.distance_m)} m` : 'N/A';
        const oneway = props.oneway ? 'Yes' : 'No';

        return `
            <div class="popup-title">Road Segment</div>
            <table class="popup-table">
                <tr><th>Highway Type</th><td>${highway}</td></tr>
                <tr><th>Length</th><td>${distance}</td></tr>
                <tr><th>One-way</th><td>${oneway}</td></tr>
                <tr><th>Edge Key</th><td>(${props.source} → ${props.target}, ${props.edge_key || 0})</td></tr>
            </table>
        `;
    }

    function createPOIPopup(props) {
        const categoryLabel = CATEGORY_LABELS[props.category] || props.category;
        const distance = props.distance_to_node_m ? `${Math.round(props.distance_to_node_m)} m` : 'N/A';

        return `
            <div class="popup-title">${escapeHtml(props.name)}</div>
            <span class="popup-badge" style="background: ${props.color}20; color: ${props.color};">${categoryLabel}</span>
            <table class="popup-table">
                <tr><th>POI ID</th><td>${props.poi_id}</td></tr>
                <tr><th>Nearest Node</th><td>${props.nearest_node || 'N/A'}</td></tr>
                <tr><th>Offset Distance</th><td>${distance}</td></tr>
            </table>
        `;
    }

    function createRoutePopup(props) {
        const distance = props.distance_km ? `${props.distance_km} km` : 'N/A';
        const time = props.time_min ? `${props.time_min} min` : 'N/A';

        return `
            <div class="popup-title">Trip Route</div>
            <table class="popup-table">
                <tr><th>Estimated Time</th><td><strong>${time}</strong></td></tr>
                <tr><th>Total Distance</th><td>${distance}</td></tr>
                <tr><th>Intersections</th><td>${props.path_nodes ? props.path_nodes.length : 'N/A'}</td></tr>
            </table>
        `;
    }

    function createRouteSegmentPopup(props) {
        const isJammed = props.is_jammed;
        const statusLabel = isJammed ? 'Heavy Traffic (Jam)' : 'Normal Flow';
        const statusColor = isJammed ? '#d93025' : '#188038';

        return `
            <div class="popup-title" style="color: ${statusColor};">
                ${isJammed ? '🔴 ' : '🟢 '} ${statusLabel}
            </div>
            <table class="popup-table">
                <tr><th>Current Speed</th><td><strong>${props.current_speed_kph} km/h</strong></td></tr>
                <tr><th>Free-Flow Speed</th><td>${props.free_flow_speed_kph} km/h</td></tr>
                <tr><th>Flow Capacity</th><td>${(props.speed_ratio * 100).toFixed(0)}%</td></tr>
                <tr><th>Segment #</th><td>${props.segment_index + 1}</td></tr>
            </table>
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
            alert('Please select both start and destination locations');
            return;
        }

        if (startPoi === endPoi) {
            alert('Start and destination must be different locations');
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
            showRouteInfo(result.route_info, result.geojson);
            state.ui.clearRouteBtn.hidden = false;

        } catch (error) {
            console.error('Route finding error:', error);
            alert(`Error finding route: ${error.message}`);
        } finally {
            setLoadingState(false);
        }
    }

    function displayRoute(geojson, routeInfo) {
        if (state.layers.route) {
            state.layers.route.clearLayers();
        }

        let jammedSegmentsCount = 0;
        let totalSegmentsCount = 0;

        if (geojson.type === 'FeatureCollection') {
            // First pass: Add route casing line for Google Maps contrast
            geojson.features.forEach(feature => {
                const props = feature.properties;
                if (props.type === 'route_segment') {
                    totalSegmentsCount++;
                    if (props.is_jammed) jammedSegmentsCount++;

                    // White / dark casing underneath
                    const casingLayer = L.geoJSON(feature, {
                        style: {
                            color: '#ffffff',
                            weight: 7,
                            opacity: 0.9,
                            lineCap: 'round',
                            lineJoin: 'round'
                        },
                        interactive: false
                    });
                    state.layers.route.addLayer(casingLayer);

                    // Main colored line (Blue or Red)
                    const segmentLayer = L.geoJSON(feature, {
                        style: {
                            color: props.color || (props.is_jammed ? '#d93025' : '#1a73e8'),
                            weight: 4.5,
                            opacity: 0.95,
                            lineCap: 'round',
                            lineJoin: 'round'
                        },
                        onEachFeature: (feature, layer) => {
                            layer.bindPopup(createRouteSegmentPopup(feature.properties));
                        }
                    });
                    state.layers.route.addLayer(segmentLayer);
                }
            });

            // Second pass: Start & Destination Markers
            geojson.features.forEach(feature => {
                const props = feature.properties;
                if (props.type === 'start') {
                    const startLayer = L.geoJSON(feature, {
                        pointToLayer: (feature, latlng) => {
                            return L.marker(latlng, {
                                icon: L.divIcon({
                                    className: 'route-marker',
                                    html: `<div class="gm-pin-start" title="Starting Location">
                                        <span class="gm-pin-ring"></span>
                                    </div>`,
                                    iconSize: [22, 22],
                                    iconAnchor: [11, 11]
                                }),
                                zIndexOffset: 1000
                            });
                        }
                    });
                    state.layers.route.addLayer(startLayer);
                } else if (props.type === 'end') {
                    const endLayer = L.geoJSON(feature, {
                        pointToLayer: (feature, latlng) => {
                            return L.marker(latlng, {
                                icon: L.divIcon({
                                    className: 'route-marker',
                                    html: `<div class="gm-pin-destination" title="Destination">
                                        <svg width="28" height="34" viewBox="0 0 24 30" fill="none">
                                            <path d="M12 0C5.37 0 0 5.37 0 12c0 9 12 18 12 18s12-9 12-18c0-6.63-5.37-12-12-12z" fill="#EA4335"/>
                                            <circle cx="12" cy="11" r="4.5" fill="#FFFFFF"/>
                                            <circle cx="12" cy="11" r="2.2" fill="#B31412"/>
                                        </svg>
                                    </div>`,
                                    iconSize: [28, 34],
                                    iconAnchor: [14, 32]
                                }),
                                zIndexOffset: 1001
                            });
                        }
                    });
                    state.layers.route.addLayer(endLayer);
                }
            });
        } else if (geojson.type === 'Feature') {
            const routeLayer = L.geoJSON(geojson, {
                style: {
                    color: '#1a73e8',
                    weight: 5,
                    opacity: 0.95,
                    lineCap: 'round',
                    lineJoin: 'round'
                },
                onEachFeature: (feature, layer) => {
                    layer.bindPopup(createRoutePopup(feature.properties));
                }
            });
            state.layers.route.addLayer(routeLayer);
        }

        // Fit map to route bounds
        if (state.layers.route.getLayers().length > 0) {
            const bounds = state.layers.route.getBounds();
            state.map.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 });
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

    function showRouteInfo(info, geojson) {
        // Calculate jammed percentage
        let jammedCount = 0;
        let totalCount = 0;

        if (geojson && geojson.features) {
            geojson.features.forEach(f => {
                if (f.properties && f.properties.type === 'route_segment') {
                    totalCount++;
                    if (f.properties.is_jammed) jammedCount++;
                }
            });
        }

        const hasJam = jammedCount > 0;
        const normalCount = Math.max(0, totalCount - jammedCount);
        const normalPct = totalCount > 0 ? (normalCount / totalCount * 100) : 100;
        const jammedPct = 100 - normalPct;

        // Big Travel Time hero
        if (state.ui.routeTimeVal) {
            state.ui.routeTimeVal.textContent = `${info.total_time_min} min`;
            state.ui.routeTimeVal.className = `route-duration ${hasJam ? 'jammed' : 'normal'}`;
        }

        // Traffic status label
        if (state.ui.routeTrafficLabel) {
            state.ui.routeTrafficLabel.textContent = hasJam
                ? `Slowdowns (${jammedCount} ${jammedCount === 1 ? 'jam' : 'jams'})`
                : 'Fastest route now';
            state.ui.routeTrafficLabel.className = `route-status-pill ${hasJam ? 'jammed' : 'normal'}`;
        }

        // Google Maps traffic progress bar
        if (state.ui.routeTrafficBar) {
            state.ui.routeTrafficBar.innerHTML = `
                <div class="traffic-segment normal" style="width: ${normalPct}%;"></div>
                <div class="traffic-segment jammed" style="width: ${jammedPct}%;"></div>
            `;
        }

        // Stats
        if (state.ui.routeDistance) {
            state.ui.routeDistance.textContent = `${info.total_distance_km} km`;
        }
        if (state.ui.routeNodes) {
            state.ui.routeNodes.textContent = `${info.path_nodes ? info.path_nodes.length : 0} nodes`;
        }
        if (state.ui.routeModeBadge) {
            state.ui.routeModeBadge.textContent = `${info.traffic_mode || 'LIVE'} A*`;
        }

        // Step endpoints
        if (state.ui.routeStart) state.ui.routeStart.textContent = info.start_poi;
        if (state.ui.routeEnd) state.ui.routeEnd.textContent = info.end_poi;

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
    // Traffic Status
    // ============================================================

    async function loadTrafficStatus() {
        try {
            const response = await fetch('/api/traffic/status');
            const data = await response.json();

            if (data.status === 'ok') {
                const mode = data.mode || 'LIVE';
                state.ui.trafficModeEl.textContent = mode;
                state.ui.trafficModeEl.className = 'cell-value pill-mode';

                state.ui.trafficTimestampEl.textContent = formatTimestamp(data.timestamp);
                state.ui.trafficEdgesEl.textContent = data.edges_with_speed ? data.edges_with_speed.toLocaleString() : '200,540';
                state.ui.trafficVBoundEl.textContent = data.v_bound_kmh ? `${data.v_bound_kmh} km/h` : '72 km/h';

                // Update Header Live Badge
                if (state.ui.headerTrafficBadge && state.ui.headerTrafficText) {
                    state.ui.headerTrafficBadge.className = `traffic-mode-badge mode-${mode.toLowerCase()}`;
                    if (mode === 'LIVE') {
                        state.ui.headerTrafficText.textContent = 'Live Traffic Feed';
                    } else if (mode === 'REPLAY') {
                        state.ui.headerTrafficText.textContent = 'Replay Traffic';
                    } else {
                        state.ui.headerTrafficText.textContent = 'Fallback Model';
                    }
                }
            } else {
                setTrafficStatusError();
            }
        } catch (error) {
            console.error('Failed to load traffic status:', error);
            setTrafficStatusError();
        }
    }

    function setTrafficStatusError() {
        if (state.ui.trafficModeEl) state.ui.trafficModeEl.textContent = 'Offline';
        if (state.ui.headerTrafficBadge) {
            state.ui.headerTrafficBadge.className = 'traffic-mode-badge mode-fallback';
            state.ui.headerTrafficText.textContent = 'Offline / Fallback';
        }
    }

    function formatTimestamp(isoString) {
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return isoString;
        }
    }

    // ============================================================
    // Sidebar Panel Toggle (Google Maps Style)
    // ============================================================

    function toggleDashboard() {
        const sidebar = state.ui.sidebarWrapper || document.getElementById('sidebar-wrapper') || state.ui.controlsPanel;
        const toggle = state.ui.panelToggle;

        if (!sidebar || !toggle) return;

        const isHidden = sidebar.classList.toggle('hidden');
        toggle.setAttribute('aria-expanded', !isHidden);
        toggle.title = isHidden ? 'Expand side panel (Ctrl+D)' : 'Collapse side panel (Ctrl+D)';

        // Fluid Leaflet resize during 350ms slide animation
        const startTime = performance.now();
        const duration = 380; // ms

        function step(currentTime) {
            if (state.map) {
                state.map.invalidateSize({ pan: false });
            }
            if (currentTime - startTime < duration) {
                requestAnimationFrame(step);
            } else if (state.map) {
                state.map.invalidateSize();
            }
        }
        requestAnimationFrame(step);
    }

    // ============================================================
    // UI Population
    // ============================================================

    function populatePOIDropdowns() {
        const pois = state.data.pois;

        [state.ui.startPoiSelect, state.ui.endPoiSelect].forEach(select => {
            while (select.options.length > 1) {
                select.remove(1);
            }

            pois.forEach(poi => {
                const option = document.createElement('option');
                option.value = poi.poi_id;
                const catLabel = CATEGORY_LABELS[poi.category] || poi.category;
                option.textContent = `${poi.name} (${catLabel})`;
                select.appendChild(option);
            });
        });

        updateRouteButtonState();
    }

    function swapPOIs() {
        const startVal = state.ui.startPoiSelect.value;
        const endVal = state.ui.endPoiSelect.value;

        state.ui.startPoiSelect.value = endVal;
        state.ui.endPoiSelect.value = startVal;

        updateRouteButtonState();

        if (startVal && endVal) {
            findRoute();
        }
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

        const items = [
            { label: 'Normal Traffic', color: '#1a73e8', class: 'normal' },
            { label: 'Heavy Jam', color: '#d93025', class: 'jammed' },
            { label: 'Origin Point', color: '#188038', class: 'start' },
            { label: 'Destination', color: '#ea4335', class: 'end' }
        ];

        // Also add top 4 present categories
        const presentCategories = [...new Set(state.data.pois.map(p => p.category))].slice(0, 4);
        presentCategories.forEach(cat => {
            items.push({
                label: CATEGORY_LABELS[cat] || cat,
                color: CATEGORY_COLORS[cat] || '#80868b',
                class: 'poi'
            });
        });

        items.forEach(item => {
            const div = document.createElement('div');
            div.className = 'legend-item';
            div.innerHTML = `
                <span class="legend-swatch ${item.class}" style="background: ${item.color};"></span>
                <span>${escapeHtml(item.label)}</span>
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

        if (layer) {
            if (visible) {
                if (!state.map.hasLayer(layer)) {
                    state.map.addLayer(layer);
                }
            } else {
                if (state.map.hasLayer(layer)) {
                    state.map.removeLayer(layer);
                }
            }
        }
        if (toggle) {
            toggle.checked = visible;
        }
    }

    // ============================================================
    // Event Listeners
    // ============================================================

    function setupEventListeners() {
        state.ui.findRouteBtn.addEventListener('click', findRoute);
        state.ui.clearRouteBtn.addEventListener('click', clearRoute);

        // Location Swap button (⇄)
        if (state.ui.swapPoiBtn) {
            state.ui.swapPoiBtn.addEventListener('click', swapPOIs);
        }

        // Google Maps edge tab toggle
        if (state.ui.panelToggle) {
            state.ui.panelToggle.addEventListener('click', toggleDashboard);
        }

        // Keyboard shortcut Ctrl+D to toggle sidebar
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'd' || e.key === 'D')) {
                e.preventDefault();
                toggleDashboard();
            }
        });

        // Dropdown changes
        state.ui.startPoiSelect.addEventListener('change', updateRouteButtonState);
        state.ui.endPoiSelect.addEventListener('change', updateRouteButtonState);

        // Filter category change
        state.ui.categorySelect.addEventListener('change', (e) => {
            loadPOIsLayer(e.target.value || null);
        });

        // Layer toggles
        Object.entries(state.ui.layerToggles).forEach(([name, toggle]) => {
            if (toggle) {
                toggle.addEventListener('change', (e) => {
                    updateLayerVisibility(name, e.target.checked);
                });
            }
        });

        // Refresh traffic button
        if (state.ui.refreshTrafficBtn) {
            state.ui.refreshTrafficBtn.addEventListener('click', async () => {
                state.ui.refreshTrafficBtn.disabled = true;
                await loadTrafficStatus();
                state.ui.refreshTrafficBtn.disabled = false;
            });
        }
    }

    function updateRouteButtonState() {
        const hasStart = state.ui.startPoiSelect.value !== '';
        const hasEnd = state.ui.endPoiSelect.value !== '';
        const different = hasStart && hasEnd && state.ui.startPoiSelect.value !== state.ui.endPoiSelect.value;

        state.ui.findRouteBtn.disabled = !different;
    }

})();
