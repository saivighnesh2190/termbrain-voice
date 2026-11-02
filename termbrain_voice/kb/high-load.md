---
id: high-load
topics: performance
title: Laptop slow, hanging or hot
---
Compare the load average in `/proc/loadavg` with the CPU core count from `nproc`: load consistently above the core count means the CPU is saturated.
`ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head` shows the heaviest processes. baloo_file (KDE file indexing) and a local LLM running in Ollama are common heavy users on KDE laptops.
`free -h`: low "available" memory with heavy swap use causes freezes; close large apps or pick a smaller quantised model. Linux uses free RAM for cache, so low "free" alone is normal.
Pause KDE file indexing with `balooctl6 suspend` (or `balooctl suspend` on older Plasma).
