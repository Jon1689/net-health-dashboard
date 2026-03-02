import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "data.db"


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                target TEXT NOT NULL,
                dns_resolved INTEGER NOT NULL,
                ip TEXT,
                ping_ok INTEGER NOT NULL,
                notes TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES check_runs(id)
            )
            """
        )
    # Lightweight migration: add latency_ms column if missing
    cols = conn.execute("PRAGMA table_info(check_results)").fetchall()
    col_names = {c["name"] for c in cols}
    if "latency_ms" not in col_names:
        conn.execute("ALTER TABLE check_results ADD COLUMN latency_ms REAL")


def save_run(created_at_iso: str, results: List[Dict[str, Any]]) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO check_runs(created_at) VALUES (?)",
            (created_at_iso,),
        )
        run_id = int(cur.lastrowid)

        conn.executemany(
            """
            INSERT INTO check_results
            (run_id, target, dns_resolved, ip, ping_ok, notes, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    r["target"],
                    1 if r["dns_resolved"] else 0,
                    r.get("ip"),
                    1 if r["ping_ok"] else 0,
                    r["notes"],
                    r.get("latency_ms"),
                )
                for r in results
            ],
        )
        return run_id


def get_recent_runs(limit: int = 10) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        runs = conn.execute(
            """
            SELECT id, created_at
            FROM check_runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        output: List[Dict[str, Any]] = []
        for run in runs:
            results = conn.execute(
                """
                SELECT target, dns_resolved, ip, ping_ok, notes, latency_ms
                FROM check_results
                WHERE run_id = ?
                ORDER BY target ASC
                """,
                (run["id"],),
            ).fetchall()

            output.append(
                {
                    "run_id": run["id"],
                    "created_at": run["created_at"],
                    "results": [
                        {
                            "target": r["target"],
                            "dns_resolved": bool(r["dns_resolved"]),
                            "ip": r["ip"],
                            "ping_ok": bool(r["ping_ok"]),
                            "notes": r["notes"],
                            "latency_ms": r["latency_ms"],
                        }
                        for r in results
                    ],
                }
            )
        return output