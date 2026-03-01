# ORION Home Server

ORION is a private, Raspberry Pi–based home server focused on **stability, correctness, and security**.

It combines:
- **FastAPI**: Monitoring Dashboard & Control Plane
- **nginx WebDAV**: Multi-user NAS
- **Tailscale**: Secure networking & HTTPS routing
- **Pi-Monitor**: Internal health & temperature metrics
- **Mosquitto**: MQTT broker for IoT device communication
- **ESP32**: MQTT-controlled PC power button relay

---

## Technical Stack

- **Hardware**: Raspberry Pi 5
- **OS**: Raspbian 64 Lite (Debian 13)
- **Network**: Tailscale (MagicDNS + Serve)
- **Storage**: External USB Disk (EXT4) mounted at `/mnt/orion-nas`
- **Web App**: FastAPI + Uvicorn (Service: `orion-webapp.service`)
- **NAS**: nginx with WebDAV Extensions (Port: `8082`)
- **MQTT**: Mosquitto broker (Port: `1883`)
- **IoT**: ESP32 power controller via MQTT (`esp32/`)

---

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: High-level design, component diagrams, and program flows.
- **[Build Runbook](docs/BUILD_RUNBOOK.md)**: Steps to recreate or restore the entire system.
- **[Full Build Runbook](docs/ORION_BUILD_RUNBOOK.md)**: Comprehensive from-scratch rebuild guide.
- **[ESP32 Firmware](esp32/README.md)**: MQTT power controller — wiring, commands, and PlatformIO setup.

---

## Status

ORION is **stable** and in daily use for private backups and system monitoring.
The system is configured for high reliability with redundant networking (Local + Tailscale) and automated data archival.