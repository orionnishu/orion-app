// --------------------
// Globals
// --------------------
const BASE_PATH = window.BASE_PATH || '';
let netPingChart;
let netLossChart;
let netLanChart;

const REFRESH_INTERVAL_MS = 60000;

// Colors
const colors = {
    green: {
        border: 'rgba(16, 185, 129, 1)',
        bg: 'rgba(16, 185, 129, 0.1)',
        simple: '#10b981'
    },
    orange: {
        border: 'rgba(245, 158, 11, 1)',
        bg: 'rgba(245, 158, 11, 0.1)',
        simple: '#f59e0b'
    },
    red: {
        border: 'rgba(239, 68, 68, 1)',
        bg: 'rgba(239, 68, 68, 0.1)',
        simple: '#ef4444'
    },
    blue: {
        border: 'rgba(37, 99, 235, 1)',
        bg: 'rgba(37, 99, 235, 0.1)',
        simple: '#2563eb'
    }
};

// Thresholds for coloring
function getMetricTheme(value, metric) {
    switch (metric) {
        case "net_ping":
            // 0 means unreachable
            if (value == 0) return colors.red;
            if (value <= 30) return colors.green;
            if (value <= 100) return colors.orange;
            return colors.red;

        case "net_loss":
            if (value == 0) return colors.green;
            if (value <= 5) return colors.orange;
            return colors.red;

        case "net_lan":
            if (value == 0) return colors.red;
            if (value <= 5) return colors.green;
            if (value <= 20) return colors.orange;
            return colors.red;

        default:
            return colors.blue;
    }
}

// Y-axis ranges per metric
const Y_AXIS_RANGES = {
    net_ping: { min: 0, max: null },
    net_loss: { min: 0, max: 100 },
    net_lan: { min: 0, max: null },
};

// --------------------
// Chart creation helper
// --------------------

function createLineChart(canvasId, label, metricName) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext("2d");

    const yRange = Y_AXIS_RANGES[metricName] || {};

    return new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderWidth: 2,
                borderColor: colors.blue.border,
                backgroundColor: colors.blue.bg,
                fill: true,
                tension: 0.1, // Less smooth for network metrics to see spikes better
                pointRadius: 0,
                pointHoverRadius: 4,
                pointBackgroundColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 500
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#111827',
                    bodyColor: '#4b5563',
                    borderColor: '#e5e7eb',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 6,
                        font: { size: 11, family: 'Inter, sans-serif' },
                        color: '#9ca3af'
                    }
                },
                y: {
                    min: yRange.min,
                    max: yRange.max,
                    grid: { color: '#f3f4f6' },
                    ticks: {
                        font: { size: 11, family: 'Inter, sans-serif' },
                        color: '#9ca3af',
                        padding: 8
                    }
                }
            }
        }
    });
}

// --------------------
// Init charts once
// --------------------
function initCharts() {
    netPingChart = createLineChart("netPingChart", "Internet Ping (ms)", "net_ping");
    netLossChart = createLineChart("netLossChart", "Packet Loss (%)", "net_loss");
    netLanChart = createLineChart("netLanChart", "LAN Latency (ms)", "net_lan");
}

// --------------------
// Fetch + update helper
// --------------------
async function updateChart(chart, endpoint, metricName, valueId) {
    if (!chart) return;
    const window = document.getElementById("timeWindow").value;

    try {
        const res = await fetch(`${endpoint}?window=${window}`);
        const data = await res.json();

        chart.data.labels = data.labels;
        chart.data.datasets[0].data = data.values;

        if (data.values.length > 0) {
            const latest = data.values[data.values.length - 1];
            const theme = getMetricTheme(latest, metricName);

            chart.data.datasets[0].borderColor = theme.border;
            chart.data.datasets[0].backgroundColor = theme.bg;

            // Update the overview card value
            const valEl = document.getElementById(valueId);
            if (valEl) {
                valEl.textContent = latest.toFixed(1);
                valEl.style.color = theme.border;
            }
        }

        chart.update();
    } catch (err) {
        console.error(`Error updating ${metricName}:`, err);
    }
}


// --------------------
// Refresh all data
// --------------------
function refreshAll() {
    updateChart(netPingChart, BASE_PATH + "/api/metrics/net-ping", "net_ping", "val-net-ping");
    updateChart(netLossChart, BASE_PATH + "/api/metrics/net-loss", "net_loss", "val-net-loss");
    updateChart(netLanChart, BASE_PATH + "/api/metrics/net-lan", "net_lan", "val-net-lan");

    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const el = document.getElementById("last-updated");
    if (el) el.textContent = `Last refreshed at ${ts}`;
}

// --------------------
// Bootstrapping
// --------------------
document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    refreshAll();

    // auto-refresh
    setInterval(refreshAll, REFRESH_INTERVAL_MS);

    // timeframe change event
    document.getElementById("timeWindow").addEventListener("change", refreshAll);
});
