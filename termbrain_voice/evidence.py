"""Read-only evidence collectors.

Every command here is a fixed argv list (no shell, no user text interpolated),
runs with a timeout, and only reads state. If a tool is missing, the collector
says so instead of failing, so the pipeline works on any systemd distro.
"""

from __future__ import annotations

import glob
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

Runner = Callable[[Sequence[str]], str]


@dataclass
class Evidence:
    label: str
    command: str
    output: str


def run_readonly(argv: Sequence[str], timeout: int = 8) -> str:
    if shutil.which(argv[0]) is None:
        return f"({argv[0]} not installed)"
    try:
        proc = subprocess.run(
            list(argv), capture_output=True, text=True, timeout=timeout,
            env={"LC_ALL": "C", "PATH": "/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                 "SYSTEMD_PAGER": "", "HOME": str(Path.home())},
        )
    except subprocess.TimeoutExpired:
        return f"(timed out after {timeout}s)"
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.returncode and proc.stderr else "")
    return out.strip() or "(no output)"


def _read_files(pattern: str) -> str:
    parts = []
    for p in sorted(glob.glob(pattern)):
        try:
            parts.append(f"{p}: {Path(p).read_text().strip()}")
        except OSError:
            continue
    return "\n".join(parts) or "(none found)"


def _tail_file(path: str, lines: int, grep: Optional[Sequence[str]] = None) -> str:
    p = Path(path)
    if not p.exists():
        return f"({path} not found)"
    try:
        rows = p.read_text(errors="replace").splitlines()
    except OSError as e:
        return f"(cannot read {path}: {e})"
    if grep:
        rows = [r for r in rows if any(g in r.lower() for g in grep)]
    return "\n".join(rows[-lines:]) or "(nothing matched)"


# (label, argv) pairs. journalctl -p warning keeps only warnings and worse.
COMMANDS: Dict[str, List[tuple]] = {
    "base": [
        ("Kernel", ["uname", "-r"]),
        ("Uptime", ["uptime"]),
        ("Failed units", ["systemctl", "--failed", "--no-legend", "--no-pager"]),
    ],
    "network": [
        ("Devices", ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"]),
        ("Radio switches", ["rfkill", "list"]),
        ("Links", ["ip", "-brief", "link"]),
        ("NetworkManager warnings",
         ["journalctl", "-b", "-u", "NetworkManager", "-p", "warning", "-n", "40", "--no-pager"]),
    ],
    "audio": [
        ("Audio services", ["systemctl", "--user", "is-active", "pipewire", "pipewire-pulse", "wireplumber"]),
        ("Sound server", ["pactl", "info"]),
        ("Sound cards", ["aplay", "-l"]),
        ("WirePlumber warnings",
         ["journalctl", "--user", "-b", "-u", "wireplumber", "-p", "warning", "-n", "30", "--no-pager"]),
    ],
    "bluetooth": [
        ("Bluetooth service", ["systemctl", "is-active", "bluetooth"]),
        ("Radio switches", ["rfkill", "list", "bluetooth"]),
        ("Bluetooth warnings",
         ["journalctl", "-b", "-u", "bluetooth", "-p", "warning", "-n", "30", "--no-pager"]),
    ],
    "boot": [
        ("Boot time", ["systemd-analyze"]),
        ("Slowest units", ["systemd-analyze", "blame", "--no-pager"]),
        ("Boot errors", ["journalctl", "-b", "-p", "err", "-n", "40", "--no-pager"]),
    ],
    "performance": [
        ("Load", ["cat", "/proc/loadavg"]),
        ("Memory", ["free", "-h"]),
        ("Top processes", ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"]),
    ],
    "packages": [
        ("Kernels installed", ["mhwd-kernel", "-li"]),
    ],
    "disk": [
        ("Filesystems", ["df", "-h", "-x", "tmpfs", "-x", "devtmpfs", "-x", "efivarfs"]),
        ("Journal size", ["journalctl", "--disk-usage"]),
    ],
    "power": [
        ("Power profile", ["powerprofilesctl", "get"]),
    ],
    "general": [
        ("Errors this boot", ["journalctl", "-b", "-p", "err", "-n", "40", "--no-pager"]),
    ],
}

# Max lines kept per command, so one noisy log cannot crowd out the rest.
LINE_CAP = {"Slowest units": 12, "Top processes": 10}
DEFAULT_LINE_CAP = 40


def collect(topics: Sequence[str], runner: Runner = run_readonly) -> List[Evidence]:
    items: List[Evidence] = []
    seen = set()
    for topic in ["base", *topics]:
        for label, argv in COMMANDS.get(topic, []):
            key = tuple(argv)
            if key in seen:
                continue
            seen.add(key)
            out = runner(argv)
            cap = LINE_CAP.get(label, DEFAULT_LINE_CAP)
            items.append(Evidence(label, " ".join(argv), "\n".join(out.splitlines()[:cap])))
        if topic == "packages":
            items.append(Evidence(
                "Recent pacman errors/warnings", "tail /var/log/pacman.log (filtered)",
                _tail_file("/var/log/pacman.log", 30, grep=["error", "warning", "failed"]),
            ))
            items.append(Evidence(
                "Last pacman transactions", "tail /var/log/pacman.log",
                _tail_file("/var/log/pacman.log", 15),
            ))
            items.append(Evidence(
                "Unmerged .pacnew files", "find /etc -name '*.pacnew'",
                runner(["find", "/etc", "-maxdepth", "3", "-name", "*.pacnew"]),
            ))
        if topic == "power":
            items.append(Evidence(
                "Battery", "/sys/class/power_supply/BAT*/{status,capacity}",
                _read_files("/sys/class/power_supply/BAT*/status") + "\n"
                + _read_files("/sys/class/power_supply/BAT*/capacity"),
            ))
    return items


def render(items: Sequence[Evidence], budget: int) -> str:
    """Join evidence into prompt text, trimming the longest outputs first to fit the budget."""
    blocks = [[e.label, e.command, e.output] for e in items]

    def total() -> int:
        return sum(len(b[0]) + len(b[1]) + len(b[2]) + 16 for b in blocks)

    while total() > budget:
        longest = max(blocks, key=lambda b: len(b[2]))
        if len(longest[2]) <= 200:
            break
        lines = longest[2].splitlines()
        longest[2] = "\n".join(lines[len(lines) // 2:]) if len(lines) > 4 else longest[2][-200:]
    return "\n\n".join(f"### {b[0]}\n$ {b[1]}\n{b[2]}" for b in blocks)
