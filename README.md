# TermBrain Voice 🎙️🐧

**Tell your Linux laptop what's wrong, in Telugu, English, or both. It reads its own logs and tells you the fix out loud.**

Built for the **Gnani.ai Great Indian AI Internship Challenge 2026** on top of [TermBrain](https://github.com/saivighnesh2190/termbrain), my privacy-first Linux diagnostic CLI.

```
$ termbrain-voice ask
🎙  Listening… press Enter when done
╭─ 🎙 Heard (Telugu · 0.7s) ───────────────────────────────╮
│ నా WiFi పని చేయడం లేదు, networks కూడా కనిపించడం లేదు      │
╰──────────────────────────────────────────────────────────╯
🔎 Topics: network   read 7 sources locally in 0.4s
🧠 Thinking locally…
╭─ 🔊 Answer (Telugu · confidence high) ───────────────────╮
│ మీ WiFi software లో off అయి ఉంది. rfkill తో unblock చేస్తే │
│ networks మళ్ళీ కనిపిస్తాయి.                                │
╰──────────────────────────────────────────────────────────╯
 #  Command               Why                    Safety
 1  rfkill list           confirm the block      read-only
 2  rfkill unblock wifi   turn the radio on      review first
☁️  Sent to cloud: audio clip → Gnani Prisma; 96 chars of answer text → Gnani Timbre.
    Logs and evidence stayed on this machine.
```
*(Illustrative output: the exact wording depends on your machine and model.)*

## Why this exists

Linux help today assumes you can read `journalctl` and you think in English. Millions of Indian students and first-time Linux users can't, or don't want to, type a long English description of a problem, and they shouldn't have to paste private system logs into a cloud chatbot to get help.

TermBrain Voice splits the job so each part runs where it belongs:

| Stage | Where it runs | What leaves your machine |
|---|---|---|
| Hear: speech to text | **Gnani Prisma v3.0** (cloud) | the ≤30 s audio clip only |
| Route + collect evidence | local, read-only commands | nothing |
| Redact (MACs, IPs, SSIDs, hostname, user) | local | nothing |
| Retrieve runbooks (BM25 RAG) | local | nothing |
| Reason | **local Ollama** model | nothing |
| Safety guard | local | nothing |
| Speak: text to speech | **Gnani Timbre v3.0** (cloud) | the 1 to 3 sentence answer only |

Your logs never leave the laptop. Every session records exactly what was sent where (`sent_to_cloud` in the saved session JSON).

## How it works

```
 mic ─► pw-record ─► Gnani Prisma v3.0 ─► router ─► read-only collectors ─► redact
        (16 kHz)     codemix + keyterms   (te/en)   journalctl, nmcli, ...      │
                                                                               ▼
 speaker ◄─ pw-play ◄─ Gnani Timbre v3.0 ◄─ safety guard ◄─ Ollama (local) ◄─ BM25 runbooks
                       (reply language                       JSON mode,        (12 curated
                        = your language)                     cites runbooks)    Manjaro fixes)
```

Design choices worth noting:

- **Prisma `codemix` + keyterm prompting.** Indian users say "నా WiFi పని చేయడం లేదు", not pure Telugu. `codemix` keeps many English tech words in Latin script, but not all: in live tests Prisma wrote "sound", "speakers" and "disk" in Latin and transliterated "WiFi", "laptop" and "boot" into Telugu script (వైఫై, ల్యాప్‌టాప్, బూట్). The router therefore matches both spellings, and real Prisma transcripts are part of the eval. A list of 37 Linux keyterms (pacman, GRUB, PipeWire, journalctl…) is sent with each clip so Prisma doesn't hear "Pac-Man". Hint languages default to `te-IN,en-IN` and are hints, not a lock.
- **Deterministic router, not an LLM.** Mapping speech to evidence with keywords in Telugu and English is instant on a CPU-only laptop, can't invent a command, and is measurable (see Evaluation).
- **Read-only evidence with fixed argv.** No shell, no user text in commands, 8 s timeouts, graceful "not installed" when a tool is missing.
- **Grounded answers.** The local model gets real command output plus the top 3 runbooks, must answer in JSON and cite runbook ids. Invented citations are dropped.
- **Safety guard.** Suggested commands are never executed. Each is labelled `read-only` or `review first`; destructive ones (`rm -rf`, `dd of=`, `mkfs`, `pacman -Rdd`, `curl | sh`, `find -delete`…) are withheld and counted.
- **Reply in your language.** Timbre v3.0 voices speak all 10 supported languages, so the answer comes back in the language Prisma detected (`--reply-lang` overrides).

## Quick start (Manjaro / Arch)

```bash
# 1. Local model (CPU-friendly, multilingual)
sudo pacman -S --needed ollama python-pipx
sudo systemctl enable --now ollama
ollama pull gemma3:4b

# 2. Install
git clone https://github.com/saivighnesh2190/termbrain-voice.git
cd termbrain-voice
pipx install -e .          # or: python -m venv .venv && . .venv/bin/activate && pip install -e .

# 3. Gnani key from https://app.gnani.ai
cp .env.example .env && nano .env && source .env

# 4. Preflight, then talk
termbrain-voice check
termbrain-voice ask
```

### Commands

| Command | What it does |
|---|---|
| `termbrain-voice ask` | Record from the mic (Enter to stop), diagnose, speak the answer |
| `termbrain-voice ask --audio clip.wav` | Use a recorded clip (≤30 s, WAV/MP3/OGG/FLAC/M4A) |
| `termbrain-voice ask --text "no space left" ` | Skip speech-to-text |
| `termbrain-voice ask --reply-lang en-IN --voice Avinash` | Force reply language / Timbre voice |
| `termbrain-voice evidence "wifi not working"` | Show exactly what would be read from your machine (privacy check) |
| `termbrain-voice say "నమస్తే" --lang te-IN` | Quick Timbre test |
| `termbrain-voice check` | Verify API key, Ollama + model, mic and speaker tools |

Config via environment: `GNANI_API_KEY`, `TBV_OLLAMA_MODEL` (default `gemma3:4b`), `TBV_TTS_VOICE` (default `Shivani`), `TBV_STT_LANGS` (default `te-IN,en-IN`), `TBV_STT_FORMAT` (default `codemix`), `OLLAMA_HOST`.

**Model choice.** `gemma3:4b` is the default: Gemma 3 is trained for multilingual use and the 4B model still fits a 16 GB CPU-only laptop. (A side-by-side Telugu comparison with other small models hasn't been run yet.) `gemma3:1b` works too but gives weaker, more repetitive Telugu answers.

**Behind a proxy?** The client talks to a local Ollama directly and ignores `HTTP(S)_PROXY` for localhost, so campus or corporate proxies don't break it. If Telugu replies are weak on your hardware, use `--reply-lang en-IN` with any smaller model.

## Evaluation

```bash
pytest -q                       # 52 tests: Gnani request/response shapes, router, redaction, safety, RAG, pipeline
python evals/run_router_eval.py # router top-1 accuracy on Telugu/English/code-mixed problem statements
```

Router: **35/35 top-1** on `evals/router_cases.jsonl` (26 Telugu code-mixed, 9 English). 31 cases were written to mirror Prisma `codemix` output, and 4 are real Prisma v3.0 transcripts captured on 2026-11-07. This is a development set: one miss on the first run ("freezes") was fixed by adding verb inflections, so treat it as a regression test rather than a held-out score. CI runs tests, lint and the eval on Python 3.10 and 3.13.

Not covered by CI: live Gnani calls and live Ollama generation (they need a key and a model). Both were run end to end on 2026-11-07: Timbre-generated Telugu clips went through `ask --audio`, then Prisma, evidence, Ollama and Timbre. The test audio was synthetic Timbre speech, not a human voice. Measured Gnani latency from a cloud sandbox in India: Prisma 0.5 to 1.2 s per clip, Timbre 1.4 to 4.2 s depending on answer length. Local model time depends on your CPU. The Gnani client is tested against the documented request fields and every documented error shape, including the 429 one-active-request limit with backoff.

## Project structure

```
termbrain_voice/
  cli.py        Typer commands and Rich output
  pipeline.py   hear → route → collect → redact → retrieve → reason → guard → speak
  gnani.py      Prisma v3.0 STT + Timbre v3.0 TTS client, error normalisation, retries
  router.py     Telugu/English keyword router
  evidence.py   read-only collectors (journalctl, nmcli, rfkill, pactl, systemd-analyze, df, pacman.log…)
  redact.py     MAC / IP / UUID / email / SSID / hostname / username scrubbing
  kb.py + kb/   BM25 retriever over 12 curated Manjaro runbooks
  llm.py        Ollama JSON-mode prompt, robust parsing, speakable text
  safety.py     command classifier: read-only / review first / withheld
evals/          router eval set and runner
tests/          pytest suite (no network)
```

## Limits and next steps

- REST STT caps a clip at 30 s; streaming via Prisma's WebSocket endpoint would allow longer, interruptible conversations.
- Evidence collectors target Manjaro/Arch with systemd and NetworkManager; other distros degrade gracefully.
- Next: follow-up questions in the same session, Gnani's Pipecat plugin for barge-in, and optionally Gnani's Evon (an Indic LLM) for Telugu phrasing when the user opts in.

## Docs

- [Demo video script, 60-second cut](docs/DEMO_SCRIPT.md) ([full 2.5-minute walkthrough](docs/DEMO_SCRIPT_FULL.md))
- [Challenge write-up and post draft](docs/SUBMISSION.md)

## License

MIT. Gnani, Prisma, Timbre and Evon are trademarks of Gnani.ai.
