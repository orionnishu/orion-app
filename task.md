# ORION Raspberry Pi Migration - Actionables

## Context Summary
- **Old OS**: Ubuntu (orion-ubuntu) - crashed, mounted at `/mnt`
- **New OS**: Raspbian 64 lite / Debian 13 (trixie) on hostname `orion-raspian`
- **Repository**: Already cloned at `/home/orion/server`

---

## Actionables List

### Category A: Base System Setup
- [x] A1. Update & upgrade system packages
- [x] A2. Install essential packages (git, curl, vim, ca-certificates, etc.)
- [x] A3. Set timezone (`Asia/Kolkata`)
- [x] A4. Configure hostname properly — `orion-raspian`

### Category B: Python & Application Environment
- [x] B1. Install Python packages (python3, python3-venv, python3-pip)
- [x] B2. Create Python virtual environment in `/home/orion/server`
- [x] B3. Install Python dependencies (`pip install -r requirements.txt`)
- ~~B4. Install WsgiDAV and cheroot~~ — **DISCARDED**

### Category C: nginx WebDAV Setup
- [x] C1. Install nginx & nginx-extras (required for WebDAV extensions)
- [x] C2. Install apache2-utils (for htpasswd)
- [x] C3. Create nginx temp directories (`/var/lib/nginx/tmp`)
- [x] C4. Copy WebDAV config to `/etc/nginx/sites-available/orion-webdav`
- [x] C5. Copy htpasswd file to `/etc/nginx/dav/users.htpasswd`
- [x] C6. Enable nginx WebDAV site (symlink)
- [x] C7. Test and reload nginx — running

### Category D: Storage & Mounts
- [x] D1. Create mount point `/mnt/orion-nas`
- [x] D2. Format USB/HDD drive & get new UUID — `24708909-6970-4c0a-a170-e607251c39dd`
- [x] D3. Configure `/etc/fstab` with nofail options
- [x] D4. Create user directories under `/mnt/orion-nas/users/`
- [x] D5. Set proper permissions (group: orion, setgid)

### Category E: Groups & Permissions
- [x] E1. Create `orion` group — already exists
- [x] E2. Add `orion` user to `orion` group — already done
- [x] E3. Add `www-data` to `orion` group ✓

### Category F: systemd Services
- [x] F1. Create `orion-webapp.service` for FastAPI
- ~~F2. Create `orion-webdav.service` (WsgiDAV)~~ — **DISCARDED**
- [x] F3. Enable and start services
- [x] F4. Verify services are running — port 8000 listening

### Category G: Tailscale Setup
- [x] G1. Install Tailscale — already installed
- [x] G2. Authenticate Tailscale — already logged in
- [x] G3. Configure Tailscale Serve for FastAPI (port 8000)
- [x] G4. Configure Tailscale Serve for WebDAV (`/dav` → port 8082)
- [x] G5. Verify Tailscale routing — `https://orion-raspian.taila3b741.ts.net/`
- [ ] G6. Configure Tailscale funnel

### Category H: Networking
- [x] H1. Configure static IP for Pi ethernet — `192.168.50.1/24`
- [x] H2. Document PC static IP — `192.168.50.2/24`
- [x] H3. Verify mutual reachability — ping works (0.4ms)
- [x] H4. Test Wake-on-LAN from Pi to PC — verified

### Category I: Validation & Testing
- [x] I1. Test FastAPI locally (`curl http://127.0.0.1:8000`)
- [x] I2. Test WebDAV locally with curl PROPFIND
- [ ] I3. Test WebDAV via Tailscale with FolderSync
- [ ] I4. Verify file upload/download works

### Category J: Cleanup & Documentation
- [ ] J1. Unmount old OS when done salvaging
- [x] J2. Update documentation (`ARCHITECTURE.md`, `BUILD_RUNBOOK.md`)
- [ ] J3. Create deploy symlink (`~/bin/orion-deploy`)

### Category K: System Integration
- [x] K1. Move system configs (`systemd`, `nginx`) to repository
- [x] K2. Create symlinks from repo to system folders
- [x] K3. Export cron schedule to `system_configs/cron/crontab.txt`

### Category L: Pi-Monitor Restoration
- [x] L1. Restore `pi-monitor.db` from old OS
- [x] L2. Restore `pi-monitor.sh` and fix variables
- [x] L3. Re-configure cron jobs for stats & archival
- [x] L4. Verify dashboard charts rendering

### Category M: Admin Page & User Management
- [x] M1. Fix script paths in main.py to use absolute paths
- [x] M2. Add PC status API endpoint
- [x] M3. Create tabbed Admin interface (System, Users, Logs)
- [x] M4. Add WebDAV user listing with stats (file count, size)
- [x] M5. Add WebDAV user provisioning form
- [x] M6. Add user delete functionality with data retention option
- [x] M7. Create orion_delete_webdav_user.sh script
- [x] M8. Professional minimal styling (admin.css)

---

## Status Summary

| Category | Progress |
|----------|----------|
| A. Base System | ✅ Complete |
| B. Python/App | ✅ Complete |
| C. nginx Setup | ✅ Complete |
| D. Storage | ✅ Complete |
| E. Groups | ✅ Complete |
| F. systemd | ✅ Complete |
| G. Tailscale | ✅ Complete |
| H. Networking | 🔶 Partial |
| I. Validation | 🔶 Partial |
| J. Cleanup | 🔶 Partial |
| K. Integration | ✅ Complete |
| L. Pi-Monitor | ✅ Complete |
| M. Admin & Users | ✅ Complete |
