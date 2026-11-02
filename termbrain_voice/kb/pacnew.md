---
id: pacnew
topics: packages
title: Unmerged .pacnew files
---
A .pacnew file means pacman did not overwrite a config you had changed. List them with `pacdiff -o` (from pacman-contrib) or `find /etc -name "*.pacnew"`.
Compare with `diff -u /etc/file /etc/file.pacnew`, merge what you need into your file, then delete the .pacnew. Never overwrite blindly files that hold your own settings, such as /etc/default/grub, /etc/fstab or /etc/mkinitcpio.conf.
