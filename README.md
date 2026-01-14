# ORION Home Server

This repository contains the ORION Home Server code and configs:
- FastAPI admin dashboard and monitoring UI (`app/`)
- Services: `pi-monitor/`, `webdav/`
- Project layout follows the canonical `~/server/` structure used on the Pi

Important:
- Do NOT commit secrets, database files, or the mounted NAS contents (`/mnt/orion-nas/`).
- Collector owns timestamps; DB never auto‑generates times — keep that behavior unchanged.

See [`docs/architecture.md`](docs/architecture.md) for full architectural context.

Getting started (local)
1. Create Python virtualenv and install dependencies:
   ```bash
   python3 -m venv venv
   . venv/bin/activate
   pip install -r requirements.txt
   ```
2. Edit configs (paths are absolute by design). Start webdav and FastAPI per the project's run scripts.

Contributing
- Keep per‑user isolation.
- Do not change timestamp behavior or DB schema without corresponding migration scripts.
