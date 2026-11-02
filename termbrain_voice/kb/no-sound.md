---
id: no-sound
topics: audio
title: No sound or wrong output device (PipeWire)
---
Manjaro KDE uses PipeWire with WirePlumber. Check the services: `systemctl --user is-active pipewire pipewire-pulse wireplumber` should print "active" three times.
`pactl info` should show "Server Name: PulseAudio (on PipeWire ...)". `wpctl status` lists sinks; the default one has an asterisk.
Restart the audio stack without logging out: `systemctl --user restart pipewire pipewire-pulse wireplumber`.
If `aplay -l` shows no cards, the kernel driver did not load; check `journalctl -b -k | grep -i -E "snd|sof|hda"`. Many recent Intel laptops need the `sof-firmware` package.
In KDE, the output device can be chosen in System Settings > Sound or from the volume applet.
