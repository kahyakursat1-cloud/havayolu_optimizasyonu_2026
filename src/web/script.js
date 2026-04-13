// 🚀 Digital Airline Analyst v16.0 Command Logic

const API_BASE = "/api";

// --- State Management ---
let fleetData = [];
let trajectoryChart;
let causalChart;

// --- API Calls ---
async function fetchScenario() {
    try {
        const response = await fetch(`${API_BASE}/scenario`);
        if (!response.ok) throw new Error("API Offline");
        fleetData = await response.json();
        updateUI();
        fetchKPIs();
    } catch (err) {
        console.error("Fetch Scenario Failed:", err);
    }
}

async function fetchKPIs() {
    try {
        const response = await fetch(`${API_BASE}/analytics/kpi`);
        if (!response.ok) return;
        const kpis = await response.json();
        
        // Update Side Cards
        document.getElementById('kpi-plf').innerText = `${kpis.plf}%`;
        document.getElementById('kpi-ask').innerText = (kpis.ask / 1e6).toFixed(1) + "M";
        document.getElementById('kpi-rpk').innerText = (kpis.rpk / 1e6).toFixed(1) + "M";
        document.getElementById('kpi-cqi').innerText = kpis.cqi;
        
        // Update Progress Bars
        document.getElementById('bar-ask').style.width = "100%";
        document.getElementById('bar-rpk').style.width = `${kpis.plf}%`;
    } catch (err) {
        console.error("KPI Sync Failed");
    }
}

async function runOptimize() {
    const btn = document.querySelector('button[onclick="runOptimize()"]');
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/optimize`, { method: 'POST' });
        await fetchScenario();
        logAnalystAction("Global Optimization complete. PLF refined for O&D pairs.");
    } finally {
        if (overlay) overlay.classList.add('hidden');
    }
}

async function triggerStressTest() {
    const overlay = document.getElementById('loading-overlay');
    const badge = document.getElementById('recovery-badge');
    const overlayText = document.getElementById('overlay-text');
    
    if (overlay) {
        overlayText.innerText = "SHOCK DETECTED. RECOVERY AGENT DEPLOYING...";
        overlay.classList.remove('hidden');
    }
    
    try {
        const response = await fetch(`${API_BASE}/stress-test`, { method: 'POST' });
        if (badge) badge.classList.remove('hidden');
        await fetchScenario();
        logAnalystAction("CRITICAL: Mass Delay detected at IST hub. Re-routing legs in progress.");
        
        // Hide badge after 10s
        setTimeout(() => badge.classList.add('hidden'), 10000);
    } finally {
        if (overlay) overlay.classList.add('hidden');
    }
}

// --- UI Updates ---
function updateUI() {
    if (!fleetData || fleetData.length === 0) return;

    // 1. Update Fleet Table
    const tbody = document.getElementById('fleet-table-body');
    if (tbody) {
        tbody.innerHTML = fleetData.slice(0, 10).map(f => `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                <td style="padding: 10px 5px; font-weight:bold; color:#38bdf8;">${f.flight_id}</td>
                <td style="padding: 10px 5px; color:#f8fafc;">${(f.load_factor * 100).toFixed(0)}%</td>
                <td style="padding: 10px 5px;"><span style="color:${f.saf_usage > 0 ? '#a855f7' : '#10b981'}">${f.saf_usage > 0 ? 'SAF+' : 'ECO'}</span></td>
            </tr>
        `).join('');
    }

    // 2. Causal Analytics
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

function logAnalystAction(msg) {
    const feed = document.getElementById('agent-logs');
    if (!feed) return;
    const entry = document.createElement('div');
    entry.style.cssText = "padding:0.6rem; border-radius:0.5rem; background:rgba(56,189,248,0.05); border:1px solid rgba(14,165,233,0.1); font-size:0.65rem; margin-bottom:0.5rem;";
    entry.innerHTML = `<span style="color:#38bdf8; font-weight:bold;">[ANALIST]</span> ${msg}`;
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
                labels: ['T-4h', 'T-3h', 'T-2h', 'T-1h', 'NOW', 'T+1h', 'T+2h'],
                datasets: [{
                    label: 'Fleet Delay Spread',
                    data: [10, 15, 8, 12, 5, 20, 10],
                    borderColor: '#f43f5e',
                    backgroundColor: 'rgba(244, 63, 94, 0.1)',
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
                labels: ['Weather', 'Cyber', 'Security', 'Technical', 'Operational'],
                datasets: [{
                    data: [1, 1, 1, 1, 1],
                    backgroundColor: ['#0ea5e9', '#f43f5e', '#a855f7', '#fbbf24', '#38bdf8'],
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
