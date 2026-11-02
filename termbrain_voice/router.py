"""Map what the user said to the evidence worth collecting.

Deterministic on purpose: it is fast on a CPU-only laptop, it cannot hallucinate
a command, and it is testable (see evals/router_cases.jsonl). Prisma's `codemix`
style keeps English tech words in Latin script, so a Telugu sentence like
"నా WiFi పని చేయడం లేదు" still carries the token "wifi".
"""

from __future__ import annotations

import re
from typing import Dict, List

TOPICS: Dict[str, List[str]] = {
    "network": [
        "wifi", "wi-fi", "wi fi", "internet", "network", "ethernet", "lan", "router", "hotspot",
        "connect", "connection", "dns", "networkmanager", "nmcli", "ip address",
        "వైఫై", "వై-ఫై", "ఇంటర్నెట్", "నెట్‌వర్క్", "నెట్వర్క్", "నెట్", "కనెక్ట్", "హాట్‌స్పాట్",
    ],
    "audio": [
        "sound", "audio", "speaker", "speakers", "headphone", "headphones", "earphone", "mic",
        "microphone", "volume", "pipewire", "wireplumber", "pulseaudio", "no sound",
        "సౌండ్", "శబ్దం", "ఆడియో", "స్పీకర్", "హెడ్‌ఫోన్", "మైక్", "వాల్యూమ్",
    ],
    "bluetooth": ["bluetooth", "blue tooth", "airpods", "pair", "pairing", "బ్లూటూత్", "బ్లూ టూత్"],
    "boot": [
        "boot", "booting", "startup", "start up", "grub", "login screen", "black screen",
        "slow start", "takes long to start", "shutdown", "shut down",
        "బూట్", "స్టార్ట్", "స్టార్టప్", "షట్‌డౌన్", "బ్లాక్ స్క్రీన్", "గ్రబ్",
    ],
    "performance": [
        "slow", "slowly", "lag", "lags", "lagging", "hang", "hangs", "hanging",
        "freeze", "freezes", "freezing", "frozen", "stuck", "heat", "hot",
        "fan", "cpu", "ram", "memory", "high load",
        "స్లో", "నెమ్మది", "నెమ్మదిగా", "హ్యాంగ్", "ఫ్రీజ్", "వేడి", "మెమరీ",
    ],
    "packages": [
        "update", "upgrade", "pacman", "pamac", "yay", "aur", "package", "install", "pacnew",
        "mirror", "keyring", "dependency", "dependencies", "conflict",
        "అప్డేట్", "అప్‌డేట్", "అప్గ్రేడ్", "ప్యాకేజ్", "ఇన్‌స్టాల్", "ఇన్స్టాల్",
    ],
    "disk": [
        "disk", "storage", "space", "full", "ssd", "hdd", "partition", "no space",
        "డిస్క్", "స్టోరేజ్", "స్పేస్", "ఫుల్", "నిండిపోయింది",
    ],
    "power": [
        "battery", "charging", "charge", "charger", "power", "suspend", "sleep", "drain",
        "బ్యాటరీ", "ఛార్జ్", "ఛార్జింగ్", "చార్జ్", "పవర్",
    ],
}

def _norm(text: str) -> str:
    text = text.lower().replace("\u200c", "").replace("\u200d", "")  # strip ZWNJ/ZWJ
    return re.sub(r"\s+", " ", text)


def route(transcript: str, max_topics: int = 2) -> List[str]:
    """Return up to `max_topics` topics ranked by keyword hits; ["general"] if none."""
    text = _norm(transcript)
    scores: Dict[str, int] = {}
    for topic, words in TOPICS.items():
        hits = 0
        for w in words:
            w_n = _norm(w)
            if w_n.isascii():
                if re.search(rf"(?<![a-z]){re.escape(w_n)}(?![a-z])", text):
                    hits += 2 if " " in w_n else 1
            elif w_n in text:  # Telugu script: substring match tolerates suffixes like -లో, -కి
                hits += 1
        if hits:
            scores[topic] = hits
    if not scores:
        return ["general"]
    ranked = sorted(scores, key=lambda t: (-scores[t], list(TOPICS).index(t)))
    return ranked[:max_topics]
