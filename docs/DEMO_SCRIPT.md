# Demo video script: 60-second cut

The submission video for the Gnani challenge. Target length **0:58**, so it stays under a minute after export. One idea only: you speak Telugu-English to your laptop, it finds the real cause from local logs and answers out loud, and your logs never leave the machine.

The longer walkthrough is in [DEMO_SCRIPT_FULL.md](DEMO_SCRIPT_FULL.md).

## Setup (not recorded)

```bash
source .env
termbrain-voice check                       # all four rows green
termbrain-voice ask --text "hello" --no-speak   # warm the local model so the first real call is faster
rfkill block wifi                           # the staged problem; stay online via USB tether or Ethernet so Gnani is reachable
clear
```

- Terminal font 18 pt or bigger, dark theme, KDE tray visible (the WiFi icon is the payoff).
- Record screen and mic together in OBS at 1080p. Capture desktop audio too, so Timbre's voice is in the video.
- Record one full, uncut take first. You'll trim it to 60 seconds in the edit.

## The cut

| Time | On screen | Audio |
| --- | --- | --- |
| 0:00 to 0:05 | Terminal. Caption: **"My Linux laptop, in my language."** | You: "Linux problem వస్తే, logs చదవక్కర్లేదు. Just చెప్పండి." |
| 0:05 to 0:13 | Type `termbrain-voice ask`, speak, press Enter. | You, naturally code-mixed: **"నా WiFi పని చేయడం లేదు, networks కూడా కనిపించడం లేదు."** |
| 0:13 to 0:20 | *Heard* panel shows your Telugu with "WiFi" and "networks" kept in English. Caption: **"Gnani Prisma v3.0, code-mix mode"**. Then the *Topics* line. | You: "Prisma got my Telugu and English, both. Now it reads my laptop's logs, locally." |
| 0:20 to 0:22 | **Jump cut** over the local model's thinking time. Caption: **"⏩ local Gemma on CPU, x s"** (put your real number). | None. |
| 0:22 to 0:35 | Answer panel; the cause line says WiFi is soft-blocked. Caption: **"Gnani Timbre v3.0"**. | **Timbre speaks the answer.** Don't talk over it. |
| 0:35 to 0:43 | Type `rfkill unblock wifi`. Networks reappear in the KDE tray. | You: "Real cause, real fix. And it never runs commands by itself." |
| 0:43 to 0:52 | The last two lines of output (what went to the cloud). Optional 2-second flash of `termbrain-voice evidence` showing `[MAC]` and `[SSID]` redactions. | You: "Only my voice and this one-line answer touched the cloud. My logs stayed on this laptop." |
| 0:52 to 0:58 | End card: **TermBrain Voice** · Gnani Prisma + Timbre · local Ollama · github.com/saivighnesh2190/termbrain-voice · #GnaniAI #GreatIndianAIInternshipChallenge | You: "TermBrain Voice. Built with Gnani. Thanks!" |

## Subtitles

Burn in English subtitles for every Telugu line so any judge can follow:

- "Linux problem వస్తే, logs చదవక్కర్లేదు. Just చెప్పండి." → "Got a Linux problem? No need to read logs. Just say it."
- "నా WiFi పని చేయడం లేదు, networks కూడా కనిపించడం లేదు." → "My WiFi isn't working, I can't even see networks."
- Subtitle Timbre's answer with the text the answer panel shows.

## Editing in Kdenlive (about 15 minutes)

1. `sudo pacman -S kdenlive` if it isn't installed.
2. Import the full take. Cut the local model's wait down to about 2 seconds and add the "⏩" caption with the real seconds, so the speed-up is disclosed, not hidden.
3. Trim pauses before and after each line. If it's still over 0:58, shorten the 0:43 privacy shot first; never cut the Telugu question or Timbre's answer.
4. Add the captions and end card, then export H.264 MP4, 1080p, 30 fps. Check the final duration is under 1:00.

## If something goes wrong on the take

- Prisma mishears a word: re-record just that line; keep the code-mixed phrasing, since that's the point of the video.
- Timbre's answer runs past 13 seconds: keep it whole and shorten the privacy shot instead.
- No second network for the WiFi scene: use the muted-speaker backup scene from [DEMO_SCRIPT_FULL.md](DEMO_SCRIPT_FULL.md) and keep the same timings.
