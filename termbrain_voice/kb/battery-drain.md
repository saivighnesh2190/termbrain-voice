---
id: battery-drain
topics: power
title: Battery drains fast or not charging
---
Battery state is in `/sys/class/power_supply/BAT*/status` and `capacity`. "Not charging" at a high percentage can be a charge limit set in firmware or vendor tools, which is normal.
`powerprofilesctl get` shows the active profile; switch with `powerprofilesctl set power-saver`.
Heavy background processes (see `ps -eo pid,comm,%cpu --sort=-%cpu | head`) and high screen brightness are the usual causes of fast drain.
