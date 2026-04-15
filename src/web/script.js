const API_BASE = "/api";

// v26.0: Global Error Bridge
window.onerror = function(msg, url, lineNo, columnNo, error) {
    const errorMsg = `[CRITICAL JS] ${msg} (Line: ${lineNo})`;
    if (typeof logAction === 'function') logAction(errorMsg);
    console.error(errorMsg, error);
    return false;
};

// --- UX HELPERS ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.borderLeft = type === 'error' ? '4px solid #f43f5e' : '4px solid #38bdf8';
    toast.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px;">
            <i data-lucide="${type === 'error' ? 'alert-triangle' : 'info'}" style="width:16px; height:16px;"></i>
            <span>${message}</span>
        </div>
    `;
    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function toggleLoading(active) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        if (active) overlay.classList.add('active');
        else overlay.classList.remove('active');
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    if (sidebar) {
        sidebar.classList.toggle('sidebar-collapsed');
        logAction(sidebar.classList.contains('sidebar-collapsed') ? "[UI] Sidebar Collapsed." : "[UI] Sidebar Expanded.");
    }
}

// --- State Management ---
let fleetData = [];
let trajectoryChart;
let causalChart;
let viewMode = '2D'; // '2D' or '3D'
let authToken = localStorage.getItem('aviation_auth_token');
let currentUser = null;

// v32.0: Mapping Constants for MapLibre (Mercator)
let map;
let aircraftLayer;
let customLayer;

// v32.0: AI Global State
let evolutionStats = { xp: 0, cycles: 0, status: 'Stable' };

let scene, camera, renderer, radarPulse;
let aircraftMarkers = {}; // {flight_id: {mesh: Mesh}}
let lastRenderTime = Date.now();
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

let selectedFlightId = null;
let flightTrajectoryLine = null;

let lastNarrative = "";
let decisionSummary = null;
let explanationMap = {};
let activeDecisionFilter = 'all';
let benchmarkSummary = null;

function downloadBlob(content, mimeType, filename) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
}

// v38.0: UI Panel Control
window.closeFlightPanel = function() {
    selectedFlightId = null;
    isFollowMode = false;
    const btn = document.getElementById('btn-follow');
    if (btn) btn.classList.remove('active');
    
    document.getElementById('flight-detail-panel').classList.add('hidden');
    if (flightTrajectoryLine) {
        scene.remove(flightTrajectoryLine);
        flightTrajectoryLine = null;
    }
}

window.toggleFollowMode = function() {
    isFollowMode = !isFollowMode;
    const btn = document.getElementById('btn-follow');
    if (btn) btn.classList.toggle('active', isFollowMode);
    if (isFollowMode) {
        logAction(`[RADAR] Camera lock initiated on ${selectedFlightId}.`);
    } else {
        logAction(`[RADAR] Camera lock released.`);
    }
}
window.setDecisionFilter = function(filterName) {
    activeDecisionFilter = activeDecisionFilter === filterName ? 'all' : filterName;
    updateFilterCards();
    updateUI();
    if (viewMode === '3D') {
        update3DMarkers();
        focusMapOnFilteredFlights();
    }
    const label = activeDecisionFilter === 'all' ? 'all flights' : activeDecisionFilter;
    logAction(`[FILTER] Decision focus set to ${label}.`);
}
window.clearDecisionFilter = function() {
    if (activeDecisionFilter === 'all') return;
    activeDecisionFilter = 'all';
    updateFilterCards();
    updateUI();
    if (viewMode === '3D') {
        update3DMarkers();
        focusMapOnFilteredFlights();
    }
    logAction("[FILTER] Decision focus cleared.");
}
window.downloadFilteredCsv = async function() {
    const filterName = activeDecisionFilter || 'all';
    try {
        const response = await fetch(`${API_BASE}/export/scenario.csv?filter=${encodeURIComponent(filterName)}`);
        if (!response.ok) throw new Error('Export failed');
        const csvText = await response.text();
        downloadBlob(csvText, 'text/csv;charset=utf-8', `aviation_scenario_${filterName}.csv`);
        logAction(`[EXPORT] CSV ready for ${filterName} filter.`);
    } catch (err) {
        console.error("CSV export failed:", err);
        logAction("[EXPORT] CSV export failed.");
    }
}
window.downloadDecisionReport = async function() {
    const filterName = activeDecisionFilter || 'all';
    try {
        const response = await fetch(`${API_BASE}/reports/decision-summary?filter=${encodeURIComponent(filterName)}`);
        if (!response.ok) throw new Error('Report failed');
        const payload = await response.json();
        downloadBlob(
            JSON.stringify(payload, null, 2),
            'application/json;charset=utf-8',
            `decision_report_${filterName}.json`
        );
        logAction(`[REPORT] Decision report downloaded for ${filterName} filter.`);
    } catch (err) {
        console.error("Decision report failed:", err);
        logAction("[REPORT] Decision report download failed.");
    }
}
async function _downloadBinary(path, filename, label) {
    const filterName = activeDecisionFilter || 'all';
    try {
        const response = await fetch(`${API_BASE}/export/${path}?filter=${encodeURIComponent(filterName)}`);
        if (!response.ok) throw new Error(`${label} export failed`);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename.replace('{filter}', filterName);
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        logAction(`[EXPORT] ${label} ready for ${filterName} filter.`);
    } catch (err) {
        console.error(`${label} export failed:`, err);
        logAction(`[EXPORT] ${label} export failed.`);
    }
}
window.downloadDecisionReportPdf = function() {
    return _downloadBinary('decision-report.pdf', 'decision_report_{filter}.pdf', 'PDF report');
};
window.downloadDecisionReportXlsx = function() {
    return _downloadBinary('decision-report.xlsx', 'decision_report_{filter}.xlsx', 'XLSX report');
};
let isForesightActive = false;
let foresightInterval = null;
let isFollowMode = false;

// v34.0: Tactical Typewriter Effect for Gemma Reports
function typeWriter(elementId, text, speed = 25) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.innerText = "";
    let i = 0;
    function type() {
        if (i < text.length) {
            element.innerText += text.charAt(i);
            i++;
            // v35.3: Automated Scroll-lock to follow the narrative flow
            element.scrollTop = element.scrollHeight;
            setTimeout(type, speed);
        }
    }
    type();
}

async function updateAIBriefing() {
    try {
        const response = await fetch(`${API_BASE}/ai/narrative`);
        const data = await response.json();
        
        if (data.report && data.report !== lastNarrative) {
            lastNarrative = data.report;
            typeWriter("briefing-terminal", data.report);
            logAction(`[GEMMA] New Operational Briefing Received. Tactical Insight Delivered.`);
        }
    } catch (e) {
        console.warn("Gemma Briefing Error:", e);
    }
}

// v35.0: Quantum Foresight - Toggle Predictive Heatmap Layer
function toggleForesight() {
    isForesightActive = !isForesightActive;
    const btn = document.getElementById('btn-foresight');
    
    if (isForesightActive) {
        btn.classList.add('active');
        logAction("[FORESIGHT] Strategic Projection Analysis Initiated (T+30m).");
        updateForesightHeatmap();
        foresightInterval = setInterval(updateForesightHeatmap, 30000);
    } else {
        btn.classList.remove('active');
        if (map.getLayer('foresight-heat')) map.setLayoutProperty('foresight-heat', 'visibility', 'none');
        clearInterval(foresightInterval);
        logAction("[FORESIGHT] Predictive Analysis Standby.");
    }
}

async function updateForesightHeatmap() {
    if (!isForesightActive || !map) return;
    
    try {
        const response = await fetch(`${API_BASE}/analytics/foresight-heatmap`);
        const data = await response.json();
        
        if (!map.getSource('foresight-src')) {
            map.addSource('foresight-src', { type: 'geojson', data: data });
            map.addLayer({
                id: 'foresight-heat',
                type: 'heatmap',
                source: 'foresight-src',
                maxzoom: 9,
                paint: {
                    'heatmap-weight': ['get', 'intensity'],
                    'heatmap-intensity': 1,
                    'heatmap-color': [
                        'interpolate', ['linear'], ['heatmap-density'],
                        0, 'rgba(99, 102, 241, 0)',
                        0.2, 'rgba(129, 140, 248, 0.4)',
                        0.5, 'rgba(168, 85, 247, 0.7)',
                        0.8, 'rgba(250, 204, 21, 0.9)'
                    ],
                    'heatmap-radius': 50,
                    'heatmap-opacity': 0.6
                }
            });
        } else {
            map.getSource('foresight-src').setData(data);
            map.setLayoutProperty('foresight-heat', 'visibility', 'visible');
        }
    } catch (err) {
        console.error("Foresight Sync Failed:", err);
    }
}

// --- Authentication ---
window.login = async function() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    
    errorEl.classList.add('hidden');
    
    try {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/jwt/login`, {
            method: 'POST',
            body: formData,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        
        if (!response.ok) throw new Error('Invalid credentials');
        
        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('aviation_auth_token', authToken);
        
        await checkAuthStatus();
        logAction(`[AUTH] Neural Link Established. Welcome, ${currentUser?.full_name || 'Operator'}.`);
    } catch (err) {
        console.error("Login failed:", err);
        errorEl.classList.remove('hidden');
        logAction("[AUTH] Neural Link Failure. Verify credentials.");
    }
}

