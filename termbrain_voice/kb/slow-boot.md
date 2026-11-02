---
id: slow-boot
topics: boot
title: Slow boot
---
`systemd-analyze` prints total boot time split into firmware, loader, kernel and userspace. `systemd-analyze blame` lists units by time taken; `systemd-analyze critical-chain` shows what actually blocked boot.
Common culprits: `NetworkManager-wait-online.service` (safe to disable on a laptop with `sudo systemctl disable NetworkManager-wait-online.service`), a swap or fstab entry pointing at a missing UUID (look for "Timed out waiting for device" in `journalctl -b -p err`), and long firmware times, which Linux cannot fix.
