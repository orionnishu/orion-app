from fastapi import FastAPI, Request, Depends, HTTPException, status, Query
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

def is_login_blocked(ip: str, username: str) -> bool:
    now = int(time.time())
    window_start = now - 600

    q = """
    SELECT COUNT(*)
    FROM login_attempts
    WHERE ip = ?
      AND username = ?
      AND success = 0
      AND ts >= ?
    """
    cnt = db.execute(q, (ip, username, window_start)).fetchone()[0]
    return cnt >= 5

def record_login_attempt(ip, username, success):
    db.execute(
        """
        INSERT INTO login_attempts (ts, ip, username, success)
        VALUES (?, ?, ?, ?)
        """,
        (int(time.time()), ip, username, int(success))
    )
    db.commit()

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

def is_pc_online() -> bool:
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", PC_IP],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

# --------------------
# Routes (AUTH PROTECTED)
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

@app.post("/admin/wake-pc", response_class=HTMLResponse)
def wake_pc(request: Request, user: str = Depends(authenticate)):
    subprocess.run(["wakemypc"])
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Admin",
            "pc_online": False,
            "message": "Wake signal sent"
        }
    )

@app.post("/admin/sleep-pc", response_class=HTMLResponse)
def sleep_pc(request: Request, user: str = Depends(authenticate)):
    subprocess.run(["sleepmypc"])
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Admin",
            "pc_online": True,
            "message": "Sleep command sent"
        }
    )

@app.get("/api/pc-status", response_class=JSONResponse)
def pc_status(user: str = Depends(authenticate)):
    return {"online": is_pc_online()}

# ------------------------------------------------------------------
# NEW: Unified Admin Log Reader (READ-ONLY)
# ------------------------------------------------------------------
# Purpose:
# - Read last N lines from the unified admin log file
# - No parsing, no execution, no side effects
# - Used by Admin UI log panel (polling every ~2s)
#
# Design strictly follows:
# "Scripts are the source of truth.
#  FastAPI is just a window."
# ------------------------------------------------------------------

ADMIN_LOG_FILE = Path("/var/log/orion/admin-actions.log")

@app.get("/admin/logs", response_class=JSONResponse)
def read_admin_logs(
    lines: int = Query(500, ge=10, le=5000),
    user: str = Depends(authenticate)
):
    """
    Read last N lines from the unified admin log file.

    - Append-only log
    - Raw text returned
    - UI decides rendering
    """

    if not ADMIN_LOG_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Admin log file not found"
        )

    try:
        with ADMIN_LOG_FILE.open("r", encoding="utf-8", errors="replace") as f:
            last_lines = deque(f, maxlen=lines)

        return {
            "lines": "".join(last_lines)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

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
    """
    Fetch metric data for a given time window.
    Time calculation is handled entirely by SQLite (localtime).
    """

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