# ORION Migration Checklist (orion-ubuntu → orion-raspian)

> **Created**: 2026-01-30  
> **Old OS**: Ubuntu (orion-ubuntu) - crashed, mounted at `/mnt`  
> **New OS**: Raspbian 64 lite / Debian 13 (trixie)

---

## Phase 1: Immediate Priority

### A. Base System Setup
- [ ] A1. Update & upgrade system packages
- [ ] A2. Install essential packages (check first, install if missing)
- [ ] A3. Verify timezone is `Asia/Kolkata`

### E. Groups & Permissions
- [ ] E1. Create `orion` group
- [ ] E2. Add `orion` user to `orion` group
- [ ] E3. Add `www-data` to `orion` group

### H. Networking (Pi ↔ PC Static Subnet)
- [ ] H1. Configure static IP on Pi ethernet (e.g., 192.168.50.2/24)
- [ ] H2. Document PC static IP for same subnet
- [ ] H3. Verify mutual reachability (ping test)
- [ ] H4. Test Wake-on-LAN from Pi to PC

### C. nginx Basic Setup
- [ ] C1. Install nginx (without extras for now)
- [ ] C2. Install apache2-utils (for htpasswd)
- [ ] C3. Create nginx temp directories (`/var/lib/nginx/tmp`)
- [ ] C5. Copy htpasswd file to `/etc/nginx/dav/users.htpasswd`
- [ ] C7. Test and reload nginx

---

## Phase 2: Parked for Later

### B. Python & Application (Partial)
- [x] ~~B4. WsgiDAV~~ — **NOT NEEDED** (was workaround, nginx WebDAV works)

### C. nginx WebDAV (Deferred)
- [ ] C4. Copy WebDAV config to `/etc/nginx/sites-available/orion-webdav`
- [ ] C6. Enable nginx WebDAV site (symlink)

### D. Storage & Mounts
> **Blocked**: USB drive needs to be inserted and formatted first
- [ ] D1. Create mount point `/mnt/orion-nas`
- [ ] D2. Format USB/HDD drive
- [ ] D3. Get new UUID and configure `/etc/fstab`
- [ ] D4. Create user directories under `/mnt/orion-nas/users/`
- [ ] D5. Set proper permissions (group: orion, setgid)

### F. systemd Services
- [ ] F1. Create `orion-server.service` for FastAPI
- [ ] F2. Enable and start services
- [ ] F3. Verify services are running

### G. Tailscale Serve
> **Note**: Tailscale is already installed and logged in
- [ ] G3. Configure Tailscale Serve for FastAPI (port 8000)
- [ ] G4. Configure Tailscale Serve for WebDAV (`/dav` → port 8082)
- [ ] G5. Verify Tailscale routing

### I. Validation & Testing
- [ ] I1. Test FastAPI locally
- [ ] I2. Test WebDAV locally with curl
- [ ] I3. Test WebDAV via Tailscale with FolderSync
- [ ] I4. Verify file upload/download

### J. Cleanup & Documentation
- [ ] J1. Unmount old OS when done salvaging
- [ ] J2. Update documentation if architecture changes
- [ ] J3. Create deploy symlink (`~/bin/orion-deploy`)

---

## Salvaged Configs Reference

| Item | Old Location | Notes |
|------|--------------|-------|
| systemd services | `/mnt/etc/systemd/system/orion-*.service` | Ready to copy |
| nginx WebDAV | `/mnt/etc/nginx/sites-available/orion-webdav` | Ready to copy |
| htpasswd | `/mnt/etc/nginx/dav/users.htpasswd` | 2 users |
| NAS UUID | `7b76b9f3-608e-45c2-a5c0-fd7ab19e0fc9` | Old drive UUID |
