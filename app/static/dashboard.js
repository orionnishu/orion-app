// --------------------
// Globals
// --------------------
const BASE_PATH = window.BASE_PATH || '';
let cpuTempChart;
let ramChart;
let cpuStressChart;
let fanChart;
let roomTempChart;
let roomHumidityChart;

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
      if (value <= 52) return colors.green;
      if (value <= 70) return colors.orange;
      return colors.red;

    case "cpu_stress":
      if (value <= 0.4) return colors.green;
      if (value <= 0.8) return colors.orange;
      return colors.red;

    case "ram_used":
      if (value <= 2000) return colors.green;
      if (value <= 3000) return colors.orange;
      return colors.red;

    case "fan_rpm":
      if (value <= 3000) return colors.green;
      if (value <= 4500) return colors.orange;
      return colors.red;

    case "disk_usage":
      if (value <= 60) return colors.green;
      if (value <= 80) return colors.orange;
      return colors.red;

    case "room_temp":
      if (value >= 18 && value <= 30) return colors.green;
      if ((value >= 10 && value < 18) || (value > 30 && value <= 35)) return colors.orange;
      return colors.red;

    case "room_humidity":
      if (value >= 30 && value <= 60) return colors.green;
      if ((value >= 20 && value < 30) || (value > 60 && value <= 70)) return colors.orange;
      return colors.red;

    default:
      return colors.blue;
  }
}

// Y-axis ranges per metric
const Y_AXIS_RANGES = {
  cpu_temp: { min: 30, max: 85 },
  cpu_stress: { min: 0, max: 2 },
  ram_used: { min: 0, max: 4096 },
  fan_rpm: { min: 0, max: 6000 },
  room_temp: { min: 10, max: 40 },
  room_humidity: { min: 0, max: 100 },
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
  cpuStressChart = createLineChart("cpuStressChart", "CPU Stress", "cpu_stress");
  cpuTempChart = createLineChart("cpuTempChart", "CPU Temp (°C)", "cpu_temp");
  ramChart = createLineChart("ramChart", "RAM Used (MB)", "ram_used");
  fanChart = createLineChart("fanChart", "Fan RPM", "fan_rpm");
  roomTempChart = createLineChart("roomTempChart", "Room Temp (°C)", "room_temp");
  roomHumidityChart = createLineChart("roomHumidityChart", "Humidity (%)", "room_humidity");
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
        if (metricName === 'ram_used') {
          // Show GB / Total (4GB actual)
          valEl.innerHTML = `${(latest / 1000).toFixed(1)} <span class="stat-total">/ 4.0 GB</span>`;
        } else if (metricName === 'cpu_stress') {
          valEl.textContent = latest.toFixed(2);
        } else {
          valEl.textContent = latest.toFixed(1);
        }
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
  updateChart(cpuStressChart, BASE_PATH + "/api/metrics/cpu-stress", "cpu_stress", "val-cpu-stress");
  updateChart(cpuTempChart, BASE_PATH + "/api/metrics/cpu-temp", "cpu_temp", "val-cpu-temp");
  updateChart(ramChart, BASE_PATH + "/api/metrics/ram-used", "ram_used", "val-ram-used");
  updateChart(fanChart, BASE_PATH + "/api/metrics/fan-rpm", "fan_rpm", "val-fan-rpm");
  updateChart(roomTempChart, BASE_PATH + "/api/metrics/room-temp", "room_temp", "val-room-temp");
  updateChart(roomHumidityChart, BASE_PATH + "/api/metrics/room-humidity", "room_humidity", "val-room-humidity");
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
