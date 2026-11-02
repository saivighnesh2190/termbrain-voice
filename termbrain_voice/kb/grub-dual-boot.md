---
id: grub-dual-boot
topics: boot packages
title: GRUB after updates on a Windows dual-boot
---
GRUB updates may leave /etc/default/grub.pacnew. Keep your own file and copy in new options only; make sure it contains `GRUB_DISABLE_OS_PROBER=false` or Windows disappears from the menu.
On Manjaro, after a GRUB package update run `sudo install-grub` and then `sudo update-grub` before rebooting. Verify with `grep -E "^menuentry" /boot/grub/grub.cfg`.
If GRUB is broken, boot a Manjaro live USB, run `sudo manjaro-chroot -a`, then `install-grub` and `update-grub` inside the chroot. Windows can still be started from the firmware boot menu (Windows Boot Manager).
