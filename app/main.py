from fastapi import FastAPI, Request, Depends, HTTPException, status, Query, Form, Path as PathParam
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import subprocess
import secrets
import sqlite3
import socket
import json
import time
import os
from pathlib import Path
from collections import deque

# Support for being served under a subpath (e.g., /app via Tailscale)
ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI(title="Orion Home Server", root_path=ROOT_PATH)

# --------------------
# Auth config
# --------------------
security = HTTPBasic()

USERNAME = "orion"
PASSWORD = "orion1812"   # CHANGE THIS

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username

# --------------------
# Templates & static
# --------------------
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --------------------
# PC config
# --------------------
PC_IP = "192.168.0.102"
SCRIPTS_DIR = Path("/home/orion/server/scripts")

_pc_last_check = 0.0
_pc_last_result = False
_PC_CACHE_TTL = 2.0

def is_pc_online() -> bool:
    global _pc_last_check, _pc_last_result

    now = time.time()
    if now - _pc_last_check < _PC_CACHE_TTL:
        return _pc_last_result

    _pc_last_check = now
    try:
        with socket.create_connection((PC_IP, 445), timeout=0.4):
            _pc_last_result = True
    except OSError:
        _pc_last_result = False

    return _pc_last_result

@app.get("/api/pc-status", response_class=JSONResponse)
def pc_status():
    return {"online": is_pc_online()}

# --------------------
# UI Routes (HTML only)
# --------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "title": "Home"}
    )

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Pi Health"}
    )

@app.get("/network", response_class=HTMLResponse)
def network(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse(
        "network.html",
        {"request": request, "title": "Network Dashboard"}
    )

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Admin",
            "pc_online": is_pc_online()
        }
    )

# ------------------------------------------------------------------
# Generalized Node Lifecycle Endpoints (via orion-node script)
# ------------------------------------------------------------------
ORION_NODE_SCRIPT = SCRIPTS_DIR / "orion-node"

@app.post("/admin/api/node/{name}/start", response_class=JSONResponse)
def api_node_start(name: str = PathParam(...), user: str = Depends(authenticate)):
    """Start/wake any registered node via orion-node CLI"""
    result = subprocess.run(
        [str(ORION_NODE_SCRIPT), "start", name],
        capture_output=True, text=True, timeout=30
    )
    return {
        "status": "ok" if result.returncode == 0 else "error",
        "action": "start",
        "node": name,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None
    }

@app.post("/admin/api/node/{name}/stop", response_class=JSONResponse)
def api_node_stop(name: str = PathParam(...), user: str = Depends(authenticate)):
    """Stop/sleep any registered node via orion-node CLI"""
    result = subprocess.run(
        [str(ORION_NODE_SCRIPT), "stop", name],
        capture_output=True, text=True, timeout=30
    )
    return {
        "status": "ok" if result.returncode == 0 else "error",
        "action": "stop",
        "node": name,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None
    }

@app.get("/admin/api/node/{name}/status", response_class=JSONResponse)
def api_node_status(name: str = PathParam(...), user: str = Depends(authenticate)):
    """Check reachability of any registered node via Tailscale ping"""
    result = subprocess.run(
        [str(ORION_NODE_SCRIPT), "status", name],
        capture_output=True, text=True, timeout=10
    )
    return {
        "status": "ok" if result.returncode == 0 else "error",
        "node": name,
        "reachable": result.returncode == 0,
        "output": result.stdout.strip()
    }

@app.get("/admin/api/nodes", response_class=JSONResponse)
def api_node_list(user: str = Depends(authenticate)):
    """List all registered nodes with live status"""
    result = subprocess.run(
        [str(ORION_NODE_SCRIPT), "list"],
        capture_output=True, text=True, timeout=30
    )
    # Parse the tabular output into structured data
    nodes = []
    for line in result.stdout.strip().split("\n")[2:]:  # Skip header + separator
        parts = line.split()
        if len(parts) >= 3:
            nodes.append({
                "name": parts[0],
                "tailscale_host": parts[1],
                "status": parts[2]
            })
    return nodes

# --- Backward-compatible PC aliases (call the generalized endpoints) ---

@app.post("/admin/api/wake-pc", response_class=JSONResponse)
def api_wake_pc(user: str = Depends(authenticate)):
    subprocess.Popen([str(ORION_NODE_SCRIPT), "start", "desktop-pc"])
    return {"status": "ok", "action": "wake-pc"}

