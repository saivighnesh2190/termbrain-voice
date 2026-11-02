"""The voice loop: hear -> route -> collect -> redact -> retrieve -> reason -> guard -> speak."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import evidence as ev
from .config import SUPPORTED_LANGS, Settings
from .gnani import Transcript
from .kb import Retriever, error_lines
from .llm import ask_local_llm, build_prompt
from .redact import redact
from .router import route
from .safety import triage


@dataclass
class Session:
    transcript: str = ""
    language: str = "en-IN"
    reply_language: str = "en-IN"
    topics: List[str] = field(default_factory=list)
    evidence: List[Dict[str, str]] = field(default_factory=list)
    sources_retrieved: List[str] = field(default_factory=list)
    answer: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, str]] = field(default_factory=list)
    blocked_steps: List[Dict[str, str]] = field(default_factory=list)
    spoken_audio: str = ""
    timings: Dict[str, float] = field(default_factory=dict)
    sent_to_cloud: Dict[str, str] = field(default_factory=dict)

    def save(self, data_dir: Path) -> Path:
        out = data_dir / "sessions" / time.strftime("%Y%m%d-%H%M%S.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        return out


class Timer:
    def __init__(self, timings: Dict[str, float], name: str):
        self.t, self.name = timings, name

    def __enter__(self):
        self.start = time.perf_counter()

    def __exit__(self, *exc):
        self.t[self.name] = round(time.perf_counter() - self.start, 2)


def run(
    settings: Settings,
    speech,  # GnaniClient or OfflineGnani
    audio_path: Optional[Path] = None,
    text: Optional[str] = None,
    text_language: str = "en-IN",
    reply_language: Optional[str] = None,
    speak: bool = True,
    runner: ev.Runner = ev.run_readonly,
    chat: Optional[Callable[..., Any]] = None,
    retriever: Optional[Retriever] = None,
    on_stage: Callable[[str, Session], None] = lambda stage, s: None,
) -> Session:
    s = Session()

    # 1. Hear (Gnani Prisma). Only the audio clip leaves the machine.
    if text is not None:
        tr = Transcript(text=text.strip(), language=text_language)
    else:
        if audio_path is None:
            raise ValueError("Give either audio_path or text.")
        with Timer(s.timings, "stt"):
            tr = speech.transcribe(audio_path)
        s.sent_to_cloud["stt"] = f"audio clip {audio_path.name} -> Gnani Prisma ({settings.stt_model})"
    if not tr.text:
        raise RuntimeError("Prisma returned an empty transcript. Speak closer to the mic and try again.")
    s.transcript, s.language = tr.text, tr.language
    s.reply_language = reply_language if reply_language in SUPPORTED_LANGS else tr.language
    on_stage("heard", s)

    # 2. Route + collect read-only evidence, locally.
    s.topics = route(tr.text)
    with Timer(s.timings, "evidence"):
        items = ev.collect(s.topics, runner=runner)
    for item in items:
        item.output = redact(item.output)
    s.evidence = [asdict(i) for i in items]
    evidence_text = ev.render(items, settings.evidence_char_budget)
    on_stage("evidence", s)

    # 3. Retrieve runbooks (local BM25).
    retriever = retriever or Retriever()
    docs = retriever.search(f"{tr.text}\n{' '.join(s.topics)}\n{error_lines(evidence_text)}", s.topics, k=3)
    s.sources_retrieved = [d.id for d in docs]

    # 4. Reason with the local LLM.
    with Timer(s.timings, "llm"):
        answer = ask_local_llm(
            build_prompt(tr.text, s.reply_language, evidence_text, docs),
            model=settings.ollama_model, host=settings.ollama_host, chat=chat,
        )
    known = set(s.sources_retrieved)
    answer["sources"] = [x for x in answer["sources"] if x in known]  # drop invented citations
    s.answer = answer

    # 5. Guard: never show destructive commands as advice.
    s.steps, s.blocked_steps = triage(answer["steps"])
    on_stage("answer", s)

    # 6. Speak (Gnani Timbre). Only the short spoken answer leaves the machine.
    if speak and answer["spoken_answer"]:
        out = settings.data_dir / "audio" / time.strftime("reply-%Y%m%d-%H%M%S.wav")
        with Timer(s.timings, "tts"):
            speech.synthesize(answer["spoken_answer"], s.reply_language, out)
        s.spoken_audio = str(out)
        s.sent_to_cloud["tts"] = f"{len(answer['spoken_answer'])} chars of answer text -> Gnani Timbre"
    return s
