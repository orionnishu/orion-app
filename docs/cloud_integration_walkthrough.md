# Phase 0: Generic Machine Control — Walkthrough

## What Was Built

### 1. `scripts/orion-node` — Unified machine lifecycle CLI

Single bash script (~300 lines) with all methods as internal functions:

- `method_mqtt_start/stop` — ESP32 relay via Mosquitto
- `method_wol_start` — Wake-on-LAN packet
- `method_ssh_stop` — SSH remote command
- `method_oci_start/stop` — OCI CLI instance start/stop (placeholder until OCI CLI is installed)
- `status_tailscale` — Tailscale ping reachability check
- `parse_config` — INI parser for `machines.conf`
- **Fallback chain dispatcher** — tries methods in order (e.g., MQTT first, then WoL)

Usage:
```
orion-node start desktop-pc    # tries MQTT, falls back to WoL
orion-node stop desktop-pc     # tries MQTT, falls back to SSH
orion-node status cloud2-vm2   # tailscale ping
orion-node list                # all nodes + live status
```

### 2. `scripts/machines.conf` — Machine registry

Defines 4 nodes: `desktop-pc`, `cloud2-vm1`, `cloud2-vm2`, `cloud1-vm1`.
OCI instance IDs are `PLACEHOLDER` until OCI CLI is configured on Pi.

### 3. Backward-compatible wrappers