window.logout = function() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('aviation_auth_token');
    document.getElementById('auth-overlay').classList.remove('hidden');
    document.getElementById('user-profile-bar').classList.add('hidden');
    logAction("[AUTH] Neural Link Terminated. Standby.");
}

async function checkAuthStatus() {
    if (!authToken) {
        document.getElementById('auth-overlay').classList.remove('hidden');
        return false;
    }
    
    try {
        const response = await authFetch(`${API_BASE}/auth/me`);
        if (!response.ok) throw new Error('Token expired');
        
        currentUser = await response.json();
        document.getElementById('auth-overlay').classList.add('hidden');
        document.getElementById('user-profile-bar').classList.remove('hidden');
        document.getElementById('user-name-display').innerText = currentUser.full_name || 'Operator';
        document.getElementById('user-role-display').innerText = currentUser.role || 'Viewer';
        
        // Initial data load after auth
        await fetchScenario();
        setInterval(updateEvolutionStats, 5000);
        setInterval(updateAIBriefing, 10000);
        
        return true;
    } catch (err) {
        console.warn("Auth check failed:", err);
        logout();
        return false;
    }
}

async function authFetch(url, options = {}) {
    if (!options.headers) options.headers = {};
    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }
    return fetch(url, options);
}

// --- API Calls ---
async function fetchScenario() {
    toggleLoading(true);
    try {
        const response = await authFetch(`${API_BASE}/scenario`);
        if (!response.ok) throw new Error("API Offline or Unauthorized");
        fleetData = await response.json();
        
        // ROADMAP PHASE 6: Onboarding Check
        if (fleetData.length === 0) {
            showToast("Operational Scenario is EMPTY. Initializing tactical simulation...", "info");
            await syncLive(); // Use syncLive to bootstrap data
        }

        await fetchOptimizerExplanations();
        updateUI();
        fetchKPIs();
        if (viewMode === '3D') update3DMarkers();
    } catch (err) {
        console.error("Fetch Scenario Failed:", err);
        showToast("Telemetry Link Failure: Check Neural Connectivity", "error");
    } finally {
        toggleLoading(false);
    }
}

async function fetchKPIs() {
    try {
        const response = await fetch(`${API_BASE}/analytics/kpi`);
        if (!response.ok) return;
        const kpis = await response.json();
        document.getElementById('kpi-plf').innerText = `${kpis.plf}%`;
        document.getElementById('kpi-cqi').innerText = kpis.cqi;
    } catch (err) {}
}

async function fetchOptimizerExplanations() {
    try {
        const response = await fetch(`${API_BASE}/optimizer/explanations`);
        if (!response.ok) return;
        const payload = await response.json();
        decisionSummary = payload.summary || null;
        explanationMap = {};
        (payload.flights || []).forEach(f => {
            explanationMap[f.flight_id] = f;
        });
    } catch (err) {}
}

