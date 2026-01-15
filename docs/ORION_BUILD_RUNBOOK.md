# ORION HOME SERVER – BUILD RUNBOOK

> **Purpose**: Reproducible, deterministic recipe to rebuild the ORION home server on a **fresh Ubuntu installation on Raspberry Pi**.
>
> This is **not a backup**. This is a **from-scratch build guide** that avoids copying corrupted state and instead recreates a clean, stable system.
>
> ⚠️ **Security note**  
> This document intentionally omits real IPs, UUIDs, usernames, passwords, tokens, and secrets.  
> All identifiers are placeholders and must be replaced locally.

---

## 0. Preconditions

- Hardware: Raspberry Pi 5
- OS: Ubuntu Server / Desktop (headless preferred)
- Architecture: aarch64
- SD card: ≥ 32 GB (64 GB recommended)
- Power: stable 5V supply (≥ 5A for Pi 5)

Assumptions:
- Internet available via Wi‑Fi
- Ethernet reserved for Pi ↔ PC private link
- Deployment is **manual**, never automatic

---

## 1. Base OS Setup

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl vim ca-certificates
sudo timedatectl set-timezone Asia/Kolkata
```

Reboot once:
```bash
sudo reboot
```

---

## 2. User, Sudo, SSH

```bash
sudo adduser orion
sudo usermod -aG sudo orion
```

SSH hardening (optional but recommended):
```bash
sudo nano /etc/ssh/sshd_config
```

Suggested:
- `PermitRootLogin no`
- `PasswordAuthentication yes` (or `no` if using keys)

Restart SSH:
```bash
sudo systemctl restart ssh
```

---

## 3. Networking (ORION Architecture)

### 3.1 Wi‑Fi (Internet)

Netplan example (placeholder values):

```yaml
network:
  version: 2
  renderer: networkd
  wifis:
    wlan0:
      dhcp4: true
      access-points:
        "YOUR_SSID":
          password: "YOUR_PASSWORD"
```

Apply:
```bash
sudo netplan apply
```

---

### 3.2 Ethernet (Pi ↔ PC Private Link)

Static IP, **no gateway**, no DNS.

```yaml
ethernets:
  eth0:
    dhcp4: false
    addresses:
      - 192.168.50.2/24
```

Apply:
```bash
sudo netplan apply
```

---

## 4. Storage & Mount Strategy (Hardened)

Create mount point:
```bash
sudo mkdir -p /mnt/orion-nas
```

Identify disk:
```bash
lsblk -f
```

`/etc/fstab` entry (**non‑blocking**):

```text
UUID=XXXX-XXXX  /mnt/orion-nas  ext4  defaults,nofail,x-systemd.device-timeout=10  0  2
```

Rules:
- Always use `nofail`
- Never block boot on removable storage

Validate:
```bash
mount -a
```

---

## 5. Core Packages

```bash
sudo apt install -y   python3   python3-venv   python3-pip   sqlite3   nginx   ethtool
```

---

## 6. ORION Application Setup

```bash
cd ~
git clone https://github.com/orionnishu/orion-app.git server
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 7. systemd Services (Exact Templates)

### 7.1 ORION App Service (FastAPI)

Create service file:

```bash
sudo nano /etc/systemd/system/orion-app.service
```

Contents:

```ini
[Unit]
Description=ORION FastAPI Application
After=network.target

[Service]
Type=simple
User=orion
WorkingDirectory=/home/orion/server
Environment="PATH=/home/orion/server/venv/bin"
ExecStart=/home/orion/server/venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable orion-app
sudo systemctl start orion-app
```

Verify:

```bash
systemctl status orion-app
```

---

## 8. WebDAV (WsgiDAV)

### 8.1 Install dependencies

```bash
source ~/server/venv/bin/activate
pip install wsgidav cheroot
```

---

### 8.2 Directory layout

```bash
sudo mkdir -p /mnt/orion-nas/users
sudo chown -R orion:orion /mnt/orion-nas/users
```

Per-user directories:
```bash
mkdir /mnt/orion-nas/users/user1
mkdir /mnt/orion-nas/users/user2
```

---

### 8.3 WsgiDAV configuration

Create config file:

```bash
nano ~/server/services/webdav/config.py
```

Template:

```python
from wsgidav.wsgidav_app import WsgiDAVApp

config = {
    "host": "127.0.0.1",
    "port": 8081,
    "provider_mapping": {
        "/": "/mnt/orion-nas/users"
    },
    "http_authenticator": {
        "domain_controller": "wsgidav.dc.simple_dc.SimpleDomainController",
        "accept_basic": True,
        "accept_digest": False,
        "default_to_digest": False,
    },
    "simple_dc": {
        "user1": {
            "password": "REPLACE_LOCALLY",
            "description": "",
            "roles": []
        }
    },
    "verbose": 1,
}
```

⚠️ Passwords are placeholders. Never commit real values.

---

### 8.4 WebDAV systemd service

```bash
sudo nano /etc/systemd/system/orion-webdav.service
```

```ini
[Unit]
Description=ORION WebDAV Service
After=network.target

[Service]
Type=simple
User=orion
WorkingDirectory=/home/orion/server/services/webdav
Environment="PATH=/home/orion/server/venv/bin"
ExecStart=/home/orion/server/venv/bin/python -m wsgidav.server.run_server --config config.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable orion-webdav
sudo systemctl start orion-webdav
```

Verify:

```bash
systemctl status orion-webdav
```

---

## 9. Audio / GUI Policy (Stability First)

Disable ALSA restore (known instability on Pi):

```bash
sudo systemctl mask alsa-restore.service
```

Headless default:

```bash
sudo systemctl disable gdm3
sudo systemctl set-default multi-user.target
```

GUI can be re-enabled later if required.

---

## 10. Deployment Workflow (Manual by Design)

Deploy script lives in repo:

```bash
~/server/scripts/deploy.sh
```

Exposed via symlink:

```bash
ln -s ~/server/scripts/deploy.sh ~/bin/orion-deploy
```

Deployment is always explicit:

```bash
orion-deploy
```

---

## 11. Recovery Appendix (Lessons Learned)

- Boot drops to emergency → check `/etc/fstab`
- Never block boot on USB devices
- GUI loops ≠ broken kernel
- ALSA restore failures can destabilize systemd
- Headless mode is the most reliable state

---

## 12. Parked Enhancements (Intentional)

The following are **deliberately deferred**:

- Automatic deployment (CI/CD)
- Agentic / self-healing scripts
- GUI hardening
- Alerts & monitoring automation
- Secrets management tooling

These will be revisited later with care.

---

**End of Runbook**
