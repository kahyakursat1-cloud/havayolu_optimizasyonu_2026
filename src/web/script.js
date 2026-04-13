// 🚀 Aviation Singularity v17.0 "Quantum Finale" Command Logic

const API_BASE = "/api";

// --- State Management ---
let fleetData = [];
let trajectoryChart;
let causalChart;
let viewMode = '2D'; // '2D' or '3D'

// Three.js Globals
let scene, camera, renderer, controls;
let aircraftMarkers = {}; // {flight_id: {mesh: Mesh, tag: Sprite}}
let pathLines = {}; // {flight_id: line}

// v20.0 Geographic-to-Tactical Mapping (Origin: IST)
const SCALE_LAT = 15;
const SCALE_LON = 15;
const CITY_COORDS = {
    'IST': [0, 0], // Center
    'ADB': [(27.15 - 28.74) * SCALE_LON, (38.42 - 41.27) * SCALE_LAT],
    'AYT': [(30.71 - 28.74) * SCALE_LON, (36.88 - 41.27) * SCALE_LAT],
    'ESB': [(32.86 - 28.74) * SCALE_LON, (39.93 - 41.27) * SCALE_LAT],
    'LHR': [(-0.45 - 28.74) * SCALE_LON, (51.47 - 41.27) * SCALE_LAT],
    'CDG': [(2.55 - 28.74) * SCALE_LON, (49.0 - 41.27) * SCALE_LAT],
    'FRA': [(8.57 - 28.74) * SCALE_LON, (50.0 - 41.27) * SCALE_LAT],
    'JFK': [(-73.77 - 28.74) * SCALE_LON, (40.64 - 41.27) * SCALE_LAT],
    'DXB': [(55.36 - 28.74) * SCALE_LON, (25.25 - 41.27) * SCALE_LAT]
};

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

// v21.3: Real-Time ADS-B Marker Engine
function updateLive3DMarkers(liveFlights) {
    if (!scene) return;

    // Clean up existing live markers prefixed with 'LIVE_'
    Object.keys(aircraftMarkers).forEach(id => {
        if (id.startsWith('LIVE_')) {
            const marker = aircraftMarkers[id];
            if (marker.mesh) scene.remove(marker.mesh);
            if (marker.tag) scene.remove(marker.tag);
            delete aircraftMarkers[id];
        }
    });

    liveFlights.forEach(f => {
        const id = `LIVE_${f.flight_id}`;
        
        // Convert real Lat/Lon to Tactical Plane Coords (IST origin)
        const posX = (f.lon - 28.74) * SCALE_LON;
        const posY = (f.lat - 41.27) * SCALE_LAT;
        const posZ = 12 + (f.alt / 1500); 

        const geometry = new THREE.ConeGeometry(5, 12, 4);
        const material = new THREE.MeshPhongMaterial({ 
            color: 0x22c55e, // Emerald Green for LIVE traffic
            emissive: 0x14532d,
            emissiveIntensity: 0.5
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(posX, posY, posZ);
        mesh.rotateX(Math.PI / 2);
        
        // Align heading (OpenSky headings are degrees)
        mesh.rotation.z = - (f.heading * Math.PI / 180);
        
        scene.add(mesh);
        const tag = createAircraftTag(f.flight_id);
        tag.position.set(posX, posY + 12, posZ + 8);
        
        aircraftMarkers[id] = { mesh, tag };
    });
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

// --- 3D STRATEGIC VIEW (Three.js) ---
function initThreeScene() {
    const container = document.getElementById('three-container');
    if (!container) return;
    
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020617);
    
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 2000);
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    // v20.0: Tactical Interactive Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = true;
    controls.minDistance = 50;
    controls.maxDistance = 1500;
    
    // v20.0: Tactical World Map Plane with v21.1 Load Guard
    const loader = new THREE.TextureLoader();
    loader.load('assets/map_texture.png', 
        (texture) => {
            console.log("✅ Tactical Map Texture Loaded Successfully.");
            const mapGeo = new THREE.PlaneGeometry(3000, 3000);
            const mapMat = new THREE.MeshBasicMaterial({ map: texture, transparent: true, opacity: 0.8 });
            const mapPlane = new THREE.Mesh(mapGeo, mapMat);
            mapPlane.position.z = 0;
            scene.add(mapPlane);
        },
        undefined,
        (err) => {
            console.error("❌ Map Texture Load Failed:", err);
            // Fallback grid for visibility
            const fallbackGrid = new THREE.GridHelper(3000, 60, 0x1e293b, 0x0f172a);
            fallbackGrid.rotation.x = Math.PI / 2;
            scene.add(fallbackGrid);
        }
    );

    // v19.0: Strategic City Hubs & Labels
    Object.keys(CITY_COORDS).forEach(city => {
        const coords = CITY_COORDS[city];
        createCityLabel(city, coords[0], coords[1]);
        
        // Visual Anchor for Hubs
        const hubGeo = new THREE.RingGeometry(4, 6, 32);
        const hubMat = new THREE.MeshBasicMaterial({ color: city === 'IST' ? 0xa855f7 : 0x0ea5e9, side: THREE.DoubleSide, transparent: true, opacity: 0.5 });
        const ring = new THREE.Mesh(hubGeo, hubMat);
        ring.position.set(coords[0], coords[1], 1);
        scene.add(ring);
    });

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const light = new THREE.PointLight(0x0ea5e9, 2.5, 1000);
    light.position.set(0, 0, 250);
    scene.add(light);

    camera.position.set(0, 0, 800); 
    controls.update();

    animateThree();
}

// v19.0 City Label Sprite Helper
function createCityLabel(text, x, y) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 128; // Smaller for better performance
	canvas.height = 64;
    context.font = "Bold 24px 'Orbitron', sans-serif";
    context.textAlign = "center";
    context.fillStyle = text === 'IST' ? "#a855f7" : "#38bdf8";
    context.fillText(text, 64, 40);
    const texture = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(40, 20, 1);
    sprite.position.set(x, y + 10, 5);
    scene.add(sprite);
}

