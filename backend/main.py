from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from network_checks import run_checks
from storage import init_db, save_run, get_recent_runs
import json
import asyncio
from datetime import datetime, timezone
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
import secrets

app = FastAPI(title="Network Health & Threat Dashboard")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_dotenv()  # loads backend/.env when running locally

security = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    expected_user = os.environ.get("DASH_USER", "admin")
    expected_pass = os.environ.get("DASH_PASS", "change-me")

    user_ok = secrets.compare_digest(credentials.username, expected_user)
    pass_ok = secrets.compare_digest(credentials.password, expected_pass)

    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def load_targets():
    targets_file = BASE_DIR / "targets.json"
    with open(targets_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("targets", [])

async def scheduled_monitoring_loop(interval_seconds: int = 30):
    while True:
        try:
            targets = load_targets()
            results = run_checks(targets)
            created_at = datetime.now(timezone.utc).isoformat()
            save_run(created_at, results)
        except Exception as e:
            # Keep it simple for now: don't crash the loop
            print(f"[monitor] error: {e}")

        await asyncio.sleep(interval_seconds)

init_db()

# Serve /static/* files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def homepage(username: str = Depends(require_auth)):
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/checks")
def checks(username: str = Depends(require_auth)):
    targets = load_targets()
    results = run_checks(targets)
    created_at = datetime.now(timezone.utc).isoformat()
    run_id = save_run(created_at, results)
    return {"run_id": run_id, "created_at": created_at, "results": results}

@app.get("/history")
def history(limit: int = 10, username: str = Depends(require_auth)):
    return {"runs": get_recent_runs(limit=limit)}

@app.on_event("startup")
async def start_background_monitoring():
    # Prevent double-start in the same process (common during dev reloads).
    if getattr(app.state, "monitor_task", None) is None:
        interval_seconds = 30  # change later if you want
        app.state.monitor_task = asyncio.create_task(
            scheduled_monitoring_loop(interval_seconds)
        )

@app.get("/openapi.json")
def openapi(username: str = Depends(require_auth)):
    return app.openapi()
