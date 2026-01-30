# ORION Build Runbook - Setup & Recovery

> **OS**: Raspbian 64 Lite (Debian 13/Trixie)  
> **Repository**: `/home/orion/server`

---

## 🛠 1. Base System & Prerequisites

### Packages & Config
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl vim ca-certificates python3-venv python3-pip python3-dev \
                    nginx nginx-extras libnginx-mod-http-dav-ext apache2-utils \
                    lm-sensors sqlite3

# Set Timezone
sudo timedatectl set-timezone Asia/Kolkata
```

### Groups & Workspace
```bash
sudo usermod -aG orion orion
sudo usermod -aG orion www-data

mkdir -p /home/orion/server
cd /home/orion/server
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

---

## 📂 2. Storage Setup

### USB Mount
1. Identify drive: `lsblk`
2. Format (EXT4): `sudo mkfs.ext4 -L orion-nas /dev/sdb` (Double check dev name!)
3. Find UUID: `blkid /dev/sdb`
4. Update `/etc/fstab`:
   ```bash
   UUID=<YOUR_UUID> /mnt/orion-nas ext4 defaults,nofail 0 2
   ```
5. Apply: `sudo mkdir -p /mnt/orion-nas && sudo mount -a`

### Directory Permissions
```bash
sudo mkdir -p /mnt/orion-nas/users/{praveen_flip,ruchi_realme}
sudo chown -R orion:orion /mnt/orion-nas/users
sudo chmod 2775 /mnt/orion-nas/users /mnt/orion-nas/users/*
```

---

## 🌐 3. Networking & Services

### Nginx WebDAV
1. Configure htpasswd:
   ```bash
   sudo mkdir -p /etc/nginx/dav
   sudo htpasswd -c /etc/nginx/dav/users.htpasswd <user>
   ```
2. Link config from `docs/orion-webdav.conf` to `/etc/nginx/sites-available/`
3. Enable: `sudo ln -sf /etc/nginx/sites-available/orion-webdav /etc/nginx/sites-enabled/default` (Replace default)
4. Restart: `sudo systemctl restart nginx`

### FastAPI Service
Create `/etc/systemd/system/orion-webapp.service`:
```ini
[Unit]
Description=ORION Web Application
After=network.target

[Service]
User=orion
Group=orion
WorkingDirectory=/home/orion/server
ExecStart=/home/orion/server/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
Start: `sudo systemctl enable --now orion-webapp`

---

## 📈 4. Pi-Monitor & Maintenance

### Stats Collection
Ensure crontab (`crontab -e -u orion`) has:
```cron
# Capture metrics every minute
* * * * * /home/orion/server/services/pi-monitor/bin/pi-monitor.sh >> /home/orion/server/services/pi-monitor/logs/cron.log 2>&1

# Weekly archival (Sundays)
5 0 * * 0 sqlite3 /home/orion/server/services/pi-monitor/db/pi-monitor.db < /home/orion/server/services/pi-monitor/sql/archive_weekly.sql
```

---

## 🚀 5. Testing & Validation

- **Web App**: `curl http://127.0.0.1:8000/` (Expect 401)
- **WebDAV**: `curl -u user:pass -X PROPFIND http://127.0.0.1:8082/`
- **Sensors**: Run `sensors` to verify temperature visibility.
