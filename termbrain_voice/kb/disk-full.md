---
id: disk-full
topics: disk
title: Disk or root partition full
---
`df -h` shows usage per filesystem; above about 90% on / causes failed updates and odd app behaviour.
Safe cleanups: the pacman cache (`paccache -rk2` keeps the last two versions of each package, from pacman-contrib), the journal (`sudo journalctl --vacuum-size=200M`), orphan packages (`pacman -Qdtq` lists them; review before removing), and old Timeshift snapshots (`sudo timeshift --list`, then delete old ones from the Timeshift app).
Find big folders in your home with `du -h --max-depth=1 ~ | sort -h`. Ollama models live in ~/.ollama or /usr/share/ollama and are often several GB each.
