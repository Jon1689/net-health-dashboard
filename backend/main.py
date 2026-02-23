from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from network_checks import run_checks

app = FastAPI(title="Network Health & Threat Dashboard")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

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
    # You can change these later (router, pihole, google dns, etc.)
    targets = [
        "1.1.1.1",            # Cloudflare DNS (IP avoids DNS dependency)
        "8.8.8.8",            # Google DNS
        "google.com",         # tests DNS + reachability
    ]
    return {"results": run_checks(targets)}