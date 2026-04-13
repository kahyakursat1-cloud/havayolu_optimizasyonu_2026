// 🚀 Aviation Singularity v17.0 "Quantum Finale" Command Logic

const API_BASE = "/api";

// --- State Management ---
let fleetData = [];
let trajectoryChart;
let causalChart;
let viewMode = '2D'; // '2D' or '3D'

// Three.js Globals
let scene, camera, renderer, globe;
let aircraftMarkers = {}; // {flight_id: mesh}
let pathLines = {}; // {flight_id: line}

const CITY_COORDS = {
    'IST': [0, 0],
    'ADB': [-30, -20],
    'AYT': [20, -30],
    'ESB': [40, 5],
    'LHR': [-120, 80],
    'CDG': [-100, 60],
    'FRA': [-80, 70],
    'JFK': [-300, 40],
    'DXB': [120, -40]
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
    logAction("Syncing with OpenSky & METAR nodes...");
    try {
        const response = await fetch(`${API_BASE}/sync/live`);
        const result = await response.json();
        document.getElementById('sync-status-badge').innerText = "LIVE SYNCED";
        logAction(`Live Traffic Detected: ${result.traffic.active_icao_count} AC in TR-Airspace.`);
        logAction(`IST Weather: ${result.weather.metar}`);
    } catch (err) {
        logAction("Live Sync Error: API Link Timeout.");
    }
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
    
    // v17.3 Fix: Ensure size is calculated after potential layout shifts
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    const grid = new THREE.GridHelper(400, 40, 0x334155, 0x1e293b);
    grid.rotation.x = Math.PI / 2;
    scene.add(grid);

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const light = new THREE.PointLight(0x0ea5e9, 1.5, 500);
    light.position.set(0, 0, 100);
    scene.add(light);

    camera.position.set(0, -120, 180);
    camera.lookAt(0, 0, 0);

    animateThree();
}

function animateThree() {
    requestAnimationFrame(animateThree);
    if (renderer && scene && camera) {
        renderer.render(scene, camera);
    }
}

function drawFlightPath(flight_id, origin, dest) {
    if (pathLines[flight_id]) return;
    const start = CITY_COORDS[origin] || [0, 0];
    const end = CITY_COORDS[dest] || [50, 50];
    const points = [];
    points.push(new THREE.Vector3(start[0], start[1], 0));
    const midX = (start[0] + end[0]) / 2;
    const midY = (start[1] + end[1]) / 2;
    points.push(new THREE.Vector3(midX, midY, 20));
    points.push(new THREE.Vector3(end[0], end[1], 0));
    const curve = new THREE.CatmullRomCurve3(points);
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(20));
    const material = new THREE.LineBasicMaterial({ color: 0x0ea5e9, transparent: true, opacity: 0.3 });
    const line = new THREE.Line(geometry, material);
    scene.add(line);
    pathLines[flight_id] = line;
}

function update3DMarkers() {
    if (!scene || !fleetData) return;
    
    fleetData.forEach((f) => {
        const origin = CITY_COORDS[f.origin] || [0, 0];
        const dest = CITY_COORDS[f.destination] || [10, 10];
        drawFlightPath(f.flight_id, f.origin, f.destination);

        if (!aircraftMarkers[f.flight_id]) {
            const geometry = new THREE.ConeGeometry(2, 6, 3);
            const material = new THREE.MeshPhongMaterial({ 
                color: f.assigned_delay > 0 ? 0xf43f5e : 0x0ea5e9,
                emissive: f.assigned_delay > 0 ? 0x991b1b : 0x075985,
                emissiveIntensity: 0.5
            });
            const mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);
            aircraftMarkers[f.flight_id] = mesh;
        }
        
        const mesh = aircraftMarkers[f.flight_id];
        const progress = (f.load_factor || 0.5) * 0.8; 
        const posX = origin[0] + (dest[0] - origin[0]) * progress;
        const posY = origin[1] + (dest[1] - origin[1]) * progress;
        const posZ = 15;

        mesh.position.set(posX, posY, posZ);
        mesh.lookAt(new THREE.Vector3(dest[0], dest[1], 0));
        mesh.rotateX(Math.PI / 2);
        
        if (f.assigned_delay > 0) {
            mesh.scale.setScalar(1 + Math.sin(Date.now() * 0.005) * 0.2);
        } else {
            mesh.scale.setScalar(1);
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

// --- Start System ---
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchScenario();
    setInterval(fetchScenario, 15000); 
    if (window.lucide) lucide.createIcons();
});
