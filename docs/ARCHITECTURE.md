# ORION Architecture

This document describes the **actual working ORION architecture**.

---

## 1. High-Level Design

ORION has three layers:

1. **Application Layer**: FastAPI (Monitoring Dashboard & Control Plane)
2. **Storage Layer**: Nginx WebDAV (Multi-user NAS)
3. **Transport/Security Layer**: Tailscale (Encryption & Routing)

---

## 2. Components

### 2.1 FastAPI Web App
- **Service**: `orion-webapp.service`
- **Port**: `8000`
- **Purpose**: Metrics visualization, system control (WOL, sync), and admin interface.

### 2.2 Nginx WebDAV
- **Port**: `8082`
- **Auth**: Basic Auth via `/etc/nginx/dav/users.htpasswd`
- **Storage**: `/mnt/orion-nas/users/$remote_user/`
- **Features**: Multi-user isolation, setgid permissions for group persistence.

### 2.3 Pi-Monitor (Data Collection)
- **Path**: `/home/orion/server/services/pi-monitor/`
- **DB**: SQLite (`pi-monitor.db`)
- **Collection**: Every minute via cron (`pi-monitor.sh`)
- **Archival**: Weekly aggregation and pruning (`archive_weekly.sql`).

### 2.4 Tailscale
- **DNS**: MagicDNS hostname (`orion-raspian`)
- **Routing**: Tailscale Serve handles path-based routing:
  - `/` → FastAPI (`8000`)
  - `/dav` → Nginx WebDAV (`8082`)

---

## 3. Storage Design

The system uses a dedicated USB drive mounted at `/mnt/orion-nas`.
- **Filesystem**: ext4
- **Mount**: Configured with `nofail` in `/etc/fstab`.
- **Structure**:
  ```
  /mnt/orion-nas/
  └── users/
      ├── praveen_flip/
      └── ruchi_realme/
  ```

---

## 4. Client Support

- **Primary**: FolderSync (Android)
- **Secondary**: curl, rclone, native OS WebDAV mounting.
- **Unsupported**: Solid Explorer (Authentication issues).

---

## 5. Maintenance

- **Backups**: Scripts in `scripts/` (e.g., `pisync_to_pc.sh`) handle intermittent backups.
- **Cleanup**: Weekly database archival ensures the monitoring database remains performant.

---

## 6. System Integration

To ensure high portability, core system configurations are stored in the repository under `system_configs/` and symlinked to their respective system locations.

### 6.1 Repository Managed (Internal)
*   **Systemd**: `system_configs/systemd/orion-webapp.service` → `/etc/systemd/system/`
*   **Nginx**: `system_configs/nginx/orion-webdav` → `/etc/nginx/sites-available/`
*   **Cron**: `system_configs/cron/crontab.txt` (Template source for `crontab -e`)

### 6.2 System Only (External)
The following items **cannot** be in the repository for security or technical reasons:
*   **Secrets**: `/etc/nginx/dav/users.htpasswd` (Passwords).
*   **Mounts**: `/etc/fstab` (System-specific UUIDs).
*   **Tailscale**: Proprietary state managed by the Tailscale daemon.
*   **Database**: `services/pi-monitor/db/pi-monitor.db` (Git-ignored live data).
