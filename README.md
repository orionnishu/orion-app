# ORION Home Server

ORION is a private, Raspberry Pi–based **hybrid edge-cloud system** focused on **stability, correctness, and security**.

It combines:
- **FastAPI**: Monitoring Dashboard & Control Plane
- **nginx WebDAV**: Multi-user NAS
- **Tailscale**: Secure mesh networking & HTTPS routing
- **Pi-Monitor**: Internal health & temperature metrics
- **Mosquitto**: MQTT broker for IoT device communication
- **ESP32**: MQTT-controlled PC power button relay
- **Oracle Cloud VMs**: On-demand distributed compute workers
- **Redis**: Job queue (primary on cloud, replica on Pi)
- **Prometheus + Grafana**: Cluster-wide monitoring on cloud infra node

---

## Node Inventory

| Node | Specs | Role | Status |
|---|---|---|---|
| Raspberry Pi 5 | 4 cores / 4GB | Edge Control Plane | Always-on |
| oracle-cloud2-vm2 | 1 oCPU / 6GB | Infrastructure (Redis, Prometheus, Grafana) | Always-on |
| oracle-cloud2-vm1 | 3 oCPU / 18GB | Medium Compute Worker | On-demand |
| oracle-cloud1-vm1 | 4 oCPU / 23GB | Large Compute Worker | On-demand |
| Desktop PC | 6 cores / 16GB | Fallback Worker + GPU | On-demand |

---

## Technical Stack

- **Hardware**: Raspberry Pi 5 + Oracle Cloud ARM VMs + ESP32
- **OS**: Raspbian 64 Lite (Pi), Ubuntu 24 Minimal (VMs)
- **Network**: Tailscale mesh (MagicDNS + Funnel)
- **Storage**: External USB Disks (EXT4/NTFS) mounted on Pi
- **Web App**: FastAPI + Uvicorn (Service: `orion-webapp.service`)
- **NAS**: nginx with WebDAV Extensions (Port: `8082`)
- **MQTT**: Mosquitto broker (Port: `1883`)
- **IoT**: ESP32 power controller via MQTT (`esp32/`)
- **Job Queue**: Redis 7 on VM2 (replica on Pi)
- **Monitoring**: Prometheus + Grafana + Node Exporter + Pushgateway on VM2
- **Machine Control**: Unified `orion-node` CLI for all node lifecycle management

---

## Repository Structure

```
server/
├── app/                  ← FastAPI web application
├── docs/                 ← Architecture & runbook documentation
├── esp32/                ← ESP32 PlatformIO firmware
├── gpio_experiments/     ← Raspberry Pi GPIO experiments
├── infra/                ← Infrastructure configs & setup scripts
│   ├── vm2/              ← Docker Compose + Prometheus config for VM2
│   ├── pi/               ← Redis replica setup script
│   └── workers/          ← Worker agent deployment script
├── scripts/              ← Shell scripts & machine control CLI
│   ├── orion-node         ← Unified node lifecycle CLI
│   ├── machines.conf      ← Machine registry
│   ├── orion-worker.py    ← Worker agent (deployed to VMs)
│   └── orion-worker.service ← Systemd unit for worker agent
├── services/             ← Pi-Monitor data collection
├── system_configs/       ← Symlinked system configs (systemd, nginx, cron)
└── requirements.txt
```

---

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: High-level design, component diagrams, and program flows.
- **[Build Runbook](docs/BUILD_RUNBOOK.md)**: Steps to recreate or restore the entire system.
- **[Full Build Runbook](docs/ORION_BUILD_RUNBOOK.md)**: Comprehensive from-scratch rebuild guide.
- **[Distributed Architecture Plan](docs/orion_distributed_architecture_plan.md)**: Original ChatGPT-generated plan (superseded by implementation).
- **[ESP32 Firmware](esp32/README.md)**: MQTT power controller — wiring, commands, and PlatformIO setup.

---

## Status

ORION is **stable** and in daily use for private backups, system monitoring, and distributed compute.
The system is configured for high reliability with redundant networking (Local + Tailscale), automated data archival, and Redis replication failover.