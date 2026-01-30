# ORION Home Server

ORION is a private, Raspberry Pi–based home server focused on **stability, correctness, and security**.

It combines:
- **FastAPI**: Monitoring Dashboard & Control Plane
- **nginx WebDAV**: Multi-user NAS
- **Tailscale**: Secure networking & HTTPS routing
- **Pi-Monitor**: Internal health & temperature metrics

---

## Technical Stack

- **Hardware**: Raspberry Pi 5
- **OS**: Raspbian 64 Lite (Debian 13)
- **Network**: Tailscale (MagicDNS + Serve)
- **Storage**: External USB Disk (EXT4) mounted at `/mnt/orion-nas`
- **Web App**: FastAPI + Uvicorn (Service: `orion-webapp.service`)
- **NAS**: nginx with WebDAV Extensions (Port: `8082`)

---

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: High-level design and component interaction.
- **[Build Runbook](docs/BUILD_RUNBOOK.md)**: Steps to recreate or restore the entire system.

---

## Status

ORION is **stable** and in daily use for private backups and system monitoring.
The system is configured for high reliability with redundant networking (Local + Tailscale) and automated data archival.