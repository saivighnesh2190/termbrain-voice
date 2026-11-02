# Submission write-up: TermBrain Voice

**Team:** Nekkanti Sai Vighnesh (B.Tech CSE, KL University)
**Repo:** https://github.com/saivighnesh2190/termbrain-voice
**Gnani models:** Prisma v3.0 (speech-to-text), Timbre v3.0 (text-to-speech)

## Problem

Linux troubleshooting assumes you can read raw logs and describe the problem in English. Students and first-time users in India often can't, and the usual workaround, pasting private system logs into a cloud chatbot, leaks MAC addresses, network names and usernames.

## Solution

A voice-first assistant for the Linux terminal. You describe the problem in Telugu, English or a mix. Gnani Prisma transcribes it; the app reads the relevant read-only evidence from the machine, redacts identifiers, retrieves matching runbooks, reasons with a local LLM, and Gnani Timbre speaks a short, grounded answer back in your language. Suggested commands are labelled for safety and never executed.

## How Gnani's models are used

- **Prisma v3.0** via `POST /stt/v3`: `language_code=te-IN,en-IN` as hints, `format=codemix` so English tech terms stay in Latin script inside Telugu speech, `keyterms` with 37 Linux terms and a `topic` sentence to bias recognition of words like pacman, GRUB and PipeWire. `detected_language_code` decides the reply language.
- **Timbre v3.0** via `POST /api/v1/tts/inference`: every v3.0 voice speaks all ten languages, so one voice (default Shivani) answers in whatever language the user spoke.
- Client handles every documented error shape (STT envelope, auth/rate-limit `detail`, 422 validation, 504 upstream timeout) and backs off on the one-active-request 429.

## Model details (local)

- Reasoning: Ollama, default `gemma3:4b`, JSON mode, temperature 0.2, 8k context. Configurable.
- Retrieval: BM25 over 12 curated Manjaro runbooks, with the router's topic as a prior and error lines from evidence added to the query.
- Router: deterministic Telugu and English keyword matcher (31/31 top-1 on a 31-case development set).

## Privacy and safety

Only the audio clip and the final 1 to 3 sentence answer go to Gnani. Logs stay local and are redacted (MAC, IPv4/IPv6, UUID, email, SSID, hostname, username) even before the local model sees them, so screen recordings and saved sessions are safe to share. A command classifier labels suggestions read-only or review-first and withholds destructive ones.

## Results

- 50 automated tests, ruff-clean, CI on Python 3.10 and 3.13.
- Router eval: 31/31 (22 Telugu code-mixed, 9 English), development set.
- Per-stage latency (STT, evidence, LLM, TTS) printed every run and saved per session. *(Fill in your measured numbers after recording: e.g. STT 0.x s, evidence 0.x s, LLM x s on i7 U-series CPU, TTS 0.x s.)*

## What's next

Streaming Prisma over WebSocket for longer, interruptible conversations; multi-turn follow-ups; optional Evon for Telugu phrasing when the user opts in.

---

## LinkedIn / X post (draft)

I built TermBrain Voice for the #GnaniAI Great Indian AI Internship Challenge 🎙️🐧

Tell your Linux laptop what's wrong in Telugu, English or both, and it tells you the fix out loud.

How it works:
• Gnani Prisma v3.0 turns my code-mixed Telugu into text (codemix mode + Linux keyterms, so "pacman" stays pacman)
• The app reads only the relevant logs on my machine, read-only, and redacts MACs, IPs and WiFi names
• A local Gemma model on Ollama reasons over that evidence plus curated Manjaro runbooks
• Gnani Timbre v3.0 speaks the answer back in my language

My logs never leave the laptop. Only the voice clip and the one-line answer touch the cloud.

50 tests, a Telugu/English router eval and CI on every push.

Demo + code: https://github.com/saivighnesh2190/termbrain-voice

@Gnani.ai #VoiceAI #IndicAI #Linux #LocalLLM #RAG
