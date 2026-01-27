/* =================================================
   Admin Page JS
   - PC status polling
   - JSON async admin actions
   - Unified log polling (2s)
================================================= */

/* ------------------------------
   PC Status Polling (existing)
------------------------------ */

async function refreshStatus() {
    try {
        const res = await fetch("/api/pc-status", {
            credentials: "same-origin"
        });
        const data = await res.json();

        const statusEl = document.getElementById("pc-status");
        const actionsEl = document.getElementById("actions");

        if (!statusEl || !actionsEl) return;

        actionsEl.innerHTML = "";

        if (data.online) {
            statusEl.textContent = "Online";
            statusEl.style.color = "green";

            actionsEl.innerHTML = `
                <button onclick="runAction('/admin/api/sleep-pc')">
                    Sleep Windows PC
                </button>
            `;
        } else {
            statusEl.textContent = "Offline";
            statusEl.style.color = "red";

            actionsEl.innerHTML = `
                <button onclick="runAction('/admin/api/wake-pc')">
                    Wake Windows PC
                </button>
            `;
        }
    } catch (err) {
        console.error("PC status check failed:", err);
    }
}

refreshStatus();
setInterval(refreshStatus, 10000);

/* ------------------------------
   JSON Async Admin Trigger
------------------------------ */

function runAction(url) {
    fetch(url, {
        method: "POST",
        credentials: "same-origin"
    }).catch(err => {
        console.error("Admin action failed:", err);
    });
}

/* ------------------------------
   Unified Admin Log Polling
------------------------------ */

const LOG_ENDPOINT = "/admin/logs?lines=1000";
const LOG_POLL_INTERVAL = 2000;

const logEl = document.getElementById("log-content");

async function pollLogs() {
    if (!logEl) return;

    try {
        const res = await fetch(LOG_ENDPOINT, {
            credentials: "same-origin"
        });
        const data = await res.json();

        logEl.textContent = data.lines;
        logEl.scrollTop = logEl.scrollHeight;
    } catch (err) {
        logEl.textContent = "Failed to read logs";
        console.error("Log polling failed:", err);
    }
}

pollLogs();
setInterval(pollLogs, LOG_POLL_INTERVAL);