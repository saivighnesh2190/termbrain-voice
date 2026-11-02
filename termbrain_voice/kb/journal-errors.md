---
id: journal-errors
topics: general boot
title: Reading errors in the system journal
---
`journalctl -b -p err` shows errors from the current boot; `journalctl -b -1 -p err` shows the previous boot, useful after a crash.
`systemctl --failed` lists units that failed to start; `systemctl status <unit>` explains why.
Many journal errors are harmless noise (ACPI warnings, Bluetooth firmware messages). Focus on errors that line up with when the problem happened, and on failed units.
