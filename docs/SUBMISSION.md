# Submission write-up: TermBrain Voice

**Team:** Nekkanti Sai Vighnesh (B.Tech CSE, KL University)
**Repo:** https://github.com/saivighnesh2190/termbrain-voice
**Gnani models:** Prisma v3.0 (speech-to-text), Timbre v3.0 (text-to-speech)
**Award category:** Mixed Vibes Award (best code-mixed voice build)
**Demo video:** 60 seconds (script: `docs/DEMO_SCRIPT.md`)

## Problem

Linux troubleshooting assumes you can read raw logs and describe the problem in English. Students and first-time users in India often can't, and the usual workaround, pasting private system logs into a cloud chatbot, leaks MAC addresses, network names and usernames.

## Solution

A voice-first assistant for the Linux terminal. You describe the problem in Telugu, English or a mix. Gnani Prisma transcribes it; the app reads the relevant read-only evidence from the machine, redacts identifiers, retrieves matching runbooks, reasons with a local LLM, and Gnani Timbre speaks a short, grounded answer back in your language. Suggested commands are labelled for safety and never executed.

## How Gnani's models are used

- **Prisma v3.0** via `POST /stt/v3`: `language_code=te-IN,en-IN` as hints, `format=codemix` so many English tech terms stay in Latin script inside Telugu speech (others come back transliterated, and the router handles both), `keyterms` with 37 Linux terms and a `topic` sentence to bias recognition of words like pacman, GRUB and PipeWire. `detected_language_code` decides the reply language.
- **Timbre v3.0** via `POST /api/v1/tts/inference`: every v3.0 voice speaks all ten languages, so one voice (default Shivani) answers in whatever language the user spoke.
- Client handles every documented error shape (STT envelope, auth/rate-limit `detail`, 422 validation, 504 upstream timeout) and backs off on the one-active-request 429.

## Award category: Mixed Vibes

Each entry can win at most one award, so this entry is nominated for **Mixed Vibes**, the award for the best code-mixed voice build. Code-mixing isn't a feature added on top here; the whole product rests on it:

- Users describe problems the way Telugu speakers actually talk about computers: Telugu sentences full of English tech words ("నా WiFi పని చేయడం లేదు", "Laptop చాలా slow గా ఉంది").
- Prisma runs in `format=codemix` with Telugu and English hints, so many English terms stay in Latin script inside Telugu speech; the router also matches the Telugu-script forms Prisma sometimes returns (వైఫై, బూట్), and Linux keyterms (pacman, GRUB, PipeWire) are biased in.
- The router is built and evaluated on code-mixed speech: 26 of its 35 evaluation cases are Telugu-English code-mixed, including 4 real Prisma v3.0 transcripts.
- The reply follows the user's language, and Timbre speaks it in the same voice whether the answer is Telugu, English or mixed.

The 60-second demo is built around one code-mixed request and its spoken answer, so it is also suitable for the Demo Day Drop award if the judges prefer to consider it there.

## Model details (local)

- Reasoning: Ollama, default `gemma3:4b`, JSON mode, temperature 0.2, 8k context. Configurable.
- Retrieval: BM25 over 12 curated Manjaro runbooks, with the router's topic as a prior and error lines from evidence added to the query.
- Router: deterministic Telugu and English keyword matcher (35/35 top-1 on a 35-case development set).

## Privacy and safety

Only the audio clip and the final 1 to 3 sentence answer go to Gnani. Logs stay local and are redacted (MAC, IPv4/IPv6, UUID, email, SSID, hostname, username) even before the local model sees them, so screen recordings and saved sessions are safe to share. A command classifier labels suggestions read-only or review-first and withholds destructive ones.

## Results

- 52 automated tests, ruff-clean, CI on Python 3.10 and 3.13.
- Router eval: 35/35 (26 Telugu code-mixed incl. 4 live Prisma transcripts, 9 English), development set.
- The safety guard caught a real problem during live testing: a small local model suggested a partial upgrade (`pacman -Sy <pkg>`), which is now withheld.
- Per-stage latency (STT, evidence, LLM, TTS) printed every run and saved per session. Measured live on 2026-11-07: Prisma 0.5 to 1.2 s per clip, evidence 0.02 s, Timbre 1.4 to 4.2 s depending on answer length. Local LLM: LLM_SECONDS s for gemma3:4b on an i7 U-series CPU (fill in from your run).

## What's next

Streaming Prisma over WebSocket for longer, interruptible conversations; multi-turn follow-ups; optional Evon for Telugu phrasing when the user opts in.

---

## LinkedIn / X post (draft)

I built TermBrain Voice for Gnani AI's Great Indian AI Internship Challenge 🎙️🐧

Tell your Linux laptop what's wrong in Telugu, English or the Telugu-English mix we actually speak, and it tells you the fix out loud.

How it works:
• Gnani Prisma v3.0 turns my code-mixed Telugu into text (codemix mode plus Linux keyterm hints)
• The app reads only the relevant logs on my machine, read-only, and redacts MACs, IPs and WiFi names
• A local Gemma model on Ollama reasons over that evidence plus curated Manjaro runbooks
• Gnani Timbre v3.0 speaks the answer back in my language

My logs never leave the laptop. Only the voice clip and the one-line answer touch the cloud.

52 tests, a Telugu/English router eval and CI on every push.

60-second demo in this post. Code: https://github.com/saivighnesh2190/termbrain-voice

@Gnani AI #GnaniAI #GreatIndianAIInternshipChallenge #GreatIndianAIInterns #VoiceAI #IndicAI #Linux #LocalLLM

*Attach the 60-second video to the post itself (LinkedIn and X both), tag Gnani AI's official account, and nominate one post per platform in the submission form.*