@app.post("/admin/api/sleep-pc", response_class=JSONResponse)
def api_sleep_pc(user: str = Depends(authenticate)):
    subprocess.Popen([str(ORION_NODE_SCRIPT), "stop", "desktop-pc"])
    return {"status": "ok", "action": "sleep-pc"}

# --- Other admin triggers ---

@app.post("/admin/api/pisync", response_class=JSONResponse)
def api_pi_sync(user: str = Depends(authenticate)):
    subprocess.Popen([str(SCRIPTS_DIR / "pisync_to_pc.sh")])
    return {"status": "ok", "action": "pi-sync"}

@app.post("/admin/api/deploy", response_class=JSONResponse)
def api_deploy(user: str = Depends(authenticate)):
    subprocess.Popen([str(SCRIPTS_DIR / "deploy.sh"), "--yes"])
    return {"status": "ok", "action": "deploy"}

@app.post("/admin/api/webdav/provision", response_class=JSONResponse)
def api_webdav_provision(
    username: str = Form(...),
    password: str = Form(...),
    user: str = Depends(authenticate)
):
    # Validate input
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    if not username.isalnum() and "_" not in username:
        raise HTTPException(status_code=400, detail="Username must be alphanumeric (underscores allowed)")
    
    # Run script with password as environment variable
    env = {"ORION_WEBDAV_PASSWORD": password, "PATH": "/usr/bin:/bin"}
    subprocess.Popen(
        ["sudo", "-E", str(SCRIPTS_DIR / "orion_add_webdav_user.sh"), username],
        env=env
    )
    return {"status": "ok", "action": "webdav-provision", "username": username}

# ------------------------------------------------------------------
# WebDAV User Management
# ------------------------------------------------------------------

HTPASSWD_FILE = Path("/etc/nginx/dav/users.htpasswd")
WEBDAV_BASE_DIR = Path("/mnt/orion-nas/users")

@app.get("/admin/api/webdav/users", response_class=JSONResponse)
def list_webdav_users(user: str = Depends(authenticate)):
    """List all WebDAV users with folder stats"""
    users = []
    
    # Read htpasswd file
    if HTPASSWD_FILE.exists():
        with open(HTPASSWD_FILE, "r") as f:
            for line in f:
                if ":" in line:
                    username = line.split(":")[0].strip()
                    user_data = {"username": username, "file_count": None, "size": None}
                    
                    # Get folder stats if exists
                    user_dir = WEBDAV_BASE_DIR / username
                    if user_dir.exists():
                        try:
                            result = subprocess.run(
                                ["du", "-sh", str(user_dir)],
                                capture_output=True, text=True, timeout=5
                            )
                            if result.returncode == 0:
                                user_data["size"] = result.stdout.split()[0]
                            
                            result = subprocess.run(
                                ["find", str(user_dir), "-type", "f"],
                                capture_output=True, text=True, timeout=10
                            )
                            if result.returncode == 0:
                                user_data["file_count"] = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
                        except Exception:
                            pass
                    
                    users.append(user_data)
    
    return users

@app.delete("/admin/api/webdav/users/{username}", response_class=JSONResponse)
def delete_webdav_user(
    username: str,
    delete_data: bool = Query(True),
    user: str = Depends(authenticate)
):
    """Delete a WebDAV user"""
    # Run delete script
    subprocess.Popen([
        "sudo", str(SCRIPTS_DIR / "orion_delete_webdav_user.sh"),
        username,
        "--delete-data" if delete_data else "--keep-data"
    ])
    
    return {"status": "ok", "action": "delete-user", "username": username, "data_deleted": delete_data}

# ------------------------------------------------------------------
# Unified Admin Log Reader (READ-ONLY)
# ------------------------------------------------------------------

ADMIN_LOG_FILE = Path("/var/log/orion/admin-actions.log")

@app.get("/admin/logs", response_class=JSONResponse)
def read_admin_logs(
    lines: int = Query(500, ge=10, le=5000),
    user: str = Depends(authenticate)
):
    if not ADMIN_LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="Admin log file not found")

    with ADMIN_LOG_FILE.open("r", encoding="utf-8", errors="replace") as f:
        last_lines = deque(f, maxlen=lines)

    return {"lines": "".join(last_lines)}

# --------------------
# Metrics / Dashboard APIs
# --------------------

