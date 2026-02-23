# Network Health & Threat Dashboard

A lightweight dashboard that checks basic network reachability and keeps a timestamped history of results.

## What it does
- Serves a simple web dashboard from FastAPI
- Runs network checks (DNS resolution + ping)
- Stores each check run in SQLite
- Shows recent history on the homepage
- Loads check targets from a JSON config file (no code edits needed)

## Tech
- Python + FastAPI (backend + static dashboard)
- SQLite (history storage)
- Plain HTML/JS (frontend)

## Quick start (Windows / PowerShell)

### 1) Create and activate virtual environment
From the repo root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3) Run the server

```
python -m uvicorn main:app --reload --port 8000
```

### 4) Open the dashboard

http://127.0.0.1:8000

### Configuration:

Edit targets in:
    - backend/targets.json

    Example:
    ```JSON
    {
    "targets": [
        { "name": "Router", "host": "192.168.1.1" },
        { "name": "Pi-hole", "host": "192.168.1.10" }
    ]
    }

### API Endpoints:
    - /health - API Status
    - /checks - run checks and store results
    - /history?limit=10 - recent stored runs
    - /docs - Swagger API docs

### Next Improvements:

    - Scheduled background checks every N seconds
    - Uptime % and response time stats
    - Export history as CSV
    - Authentication for remote access
    - Pull Pi-Hole stats into the dashboard