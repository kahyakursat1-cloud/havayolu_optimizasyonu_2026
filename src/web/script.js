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
    // Populate Fleet Table
    const tbody = document.getElementById('fleet-table-body');
    tbody.innerHTML = fleetData.slice(0, 50).map(f => `
        <tr class="hover:bg-white/5 transition-colors group">
            <td class="py-3 px-2 font-bold text-sky-400">${f.flight_id}</td>
            <td class="py-3 px-2 text-slate-400">${f.destination}</td>
            <td class="py-3 px-2 text-slate-300 font-mono">${f.pax_connection_count} pax</td>
        </tr>
    `).join('');

    // Update Causal Chart (Mock for distribution)
    const causes = fleetData.reduce((acc, f) => {
        const factor = f.causal_factor || 'Unknown';
        acc[factor] = (acc[factor] || 0) + 1;
        return acc;
    }, {});
    updateCausalChart(Object.keys(causes), Object.values(causes));
}

function logAgentAction(msg) {
    const feed = document.getElementById('agent-logs');
    const entry = document.createElement('div');
    entry.className = "p-3 rounded-lg bg-sky-500/5 border border-sky-500/10 text-xs animate-in fade-in slide-in-from-left";
    entry.innerHTML = `<span class="text-sky-400 font-bold">[AGENT]</span> ${msg}`;
    feed.prepend(entry);
}

// --- Charts Initialization ---
function initCharts() {
    const ctxTraj = document.getElementById('trajectoryChart').getContext('2d');
    trajectoryChart = new Chart(ctxTraj, {
        type: 'line',
        data: {
            labels: [1,2,3,4,5,6,7,8,9,10],
            datasets: [{
                label: 'Optimal Altitude (FL)',
                data: [330, 340, 350, 360, 360, 350, 350, 360, 370, 350],
                borderColor: '#38bdf8',
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { display: true, beginAtZero: false, grid: { color: 'rgba(255,255,255,0.05)' } } }
        }
    });

    const ctxCausal = document.getElementById('causalChart').getContext('2d');
    causalChart = new Chart(ctxCausal, {
        type: 'polarArea',
        data: {
            labels: ['Weather', 'Cyber', 'Security', 'Tech'],
            datasets: [{
                data: [12, 19, 3, 5],
                backgroundColor: ['#38bdf8', '#f43f5e', '#a855f7', '#fbbf24']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { r: { grid: { color: 'rgba(255,255,255,0.05)' } } }
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