async function syncLive() {
    logAction("Syncing with OpenSky & Live Radar nodes...");
    const badge = document.getElementById('sync-status-badge');
    if (badge) badge.innerText = "SYNCING...";
    
    try {
        const response = await fetch(`${API_BASE}/sync/live-traffic`);
        const data = await response.json();
        
        if (data.active_flights) {
            logAction(`Radar Sync [${data.source}]: ${data.count} aircraft tracked.`);
            if (badge) {
                badge.innerText = data.offline ? "LIVE (SIM)" : "LIVE SYNCED";
                badge.style.color = data.offline ? "#fbbf24" : "#10b981";
            }
            updateLive3DMarkers(data.active_flights);
        }
    } catch (err) {
        logAction(`Sync Error: ${err.message || 'ADS-B node unreachable'}`);
        console.error("Sync Details:", err);
        if (badge) {
            badge.innerText = "OFFLINE";
            badge.style.color = "#f43f5e";
        }
    }
}

// --- 3D Airplane Mesh Generator ---
function createAirplaneMesh(colorHex, emissiveHex, opacityScale = 0.95) {
    const group = new THREE.Group();
    const material = new THREE.MeshPhongMaterial({ 
        color: colorHex, 
        emissive: emissiveHex || colorHex, 
        emissiveIntensity: 0.7,
        transparent: true,
        opacity: opacityScale
    });
    
    // Fuselage
    const fuselage = new THREE.Mesh(new THREE.CylinderGeometry(180, 180, 2400, 12), material);
    group.add(fuselage);
    
    // Wings
    const wings = new THREE.Mesh(new THREE.BoxGeometry(2800, 400, 80), material);
    wings.position.y = 200; 
    group.add(wings);
    
    // Tail
    const tail = new THREE.Mesh(new THREE.BoxGeometry(900, 250, 80), material);
    tail.position.y = -1000; 
    group.add(tail);
    
    // Vertical Fin
    const fin = new THREE.Mesh(new THREE.BoxGeometry(80, 300, 350), material);
    fin.position.y = -1000;
    fin.position.z = 200;
    group.add(fin);

    return group;
}

function getFilteredFleetData() {
    switch (activeDecisionFilter) {
        case 'canceled':
            return fleetData.filter(f => Number(f.is_canceled) === 1);
        case 'delayed':
            return fleetData.filter(f => Number(f.assigned_delay) > 0 && Number(f.is_canceled) !== 1);
        case 'swaps':
            return fleetData.filter(f => f.assigned_aircraft && f.assigned_aircraft !== "None" && f.assigned_aircraft !== f.aircraft_id);
        case 'pressure':
            return fleetData.filter(f => !!f.slot_pressure_flag);
        default:
            return fleetData;
    }
}

function getScenarioVisualState(flight) {
    if (flight.is_canceled) {
        return { color: 0xf43f5e, status: "CANCELED", pulseSpeed: 3.0, opacity: 0.95 };
    }
    if (flight.slot_pressure_flag) {
        return { color: 0xfacc15, status: "PRESSURE", pulseSpeed: 4.0, opacity: 1.0 };
    }
    if (flight.assigned_delay > 0) {
        return { color: 0xfb923c, status: "DELAYED", pulseSpeed: 2.3, opacity: 0.9 };
    }
    return { color: 0x0ea5e9, status: "OPTIMAL", pulseSpeed: 1.2, opacity: 0.85 };
}

function shortenReason(reason) {
    if (!reason) return "No reason";
    const compact = String(reason).replace(/^Cancellation:\s*/i, '').trim();
    return compact.length > 42 ? `${compact.slice(0, 42)}...` : compact;
}

function focusMapOnFilteredFlights() {
    if (!map) return;
    const flights = getFilteredFleetData();
    if (!flights.length) return;

    if (flights.length === 1) {
        map.easeTo({
            center: [flights[0].lon, flights[0].lat],
            zoom: 10.5,
            duration: 900
        });
        return;
    }

    let minLon = Infinity;
    let minLat = Infinity;
    let maxLon = -Infinity;
    let maxLat = -Infinity;

    flights.forEach((f) => {
        minLon = Math.min(minLon, Number(f.lon));
        minLat = Math.min(minLat, Number(f.lat));
        maxLon = Math.max(maxLon, Number(f.lon));
        maxLat = Math.max(maxLat, Number(f.lat));
    });

    if (Number.isFinite(minLon) && Number.isFinite(minLat) && Number.isFinite(maxLon) && Number.isFinite(maxLat)) {
        map.fitBounds(
            [[minLon, minLat], [maxLon, maxLat]],
            { padding: 90, duration: 1000, maxZoom: 10.5 }
        );
    }
}

function updateFilterCards() {
    const filters = ['canceled', 'delayed', 'swaps', 'pressure'];
    filters.forEach(name => {
        const card = document.getElementById(`filter-${name}`);
        if (!card) return;
        const active = activeDecisionFilter === name;
        card.style.borderColor = active ? 'rgba(250, 204, 21, 0.65)' : 'rgba(255,255,255,0.08)';
        card.style.boxShadow = active ? '0 0 0 1px rgba(250,204,21,0.15), 0 0 18px rgba(250,204,21,0.18)' : 'none';
        card.style.transform = active ? 'translateY(-1px)' : 'translateY(0)';
    });

    const label = document.getElementById('active-filter-label');
    const clearBtn = document.getElementById('clear-filter-btn');
    const filterLabels = {
        all: 'All flights',
        canceled: 'Canceled flights only',
        delayed: 'Delayed flights only',
        swaps: 'Aircraft swaps only',
        pressure: 'Slot-pressure flights only'
    };
    if (label) label.innerText = filterLabels[activeDecisionFilter] || 'All flights';
    if (clearBtn) clearBtn.classList.toggle('hidden', activeDecisionFilter === 'all');
}

