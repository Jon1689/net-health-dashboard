import platform
import socket
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional
import json


@dataclass
class CheckResult:
    target: str
    dns_resolved: bool
    ip: Optional[str]
    ping_ok: bool
    notes: str


def load_targets():
    targets_file = BASE_DIR / "targets.json"
    with open(targets_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("targets", [])

def resolve_dns(hostname: str) -> (bool, Optional[str], str):
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip, "Resolved"
    except socket.gaierror:
        return False, None, "DNS resolution failed"


def ping_host(target: str, timeout_ms: int = 1000) -> (bool, str):
    """
    Uses the OS ping command (works on Windows/macOS/Linux).
    Windows: ping -n 1 -w <ms>
    Linux/macOS: ping -c 1 -W <sec> (macOS uses -W in ms? varies) - we’ll keep it basic.
    """
    system = platform.system().lower()

    if "windows" in system:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), target]
    else:
        # 1 packet, wait ~1s
        cmd = ["ping", "-c", "1", target]

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        ok = completed.returncode == 0
        return ok, "Ping ok" if ok else "Ping failed"
    except subprocess.TimeoutExpired:
        return False, "Ping timed out"
    except Exception as e:
        return False, f"Ping error: {e}"


def run_checks(targets: List[Dict[str, str]]) -> List[Dict]:
    results: List[Dict] = []

    for item in targets:
        name = item.get("name", item["host"])
        host = item["host"]

        dns_ok, ip, dns_note = resolve_dns(host)
        ping_ok, ping_note = ping_host(host)

        notes = f"{dns_note}; {ping_note}"
        results.append(
            {
                "target": host,
                "name": name,
                "dns_resolved": dns_ok,
                "ip": ip,
                "ping_ok": ping_ok,
                "notes": notes,
            }
        )

    return results