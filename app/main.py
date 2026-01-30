from fastapi import FastAPI, Request, Depends, HTTPException, status, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import subprocess
import secrets
import sqlite3
import time
from pathlib import Path
from collections import deque

app = FastAPI(title="Orion Home Server")

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
PC_IP = "192.168.50.2"
SCRIPTS_DIR = Path("/home/orion/server/scripts")

def is_pc_online() -> bool:
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", PC_IP],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

@app.get("/api/pc-status", response_class=JSONResponse)
def pc_status():
    return {"online": is_pc_online()}

# --------------------
# UI Routes (HTML only)
# --------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard"}
    )

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard"}
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
# JSON Admin Trigger Endpoints (ASYNC, NO PAGE RELOAD)
# ------------------------------------------------------------------

@app.post("/admin/api/wake-pc", response_class=JSONResponse)
def api_wake_pc(user: str = Depends(authenticate)):
    subprocess.Popen([str(SCRIPTS_DIR / "wakemypc.sh")])
    return {"status": "ok", "action": "wake-pc"}

@app.post("/admin/api/sleep-pc", response_class=JSONResponse)
def api_sleep_pc(user: str = Depends(authenticate)):
    subprocess.Popen([str(SCRIPTS_DIR / "sleepmypc.sh")])
    return {"status": "ok", "action": "sleep-pc"}

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
    "2h": "-2 hours",
    "6h": "-6 hours",
    "24h": "-24 hours",
    "7d": "-7 days",
}

def _metric_series(metric_name: str, window: str):
    if window not in WINDOW_MAP:
        window = "24h"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(f"""
        SELECT ts, value
        FROM metrics
        WHERE name = ?
          AND ts >= datetime('now', '{WINDOW_MAP[window]}', 'localtime')
        ORDER BY ts
    """, (metric_name,))

    rows = cur.fetchall()
    conn.close()

    return {
        "labels": [r[0] for r in rows],
        "values": [float(r[1]) for r in rows],
    }

@app.get("/api/metrics/cpu-temp", response_class=JSONResponse)
def cpu_temp_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("cpu_temp", window)

@app.get("/api/metrics/ram-used", response_class=JSONResponse)
def ram_used_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("ram_used", window)

@app.get("/api/metrics/load-1m", response_class=JSONResponse)
def load_1m_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("load_1m", window)

@app.get("/api/metrics/fan-rpm", response_class=JSONResponse)
def fan_rpm_series(window: str = "24h", user: str = Depends(authenticate)):
    return _metric_series("fan_rpm", window)