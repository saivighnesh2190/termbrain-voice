---
id: wifi-down
topics: network
title: WiFi not connecting or no networks listed
---
Check the radio first: `rfkill list` shows "Soft blocked: yes" when WiFi is switched off in software and "Hard blocked: yes" when a physical key or BIOS setting disables it. A soft block clears with `rfkill unblock wifi`.
Check NetworkManager state with `nmcli device` (look for the wifi device as "disconnected" or "unavailable") and `nmcli radio wifi` (should be "enabled"; turn on with `nmcli radio wifi on`).
If the device is missing entirely, the driver or firmware did not load: look at `journalctl -b -k | grep -i -E "firmware|wlan|iwlwifi|rtw|ath"`. After a kernel change, booting the previous kernel from GRUB Advanced options is a quick test.
Restarting the service is safe: `sudo systemctl restart NetworkManager`.
Dual-boot with Windows: Windows Fast Startup can leave the WiFi card in a bad state; disable Fast Startup in Windows power options.
