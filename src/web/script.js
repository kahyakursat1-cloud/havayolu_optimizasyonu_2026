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
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    // Add a simple grid/base representing the airspace
    const grid = new THREE.GridHelper(200, 20, 0x334155, 0x1e293b);
    grid.rotation.x = Math.PI / 2;
    scene.add(grid);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    const pointLight = new THREE.PointLight(0x0ea5e9, 1);
    pointLight.position.set(50, 50, 50);
    scene.add(pointLight);

    camera.position.z = 100;
    camera.position.y = -50;
    camera.lookAt(0, 0, 0);

    animateThree();
}

function animateThree() {
    requestAnimationFrame(animateThree);
    renderer.render(scene, camera);
}

function update3DMarkers() {
    if (!scene) return;
    
    fleetData.forEach((f, idx) => {
        if (!aircraftMarkers[f.flight_id]) {
            const geometry = new THREE.ConeGeometry(1, 4, 3);
            const material = new THREE.MeshPhongMaterial({ color: f.assigned_delay > 0 ? 0xf43f5e : 0x0ea5e9 });
            const mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);
            aircraftMarkers[f.flight_id] = mesh;
        }
        
        // Mock positioning aircraft in a row for demo visual
        const mesh = aircraftMarkers[f.flight_id];
        const x = (idx % 10) * 15 - 75;
        const y = Math.floor(idx / 10) * 15 - 75;
        const z = 10 + (f.assigned_delay ? -5 : 0);
        mesh.position.set(x, y, z);
        mesh.rotation.z += 0.02;
    });
}

function setViewMode(mode) {
    viewMode = mode;
    document.getElementById('toggle-2d').classList.toggle('active', mode === '2D');
    document.getElementById('toggle-3d').classList.toggle('active', mode === '3D');
    document.getElementById('three-container').classList.toggle('hidden', mode === '2D');
    
    if (mode === '3D' && !scene) initThreeScene();
    if (mode === '3D') update3DMarkers();
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
