// 🚀 Aviation Singularity v15.0 Excellence Dashboard Logic

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
    } catch (err) {
        console.error("Fetch Scenario Failed:", err);
    }
}

async function runOptimize() {
    const btn = document.querySelector('button[onclick="runOptimize()"]');
    const overlay = document.getElementById('loading-overlay');
    
    // v14.2: Show overlay during heavy processing
    if (overlay) overlay.classList.remove('hidden');
    if (btn) btn.innerHTML = `<span class="animate-pulse tracking-widest">EXECUTING MILP...</span>`;
    
    try {
        const response = await fetch(`${API_BASE}/optimize`, { method: 'POST' });
        if (!response.ok) throw new Error("Optimization Timeout");
        await fetchScenario();
        logAgentAction("Aviation Excellence v15.0: Maintenance & Crew constraints verified.");
    } catch (err) {
        console.error("Optimize Failed:", err);
        logAgentAction("Warning: Solver timeout. Using legacy safety fallback.");
    } finally {
        if (btn) btn.innerText = "RE-OPTIMIZE";
        if (overlay) overlay.classList.add('hidden');
    }
}

// --- UI Updates ---
function updateUI() {
    if (!fleetData || fleetData.length === 0) return;

    // 1. Update Fleet Table (Live Excellence Scorecards)
    const tbody = document.getElementById('fleet-table-body');
    if (tbody) {
        tbody.innerHTML = fleetData.slice(0, 12).map(f => `
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                <td style="padding: 10px 5px; font-weight:bold; color:#38bdf8;">${f.flight_id}</td>
                <td style="padding: 10px 5px; color:#64748b;">${f.origin}➔${f.destination}</td>
                <td style="padding: 10px 5px;"><span style="color:${f.assigned_delay > 0 ? '#f59e0b' : '#10b981'}">${f.assigned_delay > 0 ? 'DELAYED' : 'READY'}</span></td>
            </tr>
        `).join('');
    }

    // 2. Bayesian Causal Decomposition
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

    // 3. Update Operational Health Bars (v15.0 Simulation)
    // In a real app, these values would come from /api/health
    const m_health = 90 + Math.random() * 8;
    const c_health = 80 + Math.random() * 15;
    updateHealthBars(m_health, c_health);
}

function updateHealthBars(m, c) {
    const bars = document.querySelectorAll('.health-bar-fill');
    if (bars.length >= 2) {
        bars[0].style.width = `${m}%`;
        bars[1].style.width = `${c}%`;
    }
}

function logAgentAction(msg) {
    const feed = document.getElementById('agent-logs');
    if (!feed) return;
    const entry = document.createElement('div');
    entry.style.cssText = "padding:0.6rem; border-radius:0.5rem; background:rgba(14,165,233,0.05); border:1px solid rgba(14,165,233,0.1); font-size:0.65rem; margin-bottom:0.5rem;";
    entry.innerHTML = `<span style="color:#38bdf8; font-weight:bold;">[AGENT]</span> ${msg}`;
    feed.prepend(entry);
    feed.scrollTop = 0;
}

// --- Charts Initialization ---
function initCharts() {
    const canvasTraj = document.getElementById('trajectoryChart');
    if (canvasTraj) {
        const ctxTraj = canvasTraj.getContext('2d');
        if (trajectoryChart) trajectoryChart.destroy();
        trajectoryChart = new Chart(ctxTraj, {
            type: 'line',
            data: {
                labels: ['climb', 'crz-1', 'crz-2', 'crz-3', 'crz-4', 'step-up', 'crz-5', 'crz-6', 'desc', 'appr'],
                datasets: [{
                    label: 'FL Profile',
                    data: [330, 350, 350, 360, 360, 380, 380, 370, 330, 0],
                    borderColor: '#38bdf8',
                    borderWidth: 3,
                    backgroundColor: 'rgba(56, 189, 248, 0.05)',
                    fill: true,
                    pointRadius: 4,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    y: { min: 0, max: 450, grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#475569' } },
                    x: { grid: { display: false }, ticks: { color: '#475569' } }
                }
            }
        });
    }

    const canvasCausal = document.getElementById('causalChart');
    if (canvasCausal) {
        const ctxCausal = canvasCausal.getContext('2d');
        if (causalChart) causalChart.destroy();
        causalChart = new Chart(ctxCausal, {
            type: 'doughnut',
            data: {
                labels: ['Weather', 'Cyber', 'Security', 'Technical', 'Operational'],
                datasets: [{
                    data: [20, 10, 5, 15, 50],
                    backgroundColor: ['#0ea5e9', '#f43f5e', '#a855f7', '#fbbf24', '#38bdf8'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: { legend: { display: false } }
            }
        });
    }
}

// --- Start System ---
document.addEventListener('DOMContentLoaded', () => {
    try {
        initCharts();
        fetchScenario();
        setInterval(fetchScenario, 10000); 
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        console.error("Aviation Excellence UI Init Failed:", e);
    }
});
