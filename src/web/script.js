const API_BASE = "/api";

// v26.0: Global Error Bridge
window.onerror = function(msg, url, lineNo, columnNo, error) {
    const errorMsg = `[CRITICAL JS] ${msg} (Line: ${lineNo})`;
    if (typeof logAction === 'function') logAction(errorMsg);
    console.error(errorMsg, error);
    return false;
};

// --- State Management ---
let fleetData = [];
let trajectoryChart;
let causalChart;
let viewMode = '2D'; // '2D' or '3D'

// v32.0: Mapping Constants for MapLibre (Mercator)
let map;
let aircraftLayer;
let customLayer;

// v32.0: AI Global State
let evolutionStats = { xp: 0, cycles: 0, status: 'Stable' };

let scene, camera, renderer;
let aircraftMarkers = {}; // {flight_id: {mesh: Mesh}}
let lastNarrative = "";
let isForesightActive = false;
let foresightInterval = null;

// v34.0: Tactical Typewriter Effect for Gemma Reports
function typeWriter(elementId, text, speed = 30) {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.innerHTML = "";
    let i = 0;
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
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

// --- API Calls ---
async function fetchScenario() {
    try {
        const response = await fetch(`${API_BASE}/scenario`);
        if (!response.ok) throw new Error("API Offline");
        fleetData = await response.json();
        updateUI();
        fetchKPIs();
        if (viewMode === '3D') update3DMarkers();
    } catch (err) {
        console.error("Fetch Scenario Failed:", err);
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

async function syncLive() {
    logAction("Syncing with OpenSky & Live Radar nodes...");
    const badge = document.getElementById('sync-status-badge');
    if (badge) badge.innerText = "SYNCING...";
    
    try {
        const response = await fetch(`${API_BASE}/sync/live-traffic`);
        const data = await response.json();
        
        if (data.active_flights) {
            logAction(`Live Radar: ${data.count} aircraft tracked over IST hub.`);
            if (badge) badge.innerText = "LIVE SYNCED";
            updateLive3DMarkers(data.active_flights);
        }
    } catch (err) {
        logAction("Sync Error: ADS-B node unreachable.");
        if (badge) badge.innerText = "OFFLINE";
    }
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

        const geometry = new THREE.ConeGeometry(800, 2200, 4); 
        const material = new THREE.MeshPhongMaterial({ 
            color: f.status === "DELAYED" ? 0xf43f5e : 0x0ea5e9,
            emissive: f.status === "DELAYED" ? 0xf43f5e : 0x0ea5e9,
            emissiveIntensity: 0.8,
            transparent: true,
            opacity: 0.95
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(lonOffset, latOffset, alt);
        mesh.rotateX(Math.PI / 2);
        mesh.rotation.z = - (f.heading * Math.PI / 180);
        
        // Internal tactical pulse effect data
        mesh.userData = { 
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
        const response = await fetch(`${API_BASE}/evolution/summary`);
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
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.remove('hidden');
    
    // v17.1: Frontend Safeguard Timeout (40s)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        controller.abort();
        logAction("OPTIMIZATION TIMEOUT: Server reached max processing time.");
    }, 40000); 

    try {
        const response = await fetch(`${API_BASE}/optimize`, { 
            method: 'POST',
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        const result = await response.json();
        await fetchScenario();

        if (result.status === "success") {
            logAction(`Success: ${result.message}`);
        } else if (result.status === "partial_success") {
            logAction(`Alert: ${result.message}`);
        }
        
    } catch (err) {
        if (err.name === 'AbortError') {
            logAction("Optimization Aborted (Timeout). Baseline plan restored.");
        } else {
            console.error("Optimization Failed:", err);
            logAction("Critical Error during optimization. Check network.");
        }
    } finally {
        if (overlay) overlay.classList.add('hidden');
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
        const response = await fetch(`${API_BASE}/stress-test`, { method: 'POST' });
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
            const time = Date.now() * 0.001;
            
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
                    marker.mesh.scale.set(pulse, pulse, pulse);
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
            renderer.resetState();
            renderer.render(scene, camera);
            map.triggerRepaint();
        }
    };
    map.addLayer(customLayer);
    
    // v32.4: Trigger initial data sync as soon as the layer is ready
    setTimeout(() => {
        update3DMarkers();
        syncLive();
    }, 500);
}

// v32.0: Synchronize Scenario Aircraft markers with MapLibre
function update3DMarkers() {
    if (!scene || !map || !fleetData) return;

    // Clear existing static markers
    Object.keys(aircraftMarkers).forEach(id => {
        if (!id.startsWith('LIVE_')) {
            const marker = aircraftMarkers[id];
            if (marker.mesh) scene.remove(marker.mesh);
            delete aircraftMarkers[id];
        }
    });

    fleetData.forEach((f) => {
        // v32.5: Accurate Metric Scaling for IST
        const lonOffset = (f.lon - 28.74) * 83500; 
        const latOffset = (f.lat - 41.27) * 111320;
        const alt = 2500; 

        const geometry = new THREE.ConeGeometry(1000, 3000, 4); 
        const material = new THREE.MeshPhongMaterial({ 
            color: f.assigned_delay > 0 ? 0xf43f5e : 0xa855f7, // Purple for scenario
            transparent: true,
            opacity: 0.8,
            emissive: f.assigned_delay > 0 ? 0xf43f5e : 0x7e22ce,
            emissiveIntensity: 0.6
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(lonOffset, latOffset, alt);
        mesh.rotateX(Math.PI / 2);
        mesh.rotation.z = Math.PI / 4; 
        
        mesh.userData = { 
            baseScale: 1.0, 
            pulseSpeed: 1 + Math.random() 
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
            }
        }
    }
}

// --- UI Logic ---
function updateUI() {
    const tbody = document.getElementById('fleet-table-body');
    if (tbody) {
        tbody.innerHTML = fleetData.slice(0, 8).map(f => `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                <td style="padding: 10px 5px; font-weight:bold; color:#38bdf8;">${f.flight_id}</td>
                <td style="padding: 10px 5px; color:#f8fafc;">${(f.load_factor * 100).toFixed(0)}%</td>
                <td style="padding: 10px 5px;"><span style="color:${f.assigned_delay > 0 ? '#f43f5e' : '#10b981'}">${f.assigned_delay > 0 ? 'DELAY' : 'OPTIMAL'}</span></td>
            </tr>
        `).join('');
    }

    const causes = fleetData.reduce((acc, f) => {
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
        const response = await fetch(`${API_BASE}/analytics/forecast`);
        if (!response.ok) return;
        const data = await response.json();
        updateForecastUI(data);
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

// --- Start System ---
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchScenario();
    fetchForecast();
    updateAIBriefing(); // v34.0: Initial Neural Uplink
    
    setInterval(() => {
        fetchScenario();
        fetchForecast();
        updateEvolutionStats();
    }, 15000); 
    
    setInterval(updateEvolutionStats, 5000); // Faster polling for XP
    setInterval(updateAIBriefing, 60000);    // v34.0: 60s Cognitive Heartbeat
    
    if (window.lucide) lucide.createIcons();
});
