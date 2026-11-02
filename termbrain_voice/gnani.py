"""Thin client for Gnani Prisma (speech-to-text) and Timbre (text-to-speech).

Endpoints and error shapes follow https://docs.gnani.ai (checked November 2026):
  STT REST  POST {base}/stt/v3                multipart, header X-API-Key-ID, clips <= 30 s
  TTS REST  POST {base}/api/v1/tts/inference  JSON, returns binary audio

Only two things ever leave the machine: the recorded audio clip, and the short
spoken answer text. Logs and system evidence never do.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from .config import LINUX_KEYTERMS, STT_TOPIC, SUPPORTED_LANGS, Settings

RETRYABLE = {429, 500, 502, 503, 504}


class GnaniError(RuntimeError):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"Gnani API {status} {code}: {message}")
        self.status = status
        self.code = code
        self.message = message


@dataclass
class Transcript:
    text: str
    language: str  # e.g. "te-IN"
    request_id: str = ""
    latency_s: float = 0.0


def parse_error(resp: requests.Response) -> GnaniError:
    """Normalise Gnani's several error shapes into one exception."""
    status = resp.status_code
    try:
        body = resp.json()
    except ValueError:
        return GnaniError(status, "HTTP_ERROR", resp.text[:200] or resp.reason)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):  # STT envelope: {"success": false, "error": {"type", "message"}}
            return GnaniError(status, err.get("type", "ERROR"), err.get("message", ""))
        detail = body.get("detail")
        if isinstance(detail, dict):  # auth / rate limit: {"detail": {"error_code", "message"}}
            return GnaniError(status, detail.get("error_code", "ERROR"), detail.get("message", ""))
        if isinstance(detail, list):  # 422 validation
            return GnaniError(status, "VALIDATION_ERROR", json.dumps(detail)[:300])
        if "code" in body:  # 504 UPSTREAM_TIMEOUT
            return GnaniError(status, body.get("code", "ERROR"), body.get("message", ""))
        if "message" in body:  # TTS flat body
            return GnaniError(status, "ERROR", str(body["message"]))
    return GnaniError(status, "ERROR", str(body)[:200])


class GnaniClient:
    def __init__(self, settings: Settings, session: Optional[requests.Session] = None):
        if not settings.gnani_api_key:
            raise GnaniError(401, "MISSING_API_KEY", "Set GNANI_API_KEY (from https://app.gnani.ai).")
        self.s = settings
        self.http = session or requests.Session()
        self.http.headers.update({"X-API-Key-ID": settings.gnani_api_key})

    def _post(self, path: str, attempts: int = 3, **kwargs) -> requests.Response:
        """POST with backoff. Free accounts allow one active request, so 429 is expected."""
        url = self.s.gnani_base_url.rstrip("/") + path
        delay = 1.0
        for attempt in range(1, attempts + 1):
            resp = self.http.post(url, timeout=60, **kwargs)
            if resp.status_code < 400:
                return resp
            if resp.status_code not in RETRYABLE or attempt == attempts:
                raise parse_error(resp)
            time.sleep(delay)
            delay *= 2
        raise AssertionError("unreachable")

    def transcribe(self, audio_path: Path) -> Transcript:
        data = {
            "model": self.s.stt_model,
            "language_code": self.s.stt_languages,
            "format": self.s.stt_format,
            "keyterms": json.dumps(LINUX_KEYTERMS),
            "topic": STT_TOPIC,
        }
        t0 = time.perf_counter()
        with open(audio_path, "rb") as f:
            files = {"audio_file": (audio_path.name, f, _mime(audio_path))}
            resp = self._post("/stt/v3", data=data, files=files)
        body = resp.json()
        if not body.get("success", True):
            raise parse_error(resp)
        lang = body.get("detected_language_code") or self.s.stt_languages.split(",")[0]
        return Transcript(
            text=(body.get("transcript") or "").strip(),
            language=lang if lang in SUPPORTED_LANGS else "en-IN",
            request_id=body.get("request_id", ""),
            latency_s=time.perf_counter() - t0,
        )

    def synthesize(self, text: str, language: str, out_path: Path) -> Path:
        payload = {
            "text": text,
            "voice": self.s.tts_voice,
            "model": self.s.tts_model,
            "language": language if language in SUPPORTED_LANGS else "en-IN",
            "speed": self.s.tts_speed,
            "audio_config": {
                "sample_rate": 24000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        }
        resp = self._post("/api/v1/tts/inference", json=payload)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(resp.content)
        return out_path


def _mime(path: Path) -> str:
    return {
        ".wav": "audio/wav", ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".flac": "audio/flac",
        ".m4a": "audio/mp4", ".aac": "audio/aac",
    }.get(path.suffix.lower(), "application/octet-stream")


class OfflineGnani:
    """Stand-in used by tests and `--offline`: no network, deterministic output."""

    def __init__(self, transcript: str = "", language: str = "en-IN"):
        self._text = transcript
        self._lang = language

    def transcribe(self, audio_path: Path) -> Transcript:
        sidecar = Path(str(audio_path) + ".txt")
        text = self._text or (sidecar.read_text(encoding="utf-8").strip() if sidecar.exists() else "")
        return Transcript(text=text, language=self._lang, request_id="offline")

    def synthesize(self, text: str, language: str, out_path: Path) -> Path:
        import wave

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out_path), "wb") as w:  # 0.2 s of silence
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(b"\x00\x00" * 3200)
        return out_path
