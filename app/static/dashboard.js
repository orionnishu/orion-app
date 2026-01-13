// --------------------
// Globals
// --------------------
let cpuTempChart;
let ramChart;
let loadChart;
let fanChart;

const REFRESH_INTERVAL_MS = 30000;

// Thresholds for coloring
function colorByThreshold(value, metric) {
  switch (metric) {
    case "cpu_temp":
      if (value <= 50) return "green";
      if (value <= 68) return "orange";
      return "red";

    case "ram_used":
      if (value <= 2000) return "green";
      if (value <= 2800) return "orange";
      return "red";

    case "load_1m":
      if (value <= 1.0) return "green";
      if (value <= 2.4) return "orange";
      return "red";

    case "fan_rpm":
      if (value <= 2000) return "green";
      if (value <= 3500) return "orange";
      return "red";

    default:
      return "blue";
  }
}


// --------------------
// Chart creation helper
// --------------------

function createLineChart(canvasId, label) {
  const ctx = document.getElementById(canvasId).getContext("2d");

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: label,
        data: [],
        borderWidth: 1,       // thinner lines
        tension: 0.25,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      animation: false,
      plugins: {
        legend: { display: true }
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 10 }
        }
      }
    }
  });
}

// --------------------
// Init charts once
// --------------------
function initCharts() {
  cpuTempChart = createLineChart("cpuTempChart", "CPU Temp (°C)");
  ramChart     = createLineChart("ramChart", "RAM Used (MB)");
  loadChart    = createLineChart("loadChart", "Load Avg (1m)");
  fanChart     = createLineChart("fanChart", "Fan RPM");
}

// --------------------
// Fetch + update helper
// --------------------
function updateChart(chart, endpoint, metricName) {
  const window = document.getElementById("timeWindow").value;

  fetch(`${endpoint}?window=${window}`)
    .then(res => res.json())
    .then(data => {
      chart.data.labels = data.labels;
      chart.data.datasets[0].data = data.values;

      if (data.values.length > 0) {
        const latest = data.values[data.values.length - 1];
        const color = colorByThreshold(latest, metricName);

        chart.data.datasets[0].borderColor = color;
        chart.data.datasets[0].backgroundColor = color + "33"; // light tint
      }

      chart.update();
    });
}


// --------------------
// Refresh all charts
// --------------------
function refreshAllCharts() {
  updateChart(cpuTempChart, "/api/metrics/cpu-temp", "cpu_temp");
  updateChart(ramChart, "/api/metrics/ram-used", "ram_used");
  updateChart(loadChart, "/api/metrics/load-1m", "load_1m");
  updateChart(fanChart, "/api/metrics/fan-rpm", "fan_rpm");

  const ts = new Date().toLocaleTimeString();
  const el = document.getElementById("last-updated");
  if (el) el.textContent = `Last updated: ${ts}`;
}

// --------------------
// Bootstrapping
// --------------------
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  refreshAllCharts(); // initial load

  // auto-refresh every 5s
  setInterval(refreshAllCharts, REFRESH_INTERVAL_MS);

  // refresh immediately when timeframe changes
  document
    .getElementById("timeWindow")
    .addEventListener("change", refreshAllCharts);
});
