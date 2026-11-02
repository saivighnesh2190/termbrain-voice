# Demo video script (about 2 minutes 30 seconds)

Record with OBS or KDE's Spectacle screen recorder (1080p, terminal font 16 pt or bigger, mic audio plus desktop audio so Timbre's voice is captured).

## Before you hit record

```bash
source .env
termbrain-voice check                 # all four rows green
rfkill block wifi                     # staged problem for scene 2 (switch to phone hotspot over USB or Ethernet so Gnani is reachable)
clear
```

Scene 2 needs internet for Gnani while WiFi looks "broken". Options: USB-tether your phone, or use Ethernet. If neither is handy, use the `pactl` mute scene below instead.

---

## Scene 1: the hook (0:00 to 0:15)

**On screen:** terminal, big font. Your face cam in a corner if you like.

**Say (Telugu-English, natural):**
> "Linux లో problem వస్తే మనం journalctl logs చదివి, English లో Google చేయాలి. అదే laptop కి మన భాషలో చెప్తే? This is TermBrain Voice."

## Scene 2: Telugu problem, Telugu answer (0:15 to 1:00)

**Type:** `termbrain-voice ask`

**Say into the mic, then press Enter:**
> "నా WiFi పని చేయడం లేదు, networks కూడా కనిపించడం లేదు."

**Point at, as each panel appears:**
1. "Gnani Prisma heard me, Telugu with English words, in under a second." (Heard panel)
2. "It picked the network topic and read seven things from my laptop: rfkill, NetworkManager, the journal. All locally." (Topics line)
3. Let Timbre speak the answer. Don't talk over it.
4. "It found the actual cause: WiFi is soft-blocked. It suggests a read-only check first, and marks the fix as review first. It never runs anything itself."

**Then run the fix live:** `rfkill unblock wifi` and show networks coming back in the KDE tray. This is the moment judges remember.

## Scene 3: privacy, proved (1:00 to 1:30)

**Point at the last two lines:**
> "Only two things went to the cloud: my voice clip to Prisma, and this one-line answer to Timbre. My logs, MAC address and network name never left the machine."

**Type:** `termbrain-voice evidence "wifi not working"`
> "And this shows exactly what it reads. MAC addresses, IPs and my WiFi name are redacted."

## Scene 4: English and code-mixed, plus the safety guard (1:30 to 2:05)

**Type:** `termbrain-voice ask --reply-lang en-IN`

**Say:**
> "Laptop చాలా slow గా ఉంది, fan full sound చేస్తోంది."

**Point at:** "It switched to performance evidence, load, memory and top processes, and answered in English because I asked it to. Same pipeline, any of Gnani's ten languages."

If the steps table ever shows "Withheld N destructive suggestion(s)", point at it: "If the model suggests something dangerous like rm -rf, the guard hides it."

## Scene 5: engineering close (2:05 to 2:30)

**Type:** `pytest -q && python evals/run_router_eval.py`
> "Fifty tests, a Telugu and English router eval, CI on every push. Gnani's Prisma and Timbre for voice, a local Gemma model for reasoning, RAG over curated Manjaro runbooks. Code's on GitHub. Thanks, Gnani!"

---

## Backup scene (no second network)

```bash
pactl set-sink-mute @DEFAULT_SINK@ 1    # stage it
termbrain-voice ask --no-speak          # you can't hear Timbre while muted, so read the panel
```
Say: "సౌండ్ రావడం లేదు, speakers నుంచి ఏమీ వినిపించడం లేదు." Then unmute with `pactl set-sink-mute @DEFAULT_SINK@ 0` and replay the saved reply with `pw-play` on the path shown, so the audience hears Timbre.

Note: a muted sink may not show in the evidence the model sees, so the answer may be "services are healthy, check the output device and volume". That is honest grounded behaviour; say so on camera.

## Recording tips

- Do one dry run first: first-call latency on Ollama is higher while the model loads. Run `termbrain-voice ask --text "hello" --no-speak` once before recording to warm it.
- Keep each clip under 30 seconds of speech (Prisma REST limit).
- If a take goes wrong, the session JSON in `~/.local/share/termbrain-voice/sessions/` has every timing for your write-up.
