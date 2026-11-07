"""Local reasoning with Ollama. Nothing in this module talks to the internet."""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional, Sequence

from .config import SUPPORTED_LANGS
from .kb import Doc

SYSTEM_PROMPT = """You are TermBrain Voice, a calm senior Linux engineer helping a student on Manjaro Linux (KDE).
You answer from the EVIDENCE (real command output from their machine) and the RUNBOOKS (curated fixes).
Rules:
- Only state a cause the evidence supports. If evidence is inconclusive, say so and give the next read-only check.
- Prefer read-only diagnostic commands first, then the smallest safe fix. Never suggest commands that delete data,
  format disks, or skip pacman dependency checks.
- Cite runbook ids you used in "sources".
- "spoken_answer" is read aloud by a text-to-speech voice: at most 3 short sentences, no markdown, no backticks,
  no raw command syntax, no URLs. Say what is wrong and the first thing to do, in plain words.
Return ONLY a JSON object with exactly these keys:
{"spoken_answer": str, "diagnosis": str, "likely_cause": str,
 "steps": [{"command": str, "why": str}], "sources": [str], "confidence": "low"|"medium"|"high"}"""


def build_prompt(transcript: str, language: str, evidence: str, docs: Sequence[Doc]) -> str:
    lang_name = SUPPORTED_LANGS.get(language, "English")
    if language == "en-IN":
        lang_rule = "Write spoken_answer in simple Indian English."
    else:
        lang_rule = (
            f"Write spoken_answer in {lang_name} script, the way a friend speaks it: keep technical words such as "
            "WiFi, update, pacman, settings in English (Latin letters). Write diagnosis and steps in English."
        )
    runbooks = "\n\n".join(f"[{d.id}] {d.title}\n{d.body}" for d in docs) or "(none matched)"
    return (
        f"USER SAID ({lang_name}): {transcript}\n\n"
        f"LANGUAGE RULE: {lang_rule}\n\n"
        f"EVIDENCE (redacted, from this machine):\n{evidence}\n\n"
        f"RUNBOOKS:\n{runbooks}\n\n"
        "Respond with the JSON object now."
    )


def parse_answer(raw: str) -> Dict[str, Any]:
    """Tolerate the ways small models wrap JSON (code fences, leading prose)."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    elif not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start:end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _fallback(raw)
    if not isinstance(data, dict):
        return _fallback(raw)
    steps = data.get("steps") or []
    if not isinstance(steps, list):
        steps = []
    clean_steps: List[Dict[str, str]] = []
    for s in steps:
        if isinstance(s, dict):
            clean_steps.append({"command": str(s.get("command", "")).strip().strip("`"),
                                "why": str(s.get("why", "")).strip()})
        elif isinstance(s, str):
            clean_steps.append({"command": "", "why": s})
    conf = str(data.get("confidence", "low")).lower()
    return {
        "spoken_answer": speakable(str(data.get("spoken_answer", ""))),
        "diagnosis": str(data.get("diagnosis", "")).strip(),
        "likely_cause": str(data.get("likely_cause", "")).strip(),
        "steps": clean_steps,
        "sources": [str(x) for x in (data.get("sources") or []) if isinstance(x, (str, int))],
        "confidence": conf if conf in {"low", "medium", "high"} else "low",
    }


def _fallback(raw: str) -> Dict[str, Any]:
    return {
        "spoken_answer": speakable(raw)[:300],
        "diagnosis": raw.strip(),
        "likely_cause": "",
        "steps": [],
        "sources": [],
        "confidence": "low",
    }


def speakable(text: str, limit: int = 450) -> str:
    """Make text safe to read aloud: no markdown, code, or URLs, and short enough for TTS."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[*_#>\[\]]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        cut = max(text.rfind(". ", 0, limit), text.rfind("। ", 0, limit))
        text = text[: cut + 1] if cut > 80 else text[:limit].rstrip() + "…"
    return text


ChatFn = Callable[..., Any]


def ask_local_llm(prompt: str, model: str, host: str, chat: Optional[ChatFn] = None) -> Dict[str, Any]:
    if chat is None:
        import ollama

        # Ollama runs locally: ignore HTTP(S)_PROXY, which httpx would otherwise
        # apply to localhost (common on campus/corporate networks) and get a 404.
        local = re.search(r"//(localhost|127\.0\.0\.1|\[::1\])(:|/|$)", host) is not None
        client = ollama.Client(host=host, trust_env=not local)
        chat = client.chat
    try:
        resp = chat(
            model=model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.2, "num_ctx": 8192},
        )
    except ConnectionError as e:
        raise RuntimeError(f"Ollama is not reachable at {host}. Start it with: systemctl start ollama") from e
    except Exception as e:  # ollama.ResponseError and friends
        if "not found" in str(e).lower():
            raise RuntimeError(f"Model {model} is not pulled. Run: ollama pull {model}") from e
        raise RuntimeError(f"Local LLM failed: {e}") from e
    content = resp["message"]["content"] if isinstance(resp, dict) else resp.message.content
    return parse_answer(content)