// v32.0: Real-Time ADS-B Marker Engine for MapLibre
function updateLive3DMarkers(liveFlights) {
    if (!scene || !map) return;

    // Clear existing
    Object.keys(aircraftMarkers).forEach(id => {
        if (id.startsWith('LIVE_')) {
            const marker = aircraftMarkers[id];
            if (marker.mesh) scene.remove(marker.mesh);
            delete aircraftMarkers[id];
        }
    });

    liveFlights.forEach(f => {
        const id = `LIVE_${f.flight_id}`;
        
        // v32.5: Accurate Metric Scaling for IST (Lon 28.74, Lat 41.27)
        const lonOffset = (f.lon - 28.74) * 83500; 
        const latOffset = (f.lat - 41.27) * 111320;
        const alt = f.alt || 3000;

        const isDelayed = f.status === "DELAYED";
        const color = isDelayed ? 0xf43f5e : 0xfacc15; // Yellow for live Flightradar24 feel
        const mesh = createAirplaneMesh(color, color, 0.95);
        mesh.position.set(lonOffset, latOffset, alt);
        mesh.rotateX(Math.PI / 2);
        mesh.rotation.z = - (f.heading * Math.PI / 180);
        
        // The children do not need userData anymore
        
        // Internal tactical pulse effect data
        mesh.userData = { 
            flight_id: f.flight_id,
            velocity: f.velocity,
            alt: alt,
            heading: f.heading,
            status: f.status,
            baseScale: 1.0, 
            pulseSpeed: 2 + Math.random(),
            isDelayed: f.status === "DELAYED"
        };
        
        scene.add(mesh);
        aircraftMarkers[id] = { mesh };

        // v32.0: Collect data for AI Training (Experience Buffer)
        collectAIEvidence(f);
    });
}

function collectAIEvidence(flight) {
    // Report to backend to feed the Evolution Engine
    fetch(`${API_BASE}/evolution/summary`, {
        method: 'POST', 
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            observation: [flight.lat, flight.lon, flight.alt, flight.velocity],
            reward: flight.status === "OPTIMAL" ? 1 : -1
        })
    }).catch(() => {});
}

// v22.2: Brain Stats Polling Engine
async function updateEvolutionStats() {
    try {
        const response = await authFetch(`${API_BASE}/evolution/summary`);
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('evo-xp').innerText = stats.experience_points;
            document.getElementById('evo-cycles').innerText = stats.evolution_cycles;
            document.getElementById('evo-status').innerText = stats.status.toUpperCase();
            
            // Progress bar (Loops every 100 XP for visual feel)
            const progress = (stats.experience_points % 100);
            document.getElementById('evo-progress').style.width = `${progress}%`;
        }
    } catch (err) {}
}

