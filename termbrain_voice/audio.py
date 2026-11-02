"""Microphone capture and playback through the tools every Manjaro KDE box already has.

PipeWire's pw-record/pw-play are tried first, then ALSA's arecord/aplay, so there
is no PortAudio or compiled dependency to install.
"""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
import wave
from pathlib import Path
from typing import List, Optional


def _recorder(out: Path) -> Optional[List[str]]:
    if shutil.which("pw-record"):
        return ["pw-record", "--rate", "16000", "--channels", "1", "--format", "s16", str(out)]
    if shutil.which("arecord"):
        return ["arecord", "-q", "-f", "S16_LE", "-r", "16000", "-c", "1", str(out)]
    return None


def record(out: Path, max_seconds: int = 28) -> Path:
    """Record 16 kHz mono WAV until Enter is pressed or max_seconds elapse."""
    cmd = _recorder(out)
    if cmd is None:
        raise RuntimeError("No recorder found. Install pipewire (pw-record) or alsa-utils (arecord).")
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    stop = threading.Event()

    def wait_enter() -> None:
        try:
            input()
        except EOFError:
            pass
        stop.set()

    threading.Thread(target=wait_enter, daemon=True).start()
    start = time.monotonic()
    while not stop.is_set() and time.monotonic() - start < max_seconds:
        time.sleep(0.05)
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    if not out.exists() or out.stat().st_size < 1000:
        raise RuntimeError("Recording is empty. Check the microphone in KDE System Settings > Sound.")
    return out


def duration_seconds(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except (wave.Error, EOFError, OSError):
        return 0.0


def play(path: Path) -> bool:
    for player in (["pw-play"], ["paplay"], ["aplay", "-q"]):
        if shutil.which(player[0]):
            subprocess.run([*player, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    return False
