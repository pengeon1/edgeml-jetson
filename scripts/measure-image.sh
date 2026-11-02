#!/bin/sh
# Idle measurements on OUR Yocto image (BusyBox userland, no sudo, no systemd-analyze).
# Run on the Nano after it has been idle for about 5 minutes. Measure on the
# third boot after flashing, because the first boot does one-off setup work.
# Usage: scripts/measure-image.sh [outdir] [label]
#        (defaults: ~/baseline and "ours", giving baseline-ours.txt)
#
# BusyBox 'head' does not accept -N, so sed -n is used instead.
OUT="${1:-$HOME/baseline}"
LABEL="${2:-ours}"
mkdir -p "$OUT"
F="$OUT/baseline-$LABEL.txt"

{
echo "== date"; date
echo "== release"; cat /etc/os-release; cat /etc/nv_tegra_release 2>&1
echo "== kernel"; uname -a
echo "== boot timing (microseconds since kernel start)"
systemctl show --property=KernelTimestampMonotonic --property=UserspaceTimestampMonotonic --property=FinishTimestampMonotonic
echo "== uptime"; cat /proc/uptime
echo "== failed units"; systemctl --failed --no-pager
echo "== RAM"; grep -E 'MemTotal|MemFree|MemAvailable|^Cached' /proc/meminfo
echo "== disk"; df -h /
echo "== running services"; systemctl list-units --type=service --state=running --no-legend --no-pager | wc -l
echo "== running service names"; systemctl list-units --type=service --state=running --no-legend --no-pager | awk '{print $1}'
echo "== listening ports"; (ss -tlnp 2>/dev/null || netstat -tln)
echo "== /boot"; ls -l /boot
echo "== kernel modules"; ls /lib/modules; du -sh /lib/modules/* 2>&1
echo "== loaded modules"; lsmod | sed -n '1,30p'
echo "== GPU device nodes"; ls /dev/nvhost* /dev/nvmap 2>&1 | sed -n '1,12p'
echo "== processes"; ps w | sed -n '1,25p'
} 2>&1 | tee "$F"

echo
echo "Saved to $F"
