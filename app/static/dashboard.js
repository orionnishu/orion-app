// --------------------
// Globals
// --------------------
const BASE_PATH = window.BASE_PATH || '';
let cpuTempChart;
let ramChart;
let loadChart;
let fanChart;

const REFRESH_INTERVAL_MS = 30000;

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
    case "cpu_temp":
      if (value <= 50) return colors.green;
      if (value <= 68) return colors.orange;
      return colors.red;

    case "ram_used":
      if (value <= 2000) return colors.green;
      if (value <= 2800) return colors.orange;
      return colors.red;

    case "load_1m":
      if (value <= 1.0) return colors.green;
      if (value <= 2.4) return colors.orange;
      return colors.red;

    case "fan_rpm":
      if (value <= 2000) return colors.green;
      if (value <= 3500) return colors.orange;
      return colors.red;

    case "disk_usage":
      if (value <= 70) return colors.green;
      if (value <= 90) return colors.orange;
      return colors.red;

    default:
      return colors.blue;
  }
}

// --------------------
// Chart creation helper
// --------------------

function createLineChart(canvasId, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const ctx = canvas.getContext("2d");

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
        tension: 0.4,
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
          beginAtZero: false,
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
  cpuTempChart = createLineChart("cpuTempChart", "CPU Temp");
  ramChart = createLineChart("ramChart", "RAM Used");
  loadChart = createLineChart("loadChart", "Load Avg");
  fanChart = createLineChart("fanChart", "Fan RPM");
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
        valEl.textContent = metricName === 'load_1m' ? latest.toFixed(2) : latest.toFixed(1);
        valEl.style.color = theme.border;
      }
    }

    chart.update();
  } catch (err) {
    console.error(`Error updating ${metricName}:`, err);
  }
}

// --------------------
// Storage Status Helper
// --------------------
async function updateStorage() {
  try {
    const res = await fetch(BASE_PATH + '/api/storage/status');
    const disks = await res.json();
    const grid = document.getElementById('storage-grid');

    if (disks.error) throw new Error(disks.error);

    // Create labels for common mount points
    const labels = {
      '/': 'OS Disk',
      '/boot/firmware': 'Boot',
      '/mnt/orion-nas': 'NAS Storage'
    };

    grid.innerHTML = disks.map(disk => {
      const theme = getMetricTheme(disk.percent, 'disk_usage');
      const label = labels[disk.mount] || disk.mount;
      return `
        <div class="storage-card">
          <div class="storage-title">${label}</div>
          <div class="storage-mount-path">${disk.mount}</div>
          <div class="storage-bar-container">
            <div class="storage-bar-bg">
              <div class="storage-bar-fill" style="width: ${disk.percent}%; background-color: ${theme.simple}"></div>
            </div>
            <div class="storage-bar-labels">
              <span>${disk.used} used</span>
              <span>${disk.size} total</span>
            </div>
          </div>
          <div class="storage-percent" style="color: ${theme.simple}">${disk.percent}% full</div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Error updating storage:', err);
    document.getElementById('storage-grid').innerHTML = `<div class="error">Failed to load storage status</div>`;
  }
}


// --------------------
// Refresh all data
// --------------------
function refreshAll() {
  updateChart(cpuTempChart, BASE_PATH + "/api/metrics/cpu-temp", "cpu_temp", "val-cpu-temp");
  updateChart(ramChart, BASE_PATH + "/api/metrics/ram-used", "ram_used", "val-ram-used");
  updateChart(loadChart, BASE_PATH + "/api/metrics/load-1m", "load_1m", "val-load-1m");
  updateChart(fanChart, BASE_PATH + "/api/metrics/fan-rpm", "fan_rpm", "val-fan-rpm");
  updateStorage();

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
