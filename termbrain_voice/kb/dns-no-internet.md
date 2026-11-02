---
id: dns-no-internet
topics: network
title: Connected to WiFi but no internet
---
Separate connectivity from name resolution: `ping -c 3 1.1.1.1` tests raw connectivity, `ping -c 3 archlinux.org` tests DNS too. If the IP ping works but the name fails, DNS is the problem.
`resolvectl status` (systemd-resolved) or `cat /etc/resolv.conf` shows which DNS servers are in use.
Captive portals (college or hostel WiFi) need a browser login first; open http://neverssl.com to trigger the portal page.
Reconnecting resets DHCP and DNS: `nmcli connection down "<name>" && nmcli connection up "<name>"`.
