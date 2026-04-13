// 🚀 Aviation Singularity v14.0 Dashboard Logic

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
    if (btn) btn.innerHTML = `<span class="animate-pulse tracking-widest">OPTIMIZING...</span>`;
    
    try {
        const response = await fetch(`${API_BASE}/optimize`, { method: 'POST' });
        if (!response.ok) throw new Error("Optimization Timeout");
        await fetchScenario();
        logAgentAction("Fleet-wide windowed optimization complete. New schedule z-signed.");
    } catch (err) {
        console.error("Optimize Failed:", err);
        logAgentAction("Warning: Optimization engine timeout. Using ACR recovery.");
    } finally {
        if (btn) btn.innerText = "RE-OPTIMIZE";
        if (overlay) overlay.classList.add('hidden');
    }
}

// --- UI Updates ---
function updateUI() {
    if (!fleetData || fleetData.length === 0) return;

    // Populate Fleet Table
    const tbody = document.getElementById('fleet-table-body');
    if (tbody) {
        tbody.innerHTML = fleetData.slice(0, 15).map(f => `
            <tr class="hover:bg-white/5 transition-colors group">
                <td class="py-3 px-2 font-bold text-sky-400 font-mono">${f.flight_id || 'N/A'}</td>
                <td class="py-2 px-2 text-slate-400 text-[10px]">${f.origin} ➔ ${f.destination}</td>
                <td class="py-3 px-2 text-slate-300 font-mono text-[10px]">${f.pax_connection_count || 0} pax</td>
            </tr>
        `).join('');
    }

    // Update charts if data exists
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

function logAgentAction(msg) {
    const feed = document.getElementById('agent-logs');
    if (!feed) return;
    const entry = document.createElement('div');
    entry.className = "p-3 rounded-lg bg-sky-500/5 border border-slate-800 text-[10px] animate-in fade-in slide-in-from-bottom duration-500 mb-2";
    entry.innerHTML = `<span class="text-sky-400 font-bold">[AGENT]</span> ${msg}`;
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
                    label: 'Optimal Altitude (FL)',
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
                    y: { min: 0, max: 450, grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#64748b' } },
                    x: { grid: { display: false }, ticks: { color: '#64748b' } }
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
                labels: ['Weather', 'Cyber', 'Security', 'Tech', 'Operational'],
                datasets: [{
                    data: [25, 15, 10, 20, 30],
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
        setInterval(fetchScenario, 8000); 
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        console.error("Singularity UI Init Failed:", e);
    }
});
