"""termbrain-voice command line."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Optional

import requests
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from . import __version__
from . import evidence as ev
from .audio import duration_seconds, play, record
from .config import SUPPORTED_LANGS, Settings
from .gnani import GnaniClient, GnaniError, OfflineGnani
from .pipeline import Session, run
from .redact import redact
from .router import route

app = typer.Typer(add_completion=False, help="Talk to your Linux box. Prisma hears, a local LLM thinks, Timbre answers.")
console = Console()

BADGE = {"read-only": "[green]read-only[/]", "changes system": "[yellow]review first[/]", "info": "[dim]info[/]"}


def _speech(settings: Settings, offline: bool, transcript_hint: str = "", lang: str = "en-IN"):
    if offline or settings.offline:
        return OfflineGnani(transcript_hint, lang)
    return GnaniClient(settings)


def _on_stage(stage: str, s: Session) -> None:
    if stage == "heard":
        lang = SUPPORTED_LANGS.get(s.language, s.language)
        t = f" · {s.timings['stt']}s" if "stt" in s.timings else ""
        console.print(Panel(s.transcript, title=f"🎙  Heard ({lang}{t})", border_style="cyan"))
    elif stage == "evidence":
        names = ", ".join(e["label"] for e in s.evidence)
        console.print(f"[bold]🔎 Topics:[/] {', '.join(s.topics)}   [dim]read {len(s.evidence)} sources locally "
                      f"in {s.timings.get('evidence', 0)}s: {names}[/]")
        console.print("[bold yellow]🧠 Thinking locally…[/]")
    elif stage == "answer":
        a = s.answer
        console.print(Panel(a["spoken_answer"] or "(no spoken answer)",
                            title=f"🔊 Answer ({SUPPORTED_LANGS.get(s.reply_language)} · confidence {a['confidence']}"
                                  f" · {s.timings.get('llm', 0)}s)", border_style="green"))
        if a["diagnosis"]:
            console.print(Markdown(a["diagnosis"]))
        if s.steps:
            table = Table(title="Next steps (nothing runs unless you run it)", show_lines=False)
            table.add_column("#", style="dim", width=3)
            table.add_column("Command", style="bold")
            table.add_column("Why")
            table.add_column("Safety")
            for i, st in enumerate(s.steps, 1):
                table.add_row(str(i), st["command"] or "-", st["why"], BADGE.get(st["safety"], st["safety"]))
            console.print(table)
        if s.blocked_steps:
            console.print(f"[red]⛔ Withheld {len(s.blocked_steps)} destructive suggestion(s) from the model.[/]")
        if a["sources"]:
            console.print(f"[dim]Runbooks cited: {', '.join(a['sources'])}[/]")


@app.command()
def ask(
    audio: Optional[Path] = typer.Option(None, "--audio", "-a", help="Use a recorded clip (≤30 s) instead of the mic."),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Skip speech-to-text and type the problem."),
    text_lang: str = typer.Option("en-IN", "--text-lang", help="Language of --text, e.g. te-IN."),
    reply_lang: Optional[str] = typer.Option(None, "--reply-lang", help="Force reply language, e.g. en-IN."),
    voice: Optional[str] = typer.Option(None, "--voice", help="Timbre voice, e.g. Shivani, Kalpana, Avinash."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Ollama model (default gemma3:4b)."),
    no_speak: bool = typer.Option(False, "--no-speak", help="Print the answer without Timbre audio."),
    offline: bool = typer.Option(False, "--offline", help="No Gnani calls (testing). Needs --text or a .txt sidecar."),
    as_json: bool = typer.Option(False, "--json", help="Print the full session as JSON."),
):
    """Describe a problem out loud (Telugu, English or a mix) and hear the fix."""
    settings = Settings()
    if voice:
        settings.tts_voice = voice
    if model:
        settings.ollama_model = model
    try:
        speech = _speech(settings, offline, text or "", text_lang)
        if text is None and audio is None:
            clip = settings.data_dir / "audio" / time.strftime("ask-%Y%m%d-%H%M%S.wav")
            console.print(f"[bold cyan]🎙  Listening… press Enter when done (max {settings.max_record_seconds}s).[/]")
            audio = record(clip, settings.max_record_seconds)
            console.print(f"[dim]Recorded {duration_seconds(audio):.1f}s[/]")
        session = run(
            settings, speech, audio_path=audio, text=text, text_language=text_lang,
            reply_language=reply_lang, speak=not no_speak, on_stage=(lambda *_: None) if as_json else _on_stage,
        )
    except GnaniError as e:
        console.print(f"[red]Gnani error:[/] {e}")
        raise typer.Exit(2) from e
    except (RuntimeError, ValueError) as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1) from e
    path = session.save(settings.data_dir)
    if as_json:
        console.print_json(json.dumps(session.__dict__, ensure_ascii=False))
    else:
        timing = "  ".join(f"{k} {v}s" for k, v in session.timings.items())
        console.print(f"[dim]⏱  {timing}   ·   session saved to {path}[/]")
        console.print(f"[dim]☁️  Sent to cloud: {'; '.join(session.sent_to_cloud.values()) or 'nothing'}. "
                      "Logs and evidence stayed on this machine.[/]")
    if session.spoken_audio and not as_json:
        if not play(Path(session.spoken_audio)):
            console.print(f"[yellow]No audio player found; reply saved at {session.spoken_audio}[/]")


@app.command()
def say(text: str, lang: str = typer.Option("te-IN", "--lang"), voice: Optional[str] = typer.Option(None, "--voice")):
    """Speak any text with Gnani Timbre (quick TTS test)."""
    settings = Settings()
    if voice:
        settings.tts_voice = voice
    try:
        out = GnaniClient(settings).synthesize(text, lang, settings.data_dir / "audio" / "say.wav")
    except GnaniError as e:
        console.print(f"[red]Gnani error:[/] {e}")
        raise typer.Exit(2) from e
    console.print(f"[green]Saved {out}[/]")
    play(out)


@app.command()
def evidence(problem: str = typer.Argument(..., help="Words describing the problem, e.g. 'wifi not working'.")):
    """Show exactly what would be read from this machine for a problem (privacy check)."""
    topics = route(problem)
    console.print(f"[bold]Topics:[/] {', '.join(topics)}")
    for item in ev.collect(topics):
        console.print(Panel(redact(item.output), title=f"{item.label}  [dim]$ {item.command}[/]", expand=False))


@app.command()
def check():
    """Preflight: API key, Ollama model, microphone and speaker tools."""
    s = Settings()
    rows = []
    rows.append(("GNANI_API_KEY", bool(s.gnani_api_key), "set" if s.gnani_api_key else "export GNANI_API_KEY=..."))
    try:
        tags = requests.get(s.ollama_host.rstrip("/") + "/api/tags", timeout=3).json().get("models", [])
        names = [m.get("name", "") for m in tags]
        has = any(n == s.ollama_model or n.startswith(s.ollama_model + ":") for n in names)
        rows.append(("Ollama running", True, s.ollama_host))
        rows.append((f"Model {s.ollama_model}", has, "pulled" if has else f"ollama pull {s.ollama_model}"))
    except requests.RequestException:
        rows.append(("Ollama running", False, "start it: systemctl start ollama (or ollama serve)"))
    rec = shutil.which("pw-record") or shutil.which("arecord")
    rows.append(("Recorder", bool(rec), rec or "install pipewire or alsa-utils"))
    ply = shutil.which("pw-play") or shutil.which("paplay") or shutil.which("aplay")
    rows.append(("Player", bool(ply), ply or "install pipewire or alsa-utils"))
    table = Table(title=f"TermBrain Voice {__version__} preflight")
    table.add_column("Check")
    table.add_column("OK")
    table.add_column("Detail")
    for name, ok, detail in rows:
        table.add_row(name, "✅" if ok else "❌", detail)
    console.print(table)
    if not all(ok for _, ok, _ in rows):
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
