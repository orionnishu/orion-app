# ORION System — Administrator Handbook

Welcome to the ORION Administrator Handbook. This document outlines the daily operations, monitoring, and administrative tasks for the ORION Hybrid Edge-Cloud architecture.

---

## 1. Quick Links & Dashboards

Access these interfaces from the local network or via the Tailscale VPN.

*   **Main Web Portal:** `http://192.168.0.103:8000` (Local) or `http://100.90.202.45:8000` (Tailscale)
*   **Admin Console:** `/admin`
    *   *Features:* Wake/Sleep the Windows PC, Provision/Delete WebDAV users, View Cluster State, Manually submit jobs to worker queues.
*   **System Health Dashboard:** `/dashboard`
    *   *Features:* Real-time Pi 5 charts (CPU, RAM, Disk, Temperature), Room Temperature/Humidity (via ESP32).
*   **Network Dashboard:** `/network`
    *   *Features:* Real-time ping and packet loss monitoring.
*   **Grafana (Advanced Metrics):** `http://100.117.244.106:3000`
    *   *Note:* Runs on the always-on Oracle Cloud VM (`cloud2-vm2`). Accessible *only* while connected to your Tailscale network.

***Note:** The FastAPI portals require HTTP Basic Authentication (Username: `orion`).*

---

## 2. Managing Machines (Start / Stop)

While the Job Scheduler handles worker VMs automatically, you can manually override or control any node using the unified CLI on the Raspberry Pi.

1.  SSH into the control plane (Raspberry Pi):
    ```bash
    ssh orion@192.168.0.103
    ```
2.  Use the `orion-node` tool:
    ```bash
    cd ~/server/scripts
    ./orion-node list
    ```

### Common Commands:
| Action | Command | What it does |
| :--- | :--- | :--- |
| **List Node Status** | `./orion-node list` | Shows all registered nodes and whether they are currently pingable on Tailscale. |
| **Wake Windows PC** | `./orion-node start desktop-pc` | Sends an MQTT command to the ESP32 relay; falls back to Wake-On-LAN broadcast. |
| **Sleep Windows PC** | `./orion-node stop desktop-pc` | Sends an MQTT command to the ESP32 relay; falls back to a remote SSH `schtasks` trigger. |
| **Start Cloud VM** | `./orion-node start cloud1-vm1` | Uses the OCI CLI to boot the Oracle Cloud instance. |
| **Stop Cloud VM** | `./orion-node stop cloud1-vm1` | Uses the OCI CLI to gracefully shut down the Oracle Cloud instance. |
| **Check Reachability** | `./orion-node status cloud2-vm2` | Performs a fast Tailscale ping to verify if the node is processing traffic. |

**Available Nodes:** `desktop-pc`, `cloud1-vm1` (Worker), `cloud2-vm1` (Worker), `cloud2-vm2` (Always-On Infra).

---

## 3. The Auto-Scaling Job Queue

The ORION system is designed to save cloud costs. Worker VMs (`cloud1-vm1` and `cloud2-vm1`) are kept **OFF** by default. They are entirely managed by the Pi.

### How it works:
1.  **Submit a task:** 
    *   Go to **Admin Console (`/admin`) -> Jobs tab**.
    *   Enter a bash command (e.g., `echo "Hello World"`) and select a queue (`large` or `medium`).
2.  **Auto-Boot:** The background `orion-scheduler` detects the new job. If the required VM is off, it automatically runs the OCI boot command.
3.  **Execution:** Once booted, the VM pulls the job, runs it, and saves the output to Redis.
4.  **Auto-Shutdown:** If the VM processes no jobs for **10 minutes**, it will call back to the Pi to automatically shut itself down.

*You rarely need to manage worker VMs manually; simply submit jobs to the queue.*

---

## 4. WebDAV User Management

You can easily grant users secure remote file access.

1.  Go to the **Admin Console -> Users tab**.
2.  Under **Add New User**, input a username (alphanumeric) and password.
3.  Click **Add User**. The Pi will automatically:
    *   Create their secure `$htpasswd` entry.
    *   Create their private directory in `/mnt/orion-nas/users/<username>`.
    *   Set correctly scoped Nginx permissions.
4.  Users can connect via any WebDAV client at `http://<pi-ip>/users/<username>`.
5.  **To Remove:** Click the red "Delete" button next to their name. (You can choose to preserve or permanently delete their files).

---

## 5. Troubleshooting & Underlying Services

If something stops working, check these underlying systemd/Docker services.

### On the Raspberry Pi (Control Plane)
```bash
# Check the main web application UI/API
sudo systemctl status orion-webapp

# Check the auto-scaler scheduler (watches queues to boot VMs)
sudo systemctl status orion-scheduler

# Check the local Redis replica (syncs from the cloud)
sudo systemctl status redis-server
```

### On `cloud2-vm2` (Always-On Cloud Infra)
This machine runs the central job queue (Redis) and metrics monitoring.
```bash
ssh ubuntu@orion-cloud2-vm2
cd ~/orion-infra/stack

# See running infra containers (redis-primary, prometheus, grafana, pushgateway)
docker compose ps

# View logs for a specific service
docker compose logs -f redis-primary
```

### On Worker VMs (`cloud1-vm1`, `cloud2-vm1`)
```bash
ssh ubuntu@orion-cloud1-vm1

# Check the worker agent listening for jobs
sudo systemctl status orion-worker
```
