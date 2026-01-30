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
1. Configure htpasswd (EXTERNAL):
   ```bash
   sudo mkdir -p /etc/nginx/dav
   sudo htpasswd -c /etc/nginx/dav/users.htpasswd <user>
   ```
2. Symlink config from Repository:
   ```bash
   sudo ln -sf /home/orion/server/system_configs/nginx/orion-webdav /etc/nginx/sites-available/orion-webdav
   ```
3. Enable: `sudo ln -sf /etc/nginx/sites-available/orion-webdav /etc/nginx/sites-enabled/default`
4. Restart: `sudo systemctl restart nginx`

### FastAPI Service
1. Symlink service from Repository:
   ```bash
   sudo ln -sf /home/orion/server/system_configs/systemd/orion-webapp.service /etc/systemd/system/orion-webapp.service
   ```
2. Start: `sudo systemctl daemon-reload && sudo systemctl enable --now orion-webapp`

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

## 🔒 5. Tailscale Serve (HTTPS Routing)

### Install & Authenticate
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Follow the authentication URL
```

### Configure Path-Based Routing
```bash
# Route root to FastAPI (port 8000)
sudo tailscale serve --bg 8000

# Route /dav to WebDAV (port 8082)
sudo tailscale serve --bg --set-path /dav http://127.0.0.1:8082
```

### Generate HTTPS Certificate
```bash
sudo tailscale cert orion-raspian.taila3b741.ts.net
```

### Verify Configuration
```bash
tailscale serve status
# Expected output:
# https://orion-raspian.taila3b741.ts.net (tailnet only)
# |-- /    proxy http://127.0.0.1:8000
# |-- /dav proxy http://127.0.0.1:8082
```

> [!NOTE]
> If browsers show certificate warnings, restart the Tailscale client on the accessing device and clear browser cache.

---

## 🚀 6. Testing & Validation

- **Web App**: `curl http://127.0.0.1:8000/` (Expect 401)
- **WebDAV**: `curl -u user:pass -X PROPFIND http://127.0.0.1:8082/`
- **Sensors**: Run `sensors` to verify temperature visibility.
- **HTTPS**: Access `https://orion-raspian.taila3b741.ts.net/` from a Tailscale device.