DB_PATH = "/home/orion/server/services/pi-monitor/db/pi-monitor.db"

WINDOW_MAP = {
    "1h": "-1 hours",
    "6h": "-6 hours",
    "24h": "-24 hours",
    "7d": "-7 days",
}

def _metric_series(metric_name: str, window: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if window == "weekly":
        # Query weekly archives
        cur.execute(f"""
            SELECT week_start, avg_value
            FROM metrics_weekly_avg
            WHERE name = ?
            ORDER BY week_start
        """, (metric_name,))
    else:
        # Query raw metrics
        if window not in WINDOW_MAP:
            window = "24h"
            
        cur.execute(f"""
            SELECT ts, value
            FROM metrics
            WHERE name = ?
              AND ts >= datetime('now', '{WINDOW_MAP[window]}', 'localtime')
            ORDER BY ts
        """, (metric_name,))

    rows = cur.fetchall()
    conn.close()

    labels = []
    values = []
    for r in rows:
        try:
            if r[1] is not None and str(r[1]).strip() != "":
                val = float(r[1])
                labels.append(r[0])
                values.append(val)
        except ValueError:
            pass

    return {
        "labels": labels,
        "values": values,
    }

@app.get("/api/metrics/cpu-temp", response_class=JSONResponse)
def cpu_temp_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("cpu_temp", window)

@app.get("/api/metrics/cpu-utilization", response_class=JSONResponse)
def cpu_util_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("cpu_util_index", window)

@app.get("/api/metrics/ram-used", response_class=JSONResponse)
def ram_used_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("ram_used", window)

@app.get("/api/metrics/load-1m", response_class=JSONResponse)
def load_1m_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("load_1m", window)

@app.get("/api/metrics/fan-rpm", response_class=JSONResponse)
def fan_rpm_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("fan_rpm", window)

@app.get("/api/metrics/cpu-freq", response_class=JSONResponse)
def cpu_freq_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("cpu_freq", window)

# --- Service Monitoring ---
MONITORED_SERVICES = [
    "nginx",
    "orion-webapp",
    "ssh",
    "tailscaled",
    "wpa_supplicant",
    "cron",
    "bluetooth",
    "avahi-daemon",
    "mosquitto"
]

@app.get("/api/services/status", response_class=JSONResponse)
def get_service_status(user: str = Depends(authenticate)):
    results = []
    for service in MONITORED_SERVICES:
        try:
            # Check if active
            res = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True
            )
            status = res.stdout.strip()
            # Also get sub-state if needed, but is-active returns 'active' or 'inactive'/'failed'
            processed_status = "running" if status == "active" else "stopped"
            
            # Map nice names
            nice_name = service.replace(".service", "").replace("-", " ").title()
            if service == "ssh": nice_name = "SSH"
            if service == "nginx": nice_name = "NGINX (WebDAV)"
            if service == "tailscaled": nice_name = "Tailscale"
            if service == "cron": nice_name = "Cron Jobs"
            if service == "avahi-daemon": nice_name = "mDNS (Avahi)"
            if service == "orion-webapp": nice_name = "Uvicorn (FastAPI)"
            if service == "wpa_supplicant": nice_name = "Wi-Fi"
            if service == "mosquitto": nice_name = "Mosquitto (MQTT)"

            results.append({
                "id": service,
                "name": nice_name,
                "status": processed_status, # 'running', 'stopped'
                "raw": status
            })
        except Exception as e:
            results.append({"id": service, "name": service, "status": "error", "error": str(e)})

    # --- ESP32 device status via MQTT retained message ---
    try:
        esp32_result = subprocess.run(
            ["mosquitto_sub", "-h", "192.168.0.103", "-t", "orion/pc/status", "-C", "1", "-W", "2"],
            capture_output=True, text=True, timeout=5
        )
        esp32_status = esp32_result.stdout.strip()
        results.append({
            "id": "esp32-master-bedroom",
            "name": "ESP32 Master Bedroom",
            "status": "running" if esp32_status == "esp32_online" else "stopped",
            "raw": esp32_status or "unreachable"
        })
    except Exception:
        results.append({
            "id": "esp32-master-bedroom",
            "name": "ESP32 Master Bedroom",
            "status": "stopped",
            "raw": "unreachable"
        })

    # --- Docker Engine status ---
    try:
        docker_res = subprocess.run(
            ["systemctl", "is-active", "docker"],
            capture_output=True, text=True
        )
        docker_active = docker_res.stdout.strip() == "active"
        results.append({
            "id": "docker",
            "name": "Docker Engine",
            "status": "running" if docker_active else "stopped",
            "raw": docker_res.stdout.strip()
        })
    except Exception as e:
        results.append({"id": "docker", "name": "Docker Engine", "status": "error", "error": str(e)})

    # --- Jellyfin container status ---
    try:
        jf_res = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}} {{.State.Health.Status}}", "jellyfin"],
            capture_output=True, text=True, timeout=3
        )
        jf_out = jf_res.stdout.strip()  # e.g. "running healthy"
        jf_parts = jf_out.split()
        jf_running = len(jf_parts) > 0 and jf_parts[0] == "running"
        jf_healthy = len(jf_parts) > 1 and jf_parts[1] == "healthy"
        if jf_running and jf_healthy:
            jf_status = "running"
        elif jf_running:
            jf_status = "running"  # starting / no healthcheck
        else:
            jf_status = "stopped"
        results.append({
            "id": "jellyfin",
            "name": "Jellyfin",
            "status": jf_status,
            "raw": jf_out or "not found"
        })
    except Exception as e:
        results.append({"id": "jellyfin", "name": "Jellyfin", "status": "stopped", "raw": "error"})

    return results

