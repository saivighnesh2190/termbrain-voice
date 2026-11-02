"""Scrub identifiers from evidence before it reaches any model or screen recording.

Evidence stays local either way, but redacting means a demo video, a pasted
session file or a bug report never leaks your MAC, IPs, hostname or username.
"""

from __future__ import annotations

import getpass
import re
import socket
from typing import Iterable, Optional

_PATTERNS = [
    (re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b"), "<MAC>"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "<UUID>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<EMAIL>"),
    (re.compile(r"\b(?!127\.0\.0\.1\b)(?:\d{1,3}\.){3}\d{1,3}\b"), "<IP>"),
    (re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}\b"), "<IPV6>"),
    (re.compile(r'(SSID[=: ]+|ssid[=: ]+|connection ")[^"\n]+'), r"\1<SSID>"),
]


def redact(text: str, extra_secrets: Optional[Iterable[str]] = None) -> str:
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    names = set(extra_secrets or [])
    try:
        names.add(socket.gethostname())
    except OSError:
        pass
    try:
        names.add(getpass.getuser())
    except Exception:  # noqa: BLE001 - getuser raises various errors without a passwd entry
        pass
    for name in sorted((n for n in names if n and len(n) >= 3), key=len, reverse=True):
        if name in {"root", "localhost"}:
            continue
        text = re.sub(rf"(?<![\w-]){re.escape(name)}(?![\w-])", "<USER_OR_HOST>", text)
    return text
