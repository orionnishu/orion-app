# ORION Home Server

ORION is a private, Raspberry Pi–based home server focused on **stability, correctness, and security**.

It combines:
- FastAPI (admin & dashboard)
- nginx WebDAV (NAS)
- Tailscale (secure networking & HTTPS)

This repository is the **authoritative source** for ORION’s code and documentation.

---

## What ORION Is

- Hardware: Raspberry Pi 5
- OS: Ubuntu
- Network: Tailscale (MagicDNS + Serve)
- Storage: External USB / HDD mounted at `/mnt/orion-nas`
- Web App: FastAPI + Uvicorn
- NAS: nginx WebDAV
- Android Clients:
  - FolderSync (supported, primary)
  - Material Files (supported, browsing)

## What ORION Is Not

- No router port forwarding
- No public internet exposure
- No SMB / Samba
- No unreliable WebDAV clients

---

## Repository Structure

```
server/
├── app/                 # FastAPI application
├── services/
│   └── webdav/           # WebDAV configs and scripts
├── scripts/              # Admin / deployment scripts
├── docs/                 # Architecture & runbooks
└── README.md
```

---

## Documentation

- Architecture: `docs/architecture.md`
- Build & rebuild: `docs/ORION_BUILD_RUNBOOK.md`

These docs reflect the **real, working system** — not experiments.

---

## Status

ORION is **stable** and in daily use for private backups.
Future enhancements are deliberate and incremental.

---