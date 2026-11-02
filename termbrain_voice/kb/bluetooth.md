---
id: bluetooth
topics: bluetooth
title: Bluetooth will not turn on or pair
---
The service must be running: `systemctl is-active bluetooth`; enable it with `sudo systemctl enable --now bluetooth`.
`rfkill list bluetooth` shows soft or hard blocks; clear a soft block with `rfkill unblock bluetooth`.
`bluetoothctl show` should say "Powered: yes". Power it on with `bluetoothctl power on`.
For audio devices, PipeWire handles Bluetooth audio through WirePlumber; if pairing works but there is no sound, restart the audio stack: `systemctl --user restart wireplumber`.
