import platform
import socket
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional
import re


@dataclass
class CheckResult:
    target: str
    dns_resolved: bool
    ip: Optional[str]
    ping_ok: bool
    notes: str


def resolve_dns(hostname: str) -> (bool, Optional[str], str):
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip, "Resolved"
    except socket.gaierror:
        return False, None, "DNS resolution failed"


def ping_host(target: str, timeout_ms: int = 1000) -> (bool, str, Optional[float]):
    """
    Uses OS ping command. Returns (ok, note, latency_ms).
    Latency parsing is best-effort and may be None sometimes.
    """
    system = platform.system().lower()

    if "windows" in system:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), target]
    else:
        cmd = ["ping", "-c", "1", target]

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        ok = completed.returncode == 0
        out = (completed.stdout or "") + "\n" + (completed.stderr or "")

        latency_ms: Optional[float] = None

        # Windows often contains: "Average = 23ms"
        m = re.search(r"Average\s*=\s*(\d+)\s*ms", out, re.IGNORECASE)
        if m:
            latency_ms = float(m.group(1))

        # Linux/macOS often contains: "time=23.4 ms"
        if latency_ms is None:
            m = re.search(r"time[=<]\s*([\d\.]+)\s*ms", out, re.IGNORECASE)
            if m:
                latency_ms = float(m.group(1))

        note = "Ping ok" if ok else "Ping failed"
        return ok, note, latency_ms

    except subprocess.TimeoutExpired:
        return False, "Ping timed out", None
    except Exception as e:
        return False, f"Ping error: {e}", None


def run_checks(targets: List[Dict[str, str]]) -> List[Dict]:
    results: List[Dict] = []

    for item in targets:
        name = item.get("name", item["host"])
        host = item["host"]

        dns_ok, ip, dns_note = resolve_dns(host)
        ping_ok, ping_note, latency_ms = ping_host(host)

        notes = f"{dns_note}; {ping_note}"
        results.append(
            {
                "target": host,
                "name": name,
                "dns_resolved": dns_ok,
                "ip": ip,
                "ping_ok": ping_ok,
                "notes": notes,
                "latency_ms": latency_ms,
            }
        )

    return results