// v20.0 Aircraft Tag Sprite Helper
function createAircraftTag(flight_id) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 128;
    canvas.height = 64;
    context.font = "18px 'Orbitron', sans-serif";
    context.textAlign = "center";
    context.fillStyle = "#ffffff";
    context.fillText(flight_id, 64, 40);
    const texture = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(30, 15, 1);
    scene.add(sprite);
    return sprite;
}

function animateThree() {
    requestAnimationFrame(animateThree);
    if (renderer && scene && camera) {
        const time = Date.now() * 0.001;
        
        // v17.6 Pulsing Hub Effect
        if (hubGlow) {
            const s = 1 + Math.sin(time * 3) * 0.15;
            hubGlow.scale.set(s, s, 1);
            hubGlow.material.opacity = 0.4 + Math.sin(time * 3) * 0.2;
        }

        // v20.0: Update Controls
        if (controls) controls.update();

        // v18.0 Living Airspace: Animate aircraft along paths
        Object.keys(aircraftMarkers).forEach(id => {
            const marker = aircraftMarkers[id];
            const mesh = marker.mesh;
            const tag = marker.tag;

            // Slow tactical movement loop
            const progress = (time * 0.05 + parseFloat(id.split('_')[1] || 0) * 0.1) % 1.0;
            
            const flight = fleetData.find(f => f.flight_id === id);
            if (flight) {
                const start = CITY_COORDS[flight.origin] || [0, 0];
                const end = CITY_COORDS[flight.destination] || [10, 10];
                
                // Linear move on Tactical Map Plane
                const posX = start[0] + (end[0] - start[0]) * progress;
                const posY = start[1] + (end[1] - start[1]) * progress;
                const posZ = 5; 
                
                mesh.position.set(posX, posY, posZ);
                mesh.lookAt(new THREE.Vector3(end[0], end[1], posZ));
                mesh.rotateX(Math.PI / 2);
                
                // v20.0: Tag Following
                if (tag) {
                    tag.position.set(posX, posY + 8, posZ + 5);
                }

                // Shimmering Delay Effect
                if (flight.assigned_delay > 0) {
                    mesh.scale.setScalar(1.2 + Math.sin(time * 8) * 0.4);
                }
            }
        });

        renderer.render(scene, camera);
    }
}

function drawFlightPath(flight_id, origin, dest) {
    if (pathLines[flight_id]) return;
    const start = CITY_COORDS[origin] || [0, 0];
    const end = CITY_COORDS[dest] || [50, 50];
    
    // v17.6 Dynamic Arc Height
    const dist = Math.sqrt(Math.pow(end[0]-start[0], 2) + Math.pow(end[1]-start[1], 2));
    const arcHeight = Math.min(80, dist / 3);

    const points = [];
    points.push(new THREE.Vector3(start[0], start[1], 0));
    const midX = (start[0] + end[0]) / 2;
    const midY = (start[1] + end[1]) / 2;
    points.push(new THREE.Vector3(midX, midY, arcHeight));
    points.push(new THREE.Vector3(end[0], end[1], 0));
    
    const curve = new THREE.CatmullRomCurve3(points);
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(25));
    const material = new THREE.LineBasicMaterial({ 
        color: dist > 150 ? 0x0ea5e9 : 0x38bdf8, 
        transparent: true, 
        opacity: dist > 150 ? 0.6 : 0.2 
    });
    const line = new THREE.Line(geometry, material);
    scene.add(line);
    pathLines[flight_id] = line;
}

function update3DMarkers() {
    if (!scene || !fleetData) return;
    
    fleetData.forEach((f) => {
        if (!aircraftMarkers[f.flight_id]) {
            // v20.0 Aircraft Silhouette Mesh
            const geometry = new THREE.ConeGeometry(3, 8, 32); 
            const material = new THREE.MeshPhongMaterial({ 
                color: f.assigned_delay > 0 ? 0xf43f5e : 0xffd700, // Gold for active, Red for delay
                emissive: f.assigned_delay > 0 ? 0x991b1b : 0x075985,
                emissiveIntensity: 0.5
            });
            const mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);
            
            const tag = createAircraftTag(f.flight_id);
            aircraftMarkers[f.flight_id] = { mesh, tag };
        }
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
            if (!scene) initThreeScene();
            // v17.4: Force sync on switch
            if (renderer && camera) {
                const w = container.clientWidth;
                const h = container.clientHeight;
                renderer.setSize(w, h);
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                update3DMarkers();
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
    setInterval(() => {
        fetchScenario();
        fetchForecast();
    }, 15000); 
    if (window.lucide) lucide.createIcons();
});
