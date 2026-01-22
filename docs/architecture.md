# ORION Architecture (Final)

This document describes the **actual working ORION architecture**.
It intentionally records decisions, failures, and constraints.

---

## 1. High-Level Design

ORION has three layers:

1. Application layer — FastAPI
2. Storage layer — nginx WebDAV
3. Transport/security layer — Tailscale

All external access flows through Tailscale.

---

## 2. Components

### 2.1 FastAPI

- Runs via `uvicorn`
- Bound to `127.0.0.1:8000`
- systemd unit: `orion-server.service`
- Purpose:
  - Admin UI (future)
  - Monitoring dashboard
  - Control plane

---

### 2.2 WebDAV (nginx)

- Server: nginx
- Module: http_dav + dav_ext
- Bound to `127.0.0.1:8082`
- Auth: Basic Auth (`htpasswd`)
- Root storage: `/mnt/orion-nas/users`

User isolation:
- nginx maps `$remote_user` → `/mnt/orion-nas/users/$remote_user`
- Each user is jailed to their own directory

Permissions:
- Group-based (`orion`)
- nginx (`www-data`) is a member of `orion`
- setgid directories ensure inheritance

---

### 2.3 Tailscale

Tailscale provides:
- Encrypted networking
- MagicDNS hostname
- HTTPS certificates
- Path-based routing

Important constraint:
**Port 443 is owned by Tailscale, not nginx.**

---

## 3. Routing (Authoritative)

```
https://<host>.ts.net/
  → FastAPI (127.0.0.1:8000)

https://<host>.ts.net/dav
  → nginx WebDAV (127.0.0.1:8082)
```

Configured using:
```
tailscale serve
```

Always inspect routing before changes.

---

## 4. Client Support

### Supported
- FolderSync (Android) — primary
- Material Files (Android) — browsing
- curl, rclone, desktop WebDAV clients

### Unsupported
- Solid Explorer

Reason:
- Broken auth caching
- TLS hostname rigidity
- Unreliable WebDAV behavior

---

## 5. Lessons Learned

- WebDAV correctness ≠ client compatibility
- Tailscale Serve state must be inspected before edits
- Simple mappings beat clever abstractions
- Stability before automation

---

## 6. Current State

| Component | Status |
|---------|--------|
| FastAPI | Stable |
| WebDAV | Stable |
| Multi-user | Working |
| Android backup | Working |
| Solid Explorer | Rejected |

---

End of document.