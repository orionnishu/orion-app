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
                    lm-sensors sqlite3 mosquitto mosquitto-clients

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

### 2a. WebDAV USB Stick (`/mnt/orion-nas`)
1. Identify drive: `lsblk`
2. Format (EXT4): `sudo mkfs.ext4 -L orion-nas /dev/sdb` (double-check dev name!)
3. Find UUID: `blkid /dev/sdb`
4. Update `/etc/fstab`:
   ```bash
   UUID=<YOUR_UUID> /mnt/orion-nas ext4 defaults,nofail 0 2
   ```
5. Apply: `sudo mkdir -p /mnt/orion-nas && sudo mount -a`

### 2b. WD External HDD (two partitions — media + Docker/Jellyfin data)

The WD HDD is pre-partitioned. Mount both partitions by UUID (never by `/dev/sdaX`):

```bash
sudo mkdir -p /mnt/orion-media /mnt/orion-data
```

Add to `/etc/fstab`:
```fstab
# NTFS media partition — read-only for Jellyfin
UUID=8A28D0A828D09493  /mnt/orion-media  ntfs3  ro,noatime,nofail,x-systemd.device-timeout=10  0  0

# ext4 data partition — Docker data root + Jellyfin config/cache
UUID=86ef87e2-b8c4-4ef7-bad2-b52c2e459cdc  /mnt/orion-data  ext4  defaults,noatime,nofail  0  2
```

```bash
sudo mount -a
df -h /mnt/orion-media /mnt/orion-data   # verify both mounted
```

> [!NOTE]
> `nofail` on both entries is critical — ensures the Pi boots normally even if the HDD is absent.
> Docker will fail to start if `/mnt/orion-data` is missing, but the system stays up.

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

## 🔌 4. MQTT Broker (Mosquitto)

### Enable & Start
```bash
sudo systemctl enable --now mosquitto
```

### Verify
```bash
systemctl status mosquitto
# Test pub/sub from Pi
mosquitto_pub -h 192.168.0.103 -t test -m "hello"
mosquitto_sub -h 192.168.0.103 -t test -C 1
```

> [!NOTE]
> The ESP32 connects to the broker at `192.168.0.103:1883`. Ensure the Pi's Wi-Fi IP matches this address, or update the ESP32 firmware accordingly.

---

## 📈 5. Pi-Monitor & Maintenance

### Stats Collection
Ensure crontab (`crontab -e -u orion`) has:
```cron
# Capture metrics every minute
* * * * * /home/orion/server/services/pi-monitor/bin/pi-monitor.sh >> /home/orion/server/services/pi-monitor/logs/cron.log 2>&1

# Weekly archival (Sundays)
5 0 * * 0 sqlite3 /home/orion/server/services/pi-monitor/db/pi-monitor.db < /home/orion/server/services/pi-monitor/sql/archive_weekly.sql
```

---

## 🔒 6. Tailscale Funnel (HTTPS Routing)

### Install & Authenticate
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Follow the authentication URL
```

### Configure Route: Root → nginx (WebDAV + Jellyfin proxy)
```bash
# Route / to nginx on 8082 (handles both WebDAV and /jellyfin)
sudo tailscale funnel --bg http://127.0.0.1:8082

# Route /app to FastAPI dashboard
sudo tailscale serve --bg /app http://127.0.0.1:8000
```

### Enable Funnel (public internet access)
```bash
sudo tailscale funnel --bg http://127.0.0.1:8082   # re-run with funnel to make it public
```

### Verify
```bash
tailscale funnel status
# Expected:
# https://orion-raspian.taila3b741.ts.net (Funnel on)
# |-- /    proxy http://127.0.0.1:8082
# |-- /app proxy http://127.0.0.1:8000
```

> [!NOTE]
> `/jellyfin` is routed at the nginx level (inside the 8082 server block), not as a separate Tailscale route.
> This version of Tailscale CLI does not support per-path Funnel routes beyond root.

---

## 🔧 7. ESP32 Firmware (Power Controller)

The ESP32 board controls the PC power button via GPIO4. It connects to the MQTT broker and listens for commands.

### Flash Firmware
```bash
cd ~/server/esp32
pio run -t upload
pio device monitor   # verify "esp32_online" is published
```

### Verify MQTT Communication
```bash
# Check ESP32 retained status
mosquitto_sub -h 192.168.0.103 -t orion/pc/status -C 1
# Expected: esp32_online

# Test power toggle
mosquitto_pub -h 192.168.0.103 -t orion/pc/cmd -m "pc/on_or_off"
```

> [!IMPORTANT]
> The ESP32 must be on the same Wi-Fi network (`PRAVEENARCHER`) and able to reach the broker at `192.168.0.103:1883`.

---

## 🎬 9. Docker & Jellyfin

### 9.1 Install Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker orion
```

### 9.2 Move Docker data root to HDD
```bash
sudo systemctl stop docker docker.socket

# Migrate existing data
sudo mkdir -p /mnt/orion-data/docker
sudo rsync -aHAX --info=progress2 /var/lib/docker/ /mnt/orion-data/docker/

# Configure new root
sudo nano /etc/docker/daemon.json
```

`/etc/docker/daemon.json`:
```json
{
  "data-root": "/mnt/orion-data/docker"
}
```

```bash
sudo systemctl start docker
docker info | grep "Docker Root Dir"   # expected: /mnt/orion-data/docker
```

### 9.3 Deploy Jellyfin
```bash
sudo mkdir -p /opt/orion-docker/jellyfin
sudo mkdir -p /mnt/orion-data/jellyfin/{config,cache}
```

`/opt/orion-docker/jellyfin/docker-compose.yml`:
```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    restart: unless-stopped
    ports:
      - "8096:8096"
    volumes:
      - /mnt/orion-data/jellyfin/config:/config
      - /mnt/orion-data/jellyfin/cache:/cache
      - /mnt/orion-media:/media:ro
    environment:
      - TZ=Asia/Kolkata
    devices:
      - /dev/dri:/dev/dri
```

```bash
cd /opt/orion-docker/jellyfin
sudo docker compose up -d
docker ps   # verify 'jellyfin' is Up
```

### 9.4 Configure Jellyfin BaseUrl (required for Tailscale proxy)

Edit `/mnt/orion-data/jellyfin/config/config/network.xml`:
```xml
<BaseUrl>/jellyfin</BaseUrl>
<EnableRemoteAccess>true</EnableRemoteAccess>
<KnownProxies>
  <string>127.0.0.1</string>
</KnownProxies>
```

Then restart the container:
```bash
docker restart jellyfin
curl -s http://localhost:8096/jellyfin/health   # should return 200
```

### 9.5 Verify full stack
```bash
# Jellyfin reachable via nginx proxy (Tailscale path)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/jellyfin/health   # 200

# WebDAV still protected
curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/   # 401
```

---

## 🚀 10. Testing & Validation

- **Web App**: `curl http://127.0.0.1:8000/` (Expect 401)
- **WebDAV**: `curl -u user:pass -X PROPFIND http://127.0.0.1:8082/`
- **Sensors**: Run `sensors` to verify temperature visibility.
- **HTTPS**: Access `https://orion-raspian.taila3b741.ts.net/` from a Tailscale device.
- **MQTT Broker**: `systemctl status mosquitto`
- **ESP32 Status**: `mosquitto_sub -h 192.168.0.103 -t orion/pc/status -C 1`
- **PC Status**: `curl -u orion:pass http://127.0.0.1:8000/api/pc-status`
