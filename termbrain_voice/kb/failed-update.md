---
id: failed-update
topics: packages
title: Pacman update failed or was interrupted
---
Read the error before retrying: `grep -i -E "error|warning" /var/log/pacman.log | tail -n 30`.
"failed to retrieve some files" usually means stale mirrors: `sudo pacman-mirrors --fasttrack 5 && sudo pacman -Syyu`.
"invalid or corrupted package (PGP signature)" means outdated keyrings: `sudo pacman -Sy manjaro-keyring archlinux-keyring` and then update.
"unable to lock database" with no pacman running means a stale lock from an interrupted run; confirm nothing is running with `pgrep -a pacman`, then remove `/var/lib/pacman/db.lck`.
"breaks dependency ... required by X": a package was dropped from the repos; remove X first (check the stable update announcement), then update.
Take a Timeshift snapshot before big updates: `sudo timeshift --create --comments "before update"`.
