"""Runtime configuration, read from environment variables with safe defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Languages both Prisma v3.0 (STT) and Timbre (TTS) support.
SUPPORTED_LANGS = {
    "en-IN": "English",
    "te-IN": "Telugu",
    "hi-IN": "Hindi",
    "ta-IN": "Tamil",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "pa-IN": "Punjabi",
}

# Words Prisma should favour. Linux vocabulary is rare in everyday speech, so
# keyterm prompting is what stops "pacman" turning into "Pac-Man" or "pack man".
LINUX_KEYTERMS = [
    "Manjaro", "Linux", "KDE", "Plasma", "Wayland", "pacman", "pamac", "yay", "AUR",
    "journalctl", "systemctl", "systemd", "GRUB", "kernel", "NetworkManager", "nmcli",
    "WiFi", "Bluetooth", "PipeWire", "WirePlumber", "PulseAudio", "Timeshift", "pacnew",
    "mkinitcpio", "Ollama", "SSD", "swap", "RAM", "CPU", "GPU", "driver", "firmware",
    "update", "boot", "mirror", "rfkill", "sudo",
]

STT_TOPIC = (
    "A student describes a problem with their Manjaro Linux laptop, often mixing "
    "Telugu and English, naming things like WiFi, sound, boot, updates, pacman or disk space."
)


@dataclass
class Settings:
    gnani_api_key: str = field(default_factory=lambda: os.environ.get("GNANI_API_KEY", ""))
    gnani_base_url: str = field(
        default_factory=lambda: os.environ.get("GNANI_BASE_URL", "https://api.vachana.ai")
    )
    stt_model: str = field(default_factory=lambda: os.environ.get("TBV_STT_MODEL", "prisma-v3.0"))
    # Hint languages, not a lock: Prisma follows the language actually spoken.
    stt_languages: str = field(default_factory=lambda: os.environ.get("TBV_STT_LANGS", "te-IN,en-IN"))
    # codemix keeps English words (WiFi, pacman) in Latin script inside Telugu speech.
    stt_format: str = field(default_factory=lambda: os.environ.get("TBV_STT_FORMAT", "codemix"))
    tts_model: str = field(default_factory=lambda: os.environ.get("TBV_TTS_MODEL", "timbre-v3.0"))
    tts_voice: str = field(default_factory=lambda: os.environ.get("TBV_TTS_VOICE", "Shivani"))
    tts_speed: float = field(default_factory=lambda: float(os.environ.get("TBV_TTS_SPEED", "1.0")))
    ollama_model: str = field(default_factory=lambda: os.environ.get("TBV_OLLAMA_MODEL", "gemma3:4b"))
    ollama_host: str = field(
        default_factory=lambda: os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    )
    offline: bool = field(default_factory=lambda: os.environ.get("TBV_OFFLINE", "") == "1")
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("TBV_DATA_DIR", Path.home() / ".local" / "share" / "termbrain-voice")
        )
    )
    max_record_seconds: int = 28  # Prisma REST accepts clips up to 30 s.
    evidence_char_budget: int = 6000  # Keeps prompts small enough for 3-4B CPU models.