async function runOptimize() {
    toggleLoading(true);
    
    // v17.1: Frontend Safeguard Timeout (40s)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        controller.abort();
        logAction("OPTIMIZATION TIMEOUT: Complex plan restored. Try a smaller window.");
        showToast("Optimization Timeout (60s)", "error");
    }, 60000); 

    try {
        const response = await authFetch(`${API_BASE}/optimize`, { 
            method: 'POST',
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        const result = await response.json();
        await fetchScenario();

        if (result.status === "success") {
            logAction(`Success: ${result.message}`);
            showToast("✅ Tactical Recovery Successful", "success");
            if (result.decision_summary?.top_reasons?.length) {
                logAction(`Primary driver: ${result.decision_summary.top_reasons[0].reason}`);
            }
        } else if (result.status === "partial_success") {
            logAction(`Alert: ${result.message}`);
            showToast("⚠️ Partial Optimization Achieved", "warn");
        }
        
    } catch (err) {
        if (err.name === 'AbortError') {
            logAction("Optimization Aborted (Timeout). Baseline plan restored.");
        } else {
            console.error("Optimization Failed:", err);
            logAction("Critical Error during optimization. Check network.");
            showToast("Solver Process Failure", "error");
        }
    } finally {
        toggleLoading(false);
    }
}

async function runAIOptimize() {
    logAction("AI COMMAND INITIATED: Engaging Neural Commander v1...");
    try {
        const response = await fetch(`${API_BASE}/ai/optimize`, { method: 'POST' });
        const result = await response.json();
        await fetchScenario();
        logAction(`AI Decision: ${result.message}`);
    } catch (err) {
        logAction("AI Command Error: Neural link failure.");
    }
}

async function triggerStressTest() {
    logAction("SHOCK INJECTED: Massive Hub Delay at IST Triggered.");
    try {
        const response = await authFetch(`${API_BASE}/stress-test`, { method: 'POST' });
        const badge = document.getElementById('recovery-badge');
        if (badge) badge.classList.remove('hidden');
        await fetchScenario();
        setTimeout(() => badge.classList.add('hidden'), 8000);
    } catch (err) {}
}

// v32.0: MapLibre + Three.js Custom Layer Initialization
function initMapLibre() {
    const container = document.getElementById('three-container');
    if (!container) return;

    map = new maplibregl.Map({
        container: 'three-container',
        style: {
            "version": 8,
            "sources": {},
            "layers": [
                {
                    "id": "background",
                    "type": "background",
                    "paint": { "background-color": "#020617" }
                }
            ]
        },
        center: [28.74, 41.27], // Istanbul Hub
        zoom: 9,
        pitch: 45,
        antialias: true
    });

    // Add High-Res ArcGIS Satellite Layer
    map.on('load', () => {
        map.addSource('satellite', {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256
        });
        map.addLayer({
            id: 'satellite',
            type: 'raster',
            source: 'satellite',
            minzoom: 0,
            maxzoom: 22
        });

        initThreeCustomLayer();
        logAction("VISUAL ENGINE: MapLibre Satellite Core Online.");
    });
}

function initThreeCustomLayer() {
    const modelOrigin = [28.74, 41.27];
    const modelAltitude = 0;
    const modelRotate = [Math.PI / 2, 0, 0];
    const modelAsMercatorCoordinate = maplibregl.MercatorCoordinate.fromLngLat(modelOrigin, modelAltitude);

    const modelTransform = {
        translateX: modelAsMercatorCoordinate.x,
        translateY: modelAsMercatorCoordinate.y,
        translateZ: modelAsMercatorCoordinate.z,
        rotateX: modelRotate[0],
        rotateY: modelRotate[1],
        rotateZ: modelRotate[2],
        scale: modelAsMercatorCoordinate.meterInMercatorCoordinateUnits()
    };

    customLayer = {
        id: 'aircraft-3d-layer',
        type: 'custom',
        renderingMode: '3d',
        onAdd: function (map, gl) {
            camera = new THREE.Camera();
            scene = new THREE.Scene();

            // v32.5: High-Intensity Diagnostic Lighting
            // v32.9: Tactical Radar Pulse Ring at IST
            const ringGeo = new THREE.RingGeometry(8000, 8500, 64);
            const ringMat = new THREE.MeshBasicMaterial({ 
                color: 0x0ea5e9, 
                transparent: true, 
                opacity: 0.3,
                side: THREE.DoubleSide 
            });
            radarPulse = new THREE.Mesh(ringGeo, ringMat);
            radarPulse.position.set(0, 0, 50); // Just above ground
            scene.add(radarPulse);

            renderer = new THREE.WebGLRenderer({
                canvas: map.getCanvas(),
                context: gl,
                antialias: true
            });
            renderer.autoClear = false;
        },
        render: function (gl, matrix) {
            const now = Date.now();
            const time = now * 0.001;
            const dt = lastRenderTime ? (now - lastRenderTime) / 1000.0 : 0.016;
            lastRenderTime = now;
            
            // v32.9 Tactical Animations
            if (radarPulse) {
                const s = 1 + (time % 2) * 2;
                radarPulse.scale.set(s, s, 1);
                radarPulse.material.opacity = 0.4 * (1 - (time % 2) / 2);
            }

            // Animate all aircraft markers for 'System Vitality'
            Object.keys(aircraftMarkers).forEach(id => {
                const marker = aircraftMarkers[id];
                if (marker && marker.mesh) {
                    const u = marker.mesh.userData;
                    const pulse = 1 + Math.sin(time * u.pulseSpeed) * 0.1;
                    
                    // Do not pulse scale the realistic airplanes, just opacity
                    if (marker.mesh.children && marker.mesh.children.length > 0) {
                        marker.mesh.children.forEach(c => {
                           c.material.opacity = 0.7 + (Math.sin(time * u.pulseSpeed) * 0.25);
                        });
                    }

                    // Interpolate movement for F24-style motion
                    if (u.velocity && u.heading !== undefined) {
                        const speedScale = 8; // Mapping knots to visual Three.js units per sec
                        const headingRad = -(u.heading * Math.PI / 180) + Math.PI/2;
                        marker.mesh.position.x += Math.cos(headingRad) * u.velocity * speedScale * dt;
                        marker.mesh.position.y += Math.sin(headingRad) * u.velocity * speedScale * dt;
                    }

                    // v38.0: Update trajectory tail if this is the selected flight
                    if (selectedFlightId === u.flight_id && flightTrajectoryLine) {
                        const positions = flightTrajectoryLine.geometry.attributes.position.array;
                        // Set the destination node of the trajectory to the interpolated position
                        positions[3] = marker.mesh.position.x;
                        positions[4] = marker.mesh.position.y;
                        positions[5] = marker.mesh.position.z;
                        flightTrajectoryLine.geometry.attributes.position.needsUpdate = true;
                    }
                }
            });

            const rotationX = new THREE.Matrix4().makeRotationX(modelTransform.rotateX);
            const rotationY = new THREE.Matrix4().makeRotationY(modelTransform.rotateY);
            const rotationZ = new THREE.Matrix4().makeRotationZ(modelTransform.rotateZ);

            const m = new THREE.Matrix4().fromArray(matrix);
            const l = new THREE.Matrix4()
                .makeTranslation(modelTransform.translateX, modelTransform.translateY, modelTransform.translateZ)
                .scale(new THREE.Vector3(modelTransform.scale, -modelTransform.scale, modelTransform.scale))
                .multiply(rotationX)
                .multiply(rotationY)
                .multiply(rotationZ);

            camera.projectionMatrix = m.multiply(l);

            // v38.0: Follow Mode Logic
            if (isFollowMode && selectedFlightId) {
                const target = aircraftMarkers[selectedFlightId] || Object.values(aircraftMarkers).find(m => m.mesh.userData.flight_id === selectedFlightId);
                if (target && target.mesh) {
                    // Convert Three.js local coords back to LngLat for MapLibre
                    // This is an approximation since we don't have the inverse transform easily
                    // But we can use the mesh position relative to the origin
                    const lonPos = 28.74 + (target.mesh.position.x / 83500);
                    const latPos = 41.27 + (target.mesh.position.y / 111320);
                    map.easeTo({
                        center: [lonPos, latPos],
                        duration: 0,
                        easing: (t) => t
                    });
                }
            }

            renderer.resetState();
            renderer.render(scene, camera);
            map.triggerRepaint();
        }
    };
    map.addLayer(customLayer);
    
    // v32.4: Trigger initial data sync as soon as the layer is ready
    setTimeout(() => {
        update3DMarkers();
        focusMapOnFilteredFlights();
        syncLive();
    }, 500);
}

// v32.0: Synchronize Scenario Aircraft markers with MapLibre
function update3DMarkers() {
    if (!scene || !map || !fleetData) return;
    const visibleFlights = getFilteredFleetData();
    const visibleIds = new Set(visibleFlights.map(f => f.flight_id));

    // Clear existing static markers
    Object.keys(aircraftMarkers).forEach(id => {
        if (!id.startsWith('LIVE_')) {
            const marker = aircraftMarkers[id];
            if (marker.mesh) scene.remove(marker.mesh);
            delete aircraftMarkers[id];
        }
    });

    visibleFlights.forEach((f) => {
        // v32.5: Accurate Metric Scaling for IST
        const lonOffset = (f.lon - 28.74) * 83500; 
        const latOffset = (f.lat - 41.27) * 111320;
        const alt = 2500; 

        const visual = getScenarioVisualState(f);
        
        const mesh = createAirplaneMesh(visual.color, visual.color, visual.opacity);
        mesh.position.set(lonOffset, latOffset, alt);
        mesh.rotateX(Math.PI / 2);
        mesh.rotation.z = Math.PI / 4; 
        
        mesh.userData = { 
            flight_id: f.flight_id,
            velocity: 400 + Math.random() * 50, // Approx cruising speed
            alt: alt,
            heading: 45, // Default for scenario
            status: visual.status,
            baseScale: 1.0, 
            pulseSpeed: visual.pulseSpeed,
            slotPressure: !!f.slot_pressure_flag,
            visibleIds
        };
        
        scene.add(mesh);
        aircraftMarkers[f.flight_id] = { mesh };
    });
}

function setViewMode(mode) {
    viewMode = mode;
    const container = document.getElementById('three-container');
    
    document.body.classList.toggle('strategic-3d-active', mode === '3D');
    document.getElementById('toggle-2d').classList.toggle('active', mode === '2D');
    document.getElementById('toggle-3d').classList.toggle('active', mode === '3D');
    
    if (container) {
        container.classList.toggle('hidden', mode === '2D');
        if (mode === '3D') {
            if (!map) {
                initMapLibre();
            } else {
                map.resize();
                focusMapOnFilteredFlights();
            }
        }
    }
}

// --- UI Logic ---
function updateUI() {
    const filteredFleet = getFilteredFleetData();
    const tbody = document.getElementById('fleet-table-body');
    if (tbody) {
        if (!filteredFleet.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" style="padding:18px 6px; color:#94a3b8; text-align:center; font-size:0.68rem;">
                        No flights match the current decision filter.
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = filteredFleet.slice(0, 8).map(f => `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                <td style="padding: 10px 5px; font-weight:bold; color:#38bdf8;">${f.flight_id}</td>
                <td style="padding: 10px 5px; color:#f8fafc;">${(f.load_factor * 100).toFixed(0)}%</td>
                <td style="padding: 10px 5px;">
                    <span style="color:${f.is_canceled ? '#f43f5e' : (f.slot_pressure_flag ? '#facc15' : (f.assigned_delay > 0 ? '#fb923c' : '#10b981'))}">${f.is_canceled ? 'CANCEL' : (f.slot_pressure_flag ? 'PRESSURE' : (f.assigned_delay > 0 ? 'DELAY' : 'CLEAR'))}</span>
                    <div style="font-size:0.58rem; color:#94a3b8; margin-top:4px; line-height:1.35;">${shortenReason(f.decision_reason)}</div>
                </td>
            </tr>
            `).join('');
        }
    }

    if (decisionSummary) {
        const canceled = document.getElementById('kpi-canceled');
        const delayed = document.getElementById('kpi-delayed');
        const swaps = document.getElementById('kpi-swaps');
        const topReason = document.getElementById('kpi-top-reason');
        const summaryBanner = document.getElementById('decision-summary-banner');
        if (canceled) canceled.innerText = decisionSummary.canceled;
        if (delayed) delayed.innerText = decisionSummary.delayed;
        if (swaps) swaps.innerText = decisionSummary.swap_count;
        if (topReason) {
            topReason.innerText = decisionSummary.top_reasons?.length
                ? `${decisionSummary.top_reasons[0].reason} (${decisionSummary.top_reasons[0].count})`
                : "No dominant decision driver yet.";
        }
        if (summaryBanner) {
            const top = decisionSummary.top_reasons?.[0];
            summaryBanner.innerText = top
                ? `${decisionSummary.canceled} canceled, ${decisionSummary.delayed} delayed, ${decisionSummary.swap_count} swaps. Main driver: ${top.reason}.`
                : `${decisionSummary.canceled} canceled, ${decisionSummary.delayed} delayed, ${decisionSummary.swap_count} swaps recorded.`;
        }
    }
    updateFilterCards();

    const causes = filteredFleet.reduce((acc, f) => {
        const factor = f.causal_factor || 'Operational';
        acc[factor] = (acc[factor] || 0) + 1;
        return acc;
    }, {});
    
    if (causalChart) {
        causalChart.data.labels = Object.keys(causes);
        causalChart.data.datasets[0].data = Object.values(causes);
        causalChart.update();
    }
}

function logAction(msg) {
    const feed = document.getElementById('agent-logs');
    if (!feed) return;
    const entry = document.createElement('div');
    entry.style.cssText = "padding:0.6rem; border-radius:0.5rem; background:rgba(14,165,233,0.05); border:1px solid rgba(14,165,233,0.1); font-size:0.65rem; margin-bottom:0.5rem;";
    entry.innerHTML = `<span style="color:#0ea5e9; font-weight:bold;">[STAT]</span> ${msg}`;
    feed.prepend(entry);
}

// --- Charts Initialization ---
function initCharts() {
    const canvasTraj = document.getElementById('trajectoryChart');
    if (canvasTraj) {
        const ctxTraj = canvasTraj.getContext('2d');
        trajectoryChart = new Chart(ctxTraj, {
            type: 'line',
            data: {
                labels: ['T-3', 'T-2', 'T-1', 'NOW', 'T+1', 'T+2'],
                datasets: [{
                    label: 'Quantum State Delta',
                    data: [5, 12, 8, 15, 7, 10],
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    y: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#64748b' } },
                    x: { grid: { display: false }, ticks: { color: '#64748b' } }
                }
            }
        });
    }

    const canvasCausal = document.getElementById('causalChart');
    if (canvasCausal) {
        const ctxCausal = canvasCausal.getContext('2d');
        causalChart = new Chart(ctxCausal, {
            type: 'doughnut',
            data: {
                labels: ['Weather', 'Cyber', 'Technical', 'Operational'],
                datasets: [{
                    data: [1, 1, 1, 1],
                    backgroundColor: ['#0ea5e9', '#f43f5e', '#a855f7', '#fbbf24'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '80%',
                plugins: { legend: { display: false } }
            }
        });
    }
}

async function fetchForecast() {
    try {
        const response = await authFetch(`${API_BASE}/analytics/forecast`);
        if (!response.ok) return;
        const data = await response.json();
        updateForecastUI(data);
    } catch (err) {}
}

async function fetchModelBenchmark() {
    try {
        const response = await authFetch(`${API_BASE}/analytics/model-benchmark`);
        if (!response.ok) return;
        benchmarkSummary = await response.json();
        updateBenchmarkUI(benchmarkSummary);
    } catch (err) {}
}

function updateForecastUI(forecast) {
    const tbody = document.getElementById('forecast-body');
    if (!tbody) return;
    tbody.innerHTML = forecast.map(d => `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
            <td style="padding: 6px 4px; color:#f8fafc;">${d.date}</td>
            <td style="padding: 6px 4px; font-weight:bold; color:#10b981;">${d.predicted_plf}%</td>
            <td style="padding: 6px 4px;"><span style="color:${d.disruption_risk > 15 ? '#f43f5e' : '#64748b'}">${d.disruption_risk}%</span></td>
        </tr>
    `).join('');
}

function updateBenchmarkUI(payload) {
    const tbody = document.getElementById('benchmark-body');
    const best = document.getElementById('benchmark-best-model');
    const meta = document.getElementById('benchmark-dataset-meta');
    if (!tbody || !payload) return;

    if (best) {
        best.innerText = payload.best_model ? `Best: ${payload.best_model}` : "No winner";
        best.style.color = payload.best_model ? "#facc15" : "#94a3b8";
    }

    if (meta && payload.dataset) {
        meta.innerText = `${payload.dataset.rows} rows | ${payload.dataset.train_rows} train | ${payload.dataset.test_rows} test | positive rate ${Math.round((payload.dataset.positive_rate || 0) * 100)}%`;
    }

    const models = payload.models || [];
    tbody.innerHTML = models.map(model => {
        const ok = model.status === 'ok';
        const isBest = payload.best_model === model.name;
        const stateColor = ok ? (isBest ? '#facc15' : '#10b981') : '#94a3b8';
        const stateLabel = ok ? (isBest ? 'LEADER' : 'READY') : 'SKIPPED';
        return `
            <tr style="border-bottom:1px solid rgba(255,255,255,0.03);">
                <td style="padding:6px 4px; color:${isBest ? '#f8fafc' : '#cbd5e1'}; font-weight:${isBest ? '700' : '500'};">${model.name}</td>
                <td style="padding:6px 4px; color:#f8fafc;">${ok && model.f1 != null ? model.f1.toFixed(3) : '--'}</td>
                <td style="padding:6px 4px; color:#cbd5e1;">${ok && model.roc_auc != null ? model.roc_auc.toFixed(3) : '--'}</td>
                <td style="padding:6px 4px; color:${stateColor}; font-weight:bold;">${stateLabel}</td>
            </tr>
        `;
    }).join('');
}

// --- Start System ---
document.addEventListener('DOMContentLoaded', async () => {
    initCharts();
    
    // v27.0: Auth-driven initialization
    const authenticated = await checkAuthStatus();
    if (!authenticated) {
        if (window.lucide) lucide.createIcons();
        return; 
    }

    // (The following block is already partially inside checkAuthStatus, 
    // but we can refine the startup sequence here)
    fetchForecast();
    fetchModelBenchmark();
    updateAIBriefing(); 
    
    // v35.5: WebSocket Real-Time Integration
    const wsProto = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${wsProto}//${location.host}/api/ws`);
    ws.onmessage = (event) => {
        if (event.data === "SCENARIO_UPDATED") {
            logAction("[NET] WebSocket Push: Tactical Scenario Updated.");
            fetchScenario();
            fetchForecast();
            fetchModelBenchmark();
            updateEvolutionStats();
        }
    };
    ws.onopen = () => logAction("[NET] WebSocket Connected: Real-time telemetry active.");
    
    // Keep a slow fallback heartbeat just in case
    setInterval(() => {
        if (!authToken) return;
        fetchScenario();
        fetchForecast();
        fetchModelBenchmark();
    }, 60000); 
    
    setInterval(updateEvolutionStats, 5000); // Faster polling for XP
    setInterval(updateAIBriefing, 60000);    // v34.0: 60s Cognitive Heartbeat
    
    if (window.lucide) lucide.createIcons();

// --- 3D INTERACTION LOGIC (RAYCASTER) ---

const tooltipDiv = document.createElement('div');
tooltipDiv.style.position = 'absolute';
tooltipDiv.style.background = 'rgba(15, 23, 42, 0.95)';
tooltipDiv.style.border = '1px solid #38bdf8';
tooltipDiv.style.padding = '10px';
tooltipDiv.style.color = '#fff';
tooltipDiv.style.fontSize = '11px';
tooltipDiv.style.fontFamily = 'Inter, sans-serif';
tooltipDiv.style.borderRadius = '6px';
tooltipDiv.style.pointerEvents = 'none';
tooltipDiv.style.zIndex = '1000';
tooltipDiv.style.display = 'none';
tooltipDiv.style.boxShadow = '0 0 15px rgba(14,165,233,0.3)';
document.body.appendChild(tooltipDiv);

document.getElementById('three-container').addEventListener('mousemove', (e) => {
    if (!camera || !scene || viewMode !== '3D') {
        tooltipDiv.style.display = 'none';
        return;
    }

    const rect = e.target.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    // Unproject using MapLibre's modified camera projection
    raycaster.setFromCamera(mouse, camera);

    const meshes = Object.values(aircraftMarkers).map(m => m.mesh).filter(m => m);
    // use recursive true to hit group children
    const intersects = raycaster.intersectObjects(meshes, true);

    if (intersects.length > 0) {
        const top = intersects[0];
        const u = top.object.parent.userData;
        
        if (Object.keys(u).length > 0) {
            tooltipDiv.style.left = (e.clientX + 15) + 'px';
            tooltipDiv.style.top = (e.clientY + 15) + 'px';
            tooltipDiv.innerHTML = `
                <strong style="color: #38bdf8; font-family: 'Orbitron'; font-size: 13px;">✈️ ${u.flight_id || 'UNKNOWN'}</strong><br/>
                <div style="margin-top: 4px; color: #94a3b8;">
                    SPD: <span style="color:#e2e8f0; font-weight:bold;">${Math.round(u.velocity)} kts</span><br/>
                    ALT: <span style="color:#e2e8f0; font-weight:bold;">${u.alt} ft</span><br/>
                    STATUS: <span style="color:${u.status === 'CANCELED' ? '#f43f5e' : (u.status === 'PRESSURE' ? '#facc15' : (u.status === 'DELAYED' ? '#fb923c' : '#10b981'))}; font-weight:bold;">${u.status}</span><br/>
                    <span style="color:#38bdf8; font-size:9px; margin-top:4px; display:block;">[CLICK TO LOCK RADAR]</span>
                </div>
            `;
            tooltipDiv.style.display = 'block';
            document.body.style.cursor = 'crosshair';
        }
    } else {
        tooltipDiv.style.display = 'none';
        document.body.style.cursor = 'default';
    }
});

// v38.0: Click Interaction for Detail Panel & Trajectory
document.getElementById('three-container').addEventListener('click', (e) => {
    if (!camera || !scene || viewMode !== '3D') return;

    const rect = e.target.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const meshes = Object.values(aircraftMarkers).map(m => m.mesh).filter(m => m);
    const intersects = raycaster.intersectObjects(meshes, true);

    if (intersects.length > 0) {
        const top = intersects[0];
        // v38.0: Trace up to find the group containing userData
        let obj = top.object;
        while (obj && !obj.userData.flight_id && obj.parent) {
            obj = obj.parent;
        }
        
        const u = obj ? obj.userData : null;
        if (u && u.flight_id) {
            selectedFlightId = u.flight_id;
            
            // Populate Panel
            document.getElementById('dtl-callsign').innerText = u.flight_id;
            document.getElementById('dtl-speed').innerHTML = `<span style="color:#38bdf8;">${Math.round(u.velocity)}</span> kts`;
            document.getElementById('dtl-alt').innerHTML = `<span style="color:#38bdf8;">${u.alt}</span> ft`;
            document.getElementById('dtl-heading').innerHTML = `<span style="color:#38bdf8;">${u.heading}</span>°`;
            document.getElementById('dtl-status').innerText = u.status;
            document.getElementById('dtl-status').style.color = u.status === 'CANCELED' ? '#f43f5e' : (u.status === 'PRESSURE' ? '#facc15' : (u.status === 'DELAYED' ? '#fb923c' : '#10b981'));

            // Resolve Origin/Dest and other metadata
            const fleetInfo = fleetData.find(f => f.flight_id === u.flight_id);
            if (fleetInfo) {
                document.getElementById('dtl-origin-dest').innerText = `${fleetInfo.origin} ➔ ${fleetInfo.destination}`;
                document.getElementById('dtl-lf').innerText = `${(fleetInfo.load_factor * 100).toFixed(0)}%`;
                document.getElementById('dtl-cert').innerText = fleetInfo.ac_cat || fleetInfo.ac_type || "Commercial";
                document.getElementById('dtl-reason').innerText = fleetInfo.decision_reason || "No tactical explanation available.";
                document.getElementById('dtl-slot-flag').innerText = fleetInfo.slot_pressure_flag ? "SLOT PRESSURE" : "NORMAL FLOW";
                document.getElementById('dtl-slot-flag').style.color = fleetInfo.slot_pressure_flag ? "#facc15" : "#10b981";
            } else {
                document.getElementById('dtl-origin-dest').innerText = `LIVE RADAR ➔ UNKNOWN`;
                document.getElementById('dtl-reason').innerText = "Live radar target is not part of the optimized tactical scenario.";
                document.getElementById('dtl-slot-flag').innerText = "EXTERNAL TRACK";
                document.getElementById('dtl-slot-flag').style.color = "#38bdf8";
            }

            document.getElementById('flight-detail-panel').classList.remove('hidden');

            // --- Advanced Trajectory Logic ---
            if (flightTrajectoryLine) scene.remove(flightTrajectoryLine);
            
            const points = [];
            const originColor = 0x10b981; // Green for path
            
            if (fleetInfo && fleetInfo.origin_lat) {
                // v38.0 Path Architecture: Origin -> Plane -> Destination
                const oX = (fleetInfo.origin_lon - 28.74) * 83500;
                const oY = (fleetInfo.origin_lat - 41.27) * 111320;
                const dX = (fleetInfo.dest_lon - 28.74) * 83500;
                const dY = (fleetInfo.dest_lat - 41.27) * 111320;

                points.push(new THREE.Vector3(oX, oY, 0));      // Airport Origin
                points.push(new THREE.Vector3(obj.position.x, obj.position.y, obj.position.z)); // Plane
                points.push(new THREE.Vector3(dX, dY, 0));      // Airport Dest
            } else {
                // Fallback Trail for live flights without scenario data
                const trailLength = 500000;
                const headingRad = -(u.heading * Math.PI / 180) + Math.PI/2;
                const startX = obj.position.x - Math.cos(headingRad) * trailLength;
                const startY = obj.position.y - Math.sin(headingRad) * trailLength;
                points.push(new THREE.Vector3(startX, startY, u.alt));
                points.push(new THREE.Vector3(obj.position.x, obj.position.y, u.alt));
            }
            
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({ 
                color: originColor, 
                linewidth: 2, 
                transparent: true, 
                opacity: 0.6 
            });
            flightTrajectoryLine = new THREE.Line(geometry, material);
            scene.add(flightTrajectoryLine);
            
            logAction(`[RADAR] Focused on ${u.flight_id}. Path Analysis Locked.`);
        }
    } else {
        closeFlightPanel();
    }
    });

    // v27.0: Global Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Only trigger if not in an input field
        if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

        switch(e.key.toLowerCase()) {
            case 'r': // Recover/Optimize
                e.preventDefault();
                showToast("Tactical Resolve Initiated via Shortcut (R)");
                runOptimize();
                break;
            case 'e': // Export PDF
                e.preventDefault();
                showToast("Exporting Tactical Briefing (E)");
                downloadDecisionReportPdf();
                break;
            case '/': // Toggle Foresight
                e.preventDefault();
                toggleForesight();
                break;
            case 'b': // Toggle Sidebar
                e.preventDefault();
                toggleSidebar();
                break;
        }
    });

    if (window.lucide) lucide.createIcons();
});
