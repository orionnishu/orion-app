# ORION HOME SERVER – COMPLETE CONTEXT (FOR GITHUB COPILOT)

> **Purpose of this document**
> This file captures the *entire architectural, technical, and operational context* of the ORION Home Server project so that GitHub Copilot (and any future agentic tooling) can reason correctly without re‑discovery.
>
> This is not a tutorial. This is **ground truth**.

---

## 1. PROJECT OVERVIEW

**ORION Home Server** is a self‑hosted, Raspberry Pi–based system designed to:

- Monitor Raspberry Pi hardware health
- Control a Windows PC (Wake‑on‑LAN + Sleep)
- Provide a secure admin dashboard
- Act as a personal cloud / NAS with per‑user isolation
- Support *always‑on mobile backups* (photos, videos, screenshots)

Key design goals:
- Low resource usage (Pi‑friendly)
- No vendor lock‑in
- Clear separation of concerns
- Long‑term stability (no “rot”)

---

## 2. HARDWARE & NETWORK

### Hardware
- **Primary SBC**: Raspberry Pi 5 (4GB)
- **Storage**:
  - microSD: OS
  - USB SSD / Flash drive: NAS data (ext4)
- **Windows PC**:
  - Used for heavy workloads
  - Controlled remotely via WoL + SSH

### Network Model (Important)

Dual‑network design:

1. **Wi‑Fi**
   - Internet access
   - Public ingress (via reverse tunnel)

2. **Dedicated Ethernet (Pi ↔ PC)**
   - Static IPs
   - No gateway
   - Used only for WoL + local control

This avoids broadcast issues and keeps control traffic isolated.

---

## 3. SERVER DIRECTORY STRUCTURE (CANONICAL)

All services live under a single root:

```
~/server/
├── app/                      # FastAPI app (UI + APIs)
├── services/
│   ├── pi-monitor/
│   │   ├── bin/              # pi-monitor.sh
│   │   ├── db/               # SQLite DB
│   │   ├── logs/
│   │   └── sql/              # archive_weekly.sql
│   └── webdav/
│       └── app/              # WsgiDAV config + runner
├── venv/                     # Python virtualenv
```

**Rules**:
- Absolute paths everywhere
- Cron‑safe
- Reboot‑safe

---

## 4. PI MONITORING SUBSYSTEM (DONE & STABLE)

### Collector
- Shell‑based (`pi-monitor.sh`)
- Lightweight (no Python daemon)

### Metrics Collected
- CPU temperature
- Board temperature
- CPU frequency
- RAM used
- Load average (1m)
- Fan RPM
- Fan PWM

### Time Handling (Critical Design Decision)
- Collector generates **explicit local timestamps**
- SQLite **never auto‑generates time**
- No UTC conversions anywhere

This eliminates an entire class of bugs.

---

## 5. DATABASE (SQLITE)

### Tables

- `metrics` – raw samples
- `metrics_weekly_avg` – aggregated data

### Retention & Aggregation

- Weekly aggregation via `archive_weekly.sql`
- Calendar week definition:
  - Sunday 00:00 → Saturday 23:59
- Aggregates: avg / min / max
- Old raw data deleted after aggregation

---

## 6. DASHBOARD (FASTAPI + CHART.JS)

### Backend
- FastAPI
- SQLite queries handle all time filtering
- No Python time arithmetic

### APIs
- `/api/metrics/cpu-temp`
- `/api/metrics/ram-used`
- `/api/metrics/load-1m`
- `/api/metrics/fan-rpm`

### Frontend
- Chart.js
- Auto‑refresh every 5 seconds
- Timeframe selector:
  - 1h / 2h / 6h / 24h / 7d
- Fixed Y‑axis ranges
- Health color coding:
  - 🟢 Green
  - 🟠 Amber
  - 🔴 Red

### Auth
- HTTP Basic Auth (admin‑only)

---

## 7. ADMIN PANEL (DONE)

- Wake Windows PC (WoL)
- Sleep Windows PC (SSH)
- Online/offline status
- Passwordless SSH

This panel is **admin‑only** by design.

---

## 8. NAS & STORAGE

### Disk
- USB drive formatted ext4
- Label: `ORION_NAS`
- Mounted at:

```
/mnt/orion-nas
```

### Per‑User Layout

```
/mnt/orion-nas/users/
├── praveen_flip/
└── ruchi_realme/
```

- Unix ownership enforced
- No shared folders

---

## 9. WEBDAV SERVICE (WsgiDAV)

### Why WsgiDAV
- Lightweight
- Client‑compatible (FolderSync, Solid Explorer)
- Full WebDAV method support (PROPFIND, MKCOL, PUT, etc.)

### Implementation
- Runs inside Python venv
- Bound to `127.0.0.1:8081`

### Auth
- `simple_dc` users
- Users:
  - `praveen_flip`
  - `ruchi_realme`

Each user maps to their own root directory under `/mnt/orion-nas/users/`.

### Status
- WebDAV works correctly locally
- All methods verified via curl

---

## 10. PUBLIC ACCESS ATTEMPT – TAILSCALE (IMPORTANT HISTORY)

### Initial Success
- Tailscale Funnel was initially used
- Public access worked temporarily

### What Changed
- `tailscale serve reset` was executed during reconfiguration
- After reset, Funnel **permanently downgraded to tailnet‑only**

### ACL State (Verified Correct)
- `tag:funnel` defined
- Node tagged correctly
- `nodeAttrs` includes funnel

### Final Status

```
https://orion-ubuntu.taila3b741.ts.net (tailnet only)
```

### Conclusion
- Public Funnel ingress is **disabled at Tailscale backend level**
- Not fixable via ACL / CLI / UI
- Requires Tailscale Support or alternate ingress

This is a **documented but poorly surfaced Tailscale behavior**.

---

## 11. FUTURE INGRESS STRATEGY (DECIDING)

### Recommended Architecture

- **Cloudflare Tunnel** → Public ingress
- **Tailscale** → Admin / SSH / private control

Reasons:
- Stable public access
- No VPN required for clients
- Works with mobile backup apps
- No backend gating

---

## 12. AUTH STRATEGY GOING FORWARD

### Web App (`/`)
- Cloudflare Access (optional)
- FastAPI Basic Auth (existing)

### WebDAV (`/dav`)
- Cloudflare Tunnel
- WebDAV Basic Auth only
- No OAuth (client compatibility)

---

## 13. PARKED / DEFERRED ITEMS

### Monitoring Enhancements
- Alerts
- WebSockets
- Monthly aggregates

### UI Enhancements
- Summary tiles
- Pause/resume live updates
- Role‑based auth

### Media / Cloud
- Media server
- Photo/video cloud UI
- Internet radio

---

## 14. NON‑NEGOTIABLE DESIGN PRINCIPLES

- Collector owns timestamps
- DB never auto‑creates time
- UI is dumb & stateless
- Per‑user isolation always
- Minimal stack
- Everything must survive reboot

---

## 15. CURRENT STATE (SUMMARY)

✅ Monitoring: DONE & STABLE
✅ Admin Control: DONE
✅ WebDAV: DONE (local)
❌ Public ingress: Funnel blocked
➡ Next step: Cloudflare Tunnel

---

## 16. NOTE TO AGENTS / COPILOT

- Do **not** suggest Grafana / InfluxDB
- Do **not** auto‑convert timestamps
- Do **not** merge user roots
- Assume Raspberry Pi constraints
- Respect separation: admin vs public

This document is authoritative.

