#!/usr/bin/env bash
# Idle baseline on STOCK JetPack (Ubuntu). Run on the Nano after it has been
# idle for about 5 minutes, with nothing else running.
# Usage: scripts/measure-stock.sh [outdir]       (default: ~/baseline)
# Output: <outdir>/baseline-idle.txt
#
# Notes:
# - Boot time: read the graphical.target line and the kernel + userspace parts.
#   The "Startup finished" total can be inflated by background jobs such as
#   apt-daily.service, so it is not used as the boot time.
# - RAM: use "available" from free -m (total minus available = in use).
set -u
OUT="${1:-$HOME/baseline}"
mkdir -p "$OUT"
F="$OUT/baseline-idle.txt"

{
echo "== date"; date
echo "== L4T release"; cat /etc/nv_tegra_release
echo "== kernel"; uname -a
echo "== power mode"; sudo nvpmodel -q
echo "== boot time"; systemd-analyze
echo "== critical chain"; systemd-analyze critical-chain --no-pager | sed -n '1,20p'
echo "== slowest units"; systemd-analyze blame --no-pager | sed -n '1,15p'
echo "== RAM"; free -m
echo "== swap"; swapon --show
echo "== disk"; df -h /
echo "== package count"; dpkg -l | grep -c '^ii'
echo "== running services"; systemctl list-units --type=service --state=running --no-legend | wc -l
echo "== listening ports"; ss -tlnp
echo "== kernel image size"; ls -l /boot/Image*
echo "== modules size"; du -sh /lib/modules/"$(uname -r)"
echo "== biggest top-level folders"; sudo du -xh --max-depth=1 / 2>/dev/null | sort -h | tail -12
echo "== top memory users"; ps aux --sort=-rss | sed -n '1,10p'
echo "== idle power sample"; sudo timeout 10 tegrastats
} 2>&1 | tee "$F"

echo
echo "Saved to $F"