[wakemypc.sh](file:///home/orion/server/scripts/wakemypc.sh) and [sleepmypc.sh](file:///home/orion/server/scripts/sleepmypc.sh) are now one-line `exec` wrappers → `orion-node start/stop desktop-pc`.

### 4. FastAPI generalized endpoints in [main.py](file:///home/orion/server/app/main.py)

| Endpoint | Method | Description |
|---|---|---|
| `/admin/api/node/{name}/start` | POST | Start any node |
| `/admin/api/node/{name}/stop` | POST | Stop any node |
| `/admin/api/node/{name}/status` | GET | Check node reachability |
| `/admin/api/nodes` | GET | List all nodes + status |
| `/admin/api/wake-pc` | POST | Backward compat (→ start desktop-pc) |
| `/admin/api/sleep-pc` | POST | Backward compat (→ stop desktop-pc) |

---

## Test Results

| Test | Result |
|---|---|
| `orion-node --help` | ✅ Usage printed correctly |
| `orion-node status desktop-pc` | ✅ pong in 3ms via direct Tailscale |
| `orion-node list` | ✅ 4 nodes listed (desktop-pc + vm2 online, vm1 + cloud1-vm1 offline) |
| FastAPI import | ✅ Clean import, no errors |
| `curl /admin/api/node/desktop-pc/status` | ✅ `reachable: true` |
| `curl /admin/api/nodes` | ✅ 4 nodes, correct statuses |
| `curl /api/pc-status` (backward compat) | ✅ `{"online": true}` |
| Service restart | ✅ `orion-webapp` active after restart |

---

## Files Changed

| File | Change |
|---|---|
| [orion-node](file:///home/orion/server/scripts/orion-node) | **NEW** — unified CLI |
| [machines.conf](file:///home/orion/server/scripts/machines.conf) | **NEW** — node registry |
| [wakemypc.sh](file:///home/orion/server/scripts/wakemypc.sh) | **REPLACED** — one-line wrapper |
| [main.py](file:///home/orion/server/app/main.py) | **MODIFIED** — added generalized node endpoints |

---

## Phase 1: Infrastructure (VM2)

Deployed the core infrastructure stack on `oracle-cloud2-vm2` using Docker Compose, bound exclusively to the Tailscale IP (`100.117.244.106`):
- **Redis Primary (`redis:7-alpine`)**: Handles job queues and worker states.
- **Prometheus**: Scrapes metrics from node exporters and pushgateway.
- **Grafana**: Available at `100.117.244.106:3000`.
- **Pushgateway**: Receives short-lived metrics from workers.

**Redis Replica (Pi):**
Installed native `redis-server` on the Raspberry Pi configured as a replica linking to VM2. Verified continuous replication stream (`role:slave`, `master_link_status:up`).

---

## Phase 2: Worker Agents

Created and deployed the `/home/orion/server/scripts/orion-worker.py` Python agent to both worker VMs (`cloud2-vm1` and `cloud1-vm1`) via a `systemd` service (`orion-worker.service`). 

### Agent Capabilities:
- Automatically registers its heartbeat in Redis (`orion:workers`).
- Listens to queue `orion:queue:large` (cloud1-vm1) and `orion:queue:medium` (cloud2-vm1).
- Can execute Docker/shell workloads.
- Pushes job metrics to the VM2 Pushgateway automatically.
- Detects idleness (> 10 mins) and invokes the Pi's FastAPI endpoint `POST /admin/api/node/{name}/stop` to gracefully shut itself down.

Node Exporter was also natively installed on both worker VMs for resource tracking.

### Git-Based Automated Deployment
To ensure configurations stay synchronized, the worker agents are deployed directly from the cloned Git repository (`~/server`) on the worker VMs.
- `deploy-worker.sh` automates cloning/updating the repository over SSH.
- The `orion-worker.service` systemd file is symlinked directly from the repository into `/etc/systemd/system/`.
- The `orion-worker.py` script executes directly from the cloned repository.

### OCI CLI Integration (Completed)
The Oracle `oci` CLI is installed and configured on the Raspberry Pi with two profiles (`cloud1` and `cloud2`) to control the lifecycle of the worker VMs across both tenancies.
- API signing keys were generated and uploaded.
- `machines.conf` was populated with the exact Instance OCIDs (`orion-cloud1-vm1`, `orion-cloud2-vm1`, `orion-cloud2-vm2`).
- The `orion-node start` and `orion-node stop` commands successfully execute `oci compute instance action` to dynamically spin up and tear down workers to save free-tier resources.

---

## Phase 3: Job Scheduler (Pi)

The control plane orchestrates jobs by leveraging Redis queues and the OCI CLI.

### Job Submission & Tracking
Extended the `main.py` FastAPI application to include endpoints for job scheduling:
- `POST /admin/api/job/submit`: Accepts shell/docker commands, generates a unique `job_id`, and pushes the payload directly to a Redis list (`orion:queue:<size>`).
- `GET /admin/api/job/{job_id}/status`: Provides real-time execution state (Pending, Running, or Completed with exit codes and stdout) by checking worker heartbeats and Redis result caches.
- `GET /admin/api/jobs/cluster-state`: Displays the overarching system state, length of all standard queues, and the individual statuses of all active VM workers.

### Auto-Scaling Scheduler
Created `scripts/orion-scheduler.py` (deployed as `orion-scheduler.service` on the Pi):
- **Queue Polling:** The scheduler polls the Redis worker queues (`medium`, `large`) every 10 seconds.
- **Dynamic Spin-Up:** When a queue has jobs but no active workers are registered, it automatically triggers `orion-node start <vm>` to cold-boot the corresponding Oracle VM.
- **Cooldowns:** Implements a 5-minute cooldown to prevent spamming the OCI API while the VM is booting.
- **Worker Auto-Shutdown:** As configured in Phase 2, workers shut themselves down by calling the Pi's API after 10 minutes of idleness.

### Admin Dashboard UI & Handbook
- **Admin Handbook:** Created `docs/ADMIN_HANDBOOK.md` detailing all administrative operations, CLI commands, and VM management. This is served directly from the FastAPI `/docs_static` endpoint.
- **Unified Jobs & System Tab:** Consolidated the "System" and "Jobs" sections in the `/admin` web console into a unified view. It polls the cluster state API every 5 seconds to provide a live view of the queues and active VMs, provides quick-action buttons (Deploy, Pi Sync, Sleep PC), includes a link to the Administrator Handbook, and has a UI form to submit arbitrary jobs for testing and administration.
