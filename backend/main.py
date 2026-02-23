from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from network_checks import run_checks
from datetime import datetime, timezone
from storage import init_db, save_run, get_recent_runs

app = FastAPI(title="Network Health & Threat Dashboard")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
init_db()

# Serve /static/* files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def homepage():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/checks")
def checks():
    targets = [
        "1.1.1.1",
        "8.8.8.8",
        "google.com",
    ]
    results = run_checks(targets)
    created_at = datetime.now(timezone.utc).isoformat()
    run_id = save_run(created_at, results)
    return {"run_id": run_id, "created_at": created_at, "results": results}

@app.get("/history")
def history(limit: int = 10):
    return {"runs": get_recent_runs(limit=limit)}
