// 🚀 Aviation Singularity v14.0 Dashboard Logic

const API_BASE = "http://localhost:8504/api";

// --- State Management ---
let fleetData = [];
let trajectoryChart;
let causalChart;

// --- API Calls ---
async function fetchScenario() {
    try {
        const response = await fetch(`${API_BASE}/scenario`);
        fleetData = await response.json();
        updateUI();
    } catch (err) {
        console.error("Fetch Scenario Failed:", err);
    }
}

async function runOptimize() {
    const btn = document.querySelector('button[onclick="runOptimize()"]');
    btn.innerHTML = `<span class="animate-pulse">OPTIMIZING...</span>`;
    
    try {
        await fetch(`${API_BASE}/optimize`, { method: 'POST' });
        await fetchScenario();
        logAgentAction("Fleet-wide windowed optimization complete.");
    } catch (err) {
        console.error("Optimize Failed:", err);
    } finally {
        btn.innerText = "RE-OPTIMIZE";
    }
}

// --- UI Updates ---
function updateUI() {
    if (!fleetData || fleetData.length === 0) return;

    // Populate Fleet Table
    const tbody = document.getElementById('fleet-table-body');
    tbody.innerHTML = fleetData.slice(0, 15).map(f => `
        <tr class="hover:bg-white/5 transition-colors group">
            <td class="py-3 px-2 font-bold text-sky-400 font-mono">${f.flight_id || 'N/A'}</td>
            <td class="py-2 px-2 text-slate-400 text-[10px]">${f.origin} ➔ ${f.destination}</td>
            <td class="py-3 px-2 text-slate-300 font-mono text-[10px]">${f.pax_connection_count || 0} pax</td>
        </tr>
    `).join('');

    // Update charts if data exists
    const causes = fleetData.reduce((acc, f) => {
        const factor = f.causal_factor || 'Operational';
        acc[factor] = (acc[factor] || 0) + 1;
        return acc;
    }, {});
    updateCausalChart(Object.keys(causes), Object.values(causes));
}

function logAgentAction(msg) {
    const feed = document.getElementById('agent-logs');
    const entry = document.createElement('div');
    entry.className = "p-3 rounded-lg bg-sky-500/5 border border-slate-800 text-[10px] animate-in fade-in slide-in-from-bottom duration-500 mb-2";
    entry.innerHTML = `<span class="text-sky-400 font-bold">[AGENT]</span> ${msg}`;
    feed.prepend(entry);
    // Auto-scroll logic if needed
    feed.scrollTop = 0;
}

// --- Charts Initialization ---
function initCharts() {
    const ctxTraj = document.getElementById('trajectoryChart').getContext('2d');
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
                pointBackgroundColor: '#38bdf8',
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { 
                y: { 
                    suggestedMin: 0, suggestedMax: 450,
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { color: '#64748b', font: { size: 10 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#64748b', font: { size: 9 } }
                }
            }
        }
    });

    const ctxCausal = document.getElementById('causalChart').getContext('2d');
    causalChart = new Chart(ctxCausal, {
        type: 'doughnut',
        data: {
            labels: ['Weather', 'Cyber', 'Security', 'Tech', 'Operational'],
            datasets: [{
                data: [25, 15, 10, 20, 30],
                backgroundColor: ['#38bdf8', '#f43f5e', '#a855f7', '#fbbf24', '#0ea5e9'],
                borderWidth: 0,
                hoverOffset: 10
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

function updateCausalChart(labels, values) {
    causalChart.data.labels = labels;
    causalChart.data.datasets[0].data = values;
    causalChart.update();
}

// --- Start System ---
window.onload = () => {
    initCharts();
    fetchScenario();
    setInterval(fetchScenario, 5000); // Polling every 5s
};
