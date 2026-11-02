"""Classify suggested shell commands before they are shown or spoken.

TermBrain Voice never executes a suggested command. This guard decides how each
one is presented: read-only commands are marked safe to try, system-changing
ones are marked "review first", and destructive ones are withheld entirely.
"""

from __future__ import annotations

import re
from typing import List, Tuple

SAFE, CHANGES, BLOCKED = "read-only", "changes system", "blocked"

_DESTRUCTIVE = [
    r"\brm\s+(-\w*[rf]\w*\s+)+",           # rm -rf / rm -r -f
    r"\bdd\b.*\bof=",                       # writing raw blocks
    r"\bmkfs(\.\w+)?\b", r"\bwipefs\b", r"\bshred\b", r"\bsgdisk\b", r"\bfdisk\b", r"\bparted\b",
    r"\bpacman\s+-R\w*d\w*d",              # -Rdd skips dependency checks
    r"\bpacman\b.*--overwrite\s+['\"]?/?\*", # blanket overwrite
    r"\bchmod\s+-R\s+0?777\b", r"\bchown\s+-R\s+\S+\s+/(\s|$)",
    r">\s*/dev/(sd|nvme|mmcblk)", r":\(\)\s*\{", r"\bcurl\b.*\|\s*(sudo\s+)?(ba)?sh\b",
    r"\bfind\b.*\s-(delete|exec)\b",
    r"\bwget\b.*\|\s*(sudo\s+)?(ba)?sh\b", r"\bsystemctl\s+(mask|disable)\s+(systemd-|dbus|NetworkManager)",
]

_READONLY_PREFIXES = [
    "journalctl", "systemctl status", "systemctl --failed", "systemctl is-active", "systemctl list",
    "systemctl --user status", "systemctl --user is-active", "systemd-analyze", "nmcli device",
    "nmcli general", "nmcli radio", "nmcli -t", "nmcli connection show", "ip a", "ip addr", "ip link",
    "ip -brief", "ip route", "ping", "rfkill list", "pactl info", "pactl list", "aplay -l",
    "wpctl status", "bluetoothctl show", "bluetoothctl devices", "df", "du", "free", "uname", "uptime",
    "lsblk", "lspci", "lsusb", "inxi", "cat ", "less ", "tail ", "head ", "grep ", "ls", "find ",
    "pacman -Q", "pacman -Si", "pacman -Ss", "pacdiff -o", "mhwd-kernel -li", "mhwd -li", "dmesg",
    "sensors", "top", "htop", "ps ", "resolvectl status", "timedatectl", "powerprofilesctl get",
    "checkrebuild", "sudo journalctl", "sudo dmesg",
]


def classify(command: str) -> str:
    cmd = command.strip().strip("`").strip()
    if not cmd:
        return BLOCKED
    for pat in _DESTRUCTIVE:
        if re.search(pat, cmd):
            return BLOCKED
    # Any chaining or redirection makes "read-only" impossible to promise.
    if re.search(r"(;|&&|\|\||\|\s*(sudo|tee|sh|bash)|>|\$\()", cmd):
        return CHANGES
    for prefix in _READONLY_PREFIXES:
        if cmd == prefix.strip() or cmd.startswith(prefix):
            return SAFE
    return CHANGES


def triage(steps: List[dict]) -> Tuple[List[dict], List[dict]]:
    """Split LLM steps into (kept, blocked), adding a `safety` field to kept ones."""
    kept, blocked = [], []
    for step in steps:
        cmd = str(step.get("command", "")).strip()
        level = classify(cmd) if cmd else SAFE
        if level == BLOCKED and cmd:
            blocked.append({**step, "safety": BLOCKED})
        else:
            kept.append({**step, "safety": level if cmd else "info"})
    return kept, blocked