@app.get("/api/metrics/disk-usage", response_class=JSONResponse)
def disk_usage_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("disk_usage", window)

@app.get("/api/storage/status", response_class=JSONResponse)
def storage_status(user: str = Depends(authenticate)):
    """Get real-time storage status for all physical disks"""
    try:
        result = subprocess.run(["df", "-h"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        disks = []
        for line in lines:
            if not line.startswith('/dev/'):
                continue
            parts = line.split()
            if len(parts) >= 6:
                disks.append({
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "avail": parts[3],
                    "percent": int(parts[4].replace('%', '')),
                    "mount": parts[5]
                })
        return disks
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/metrics/room-temp", response_class=JSONResponse)
def room_temp_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("room_temp", window)

@app.get("/api/metrics/room-humidity", response_class=JSONResponse)
def room_humidity_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("room_humidity", window)

@app.get("/api/metrics/net-ping", response_class=JSONResponse)
def net_ping_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("net_ping_ms", window)

@app.get("/api/metrics/net-loss", response_class=JSONResponse)
def net_loss_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("net_packet_loss", window)

@app.get("/api/metrics/net-lan", response_class=JSONResponse)
def net_lan_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("net_lan_ms", window)

@app.get("/api/sensors/dht11", response_class=JSONResponse)
def dht11_live(user: str = Depends(authenticate)):
    """Live read from DHT11 sensor via ESP32 MQTT (retained telemetry)"""
    try:
        result = subprocess.run(
            ["mosquitto_sub", "-h", "192.168.0.103", "-t", "orion/esp32/telemetry/dht", "-C", "1", "-W", "3"],
            capture_output=True, text=True, timeout=5
        )
        data = json.loads(result.stdout.strip())
        return {"temperature": data.get("temp"), "humidity": data.get("hum")}
    except Exception as e:
        return {"temperature": None, "humidity": None, "error": str(e)}

    # --- [COMMENTED OUT] Original GPIO reading (DHT11 on Pi GPIO 27) ---
    # Restore this block if sensor is moved back to the Pi.
    # try:
    #     result = subprocess.run(
    #         ["/home/orion/server/venv/bin/python3", "-u", "-c",
    #          "import board,adafruit_dht,time\n"
    #          "d=adafruit_dht.DHT11(board.D27,use_pulseio=False)\n"
    #          "for _ in range(5):\n"
    #          " try:\n"
    #          "  t,h=d.temperature,d.humidity\n"
    #          "  if t is not None and h is not None:\n"
    #          "   print(f'{t},{h}')\n"
    #          "   break\n"
    #          " except: pass\n"
    #          " time.sleep(2)\n"
    #          "d.exit()"],
    #         capture_output=True, text=True, timeout=15
    #     )
    #     output = result.stdout.strip()
    #     if output and ',' in output:
    #         temp, hum = output.split(',')
    #         return {"temperature": float(temp), "humidity": float(hum)}
    #     return {"temperature": None, "humidity": None, "error": "Sensor returned no data"}
    # except Exception as e:
    #     return {"temperature": None, "humidity": None, "error": str(e)}

