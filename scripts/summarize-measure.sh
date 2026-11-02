#!/usr/bin/env bash
# Print headline numbers from a baseline file made by measure-stock.sh or
# measure-image.sh. Works on the laptop.
# Usage: scripts/summarize-measure.sh results/ours/baseline-ours-v0.txt
set -euo pipefail
f="${1:?usage: summarize-measure.sh baseline-file.txt}"
[ -f "$f" ] || { echo "No such file: $f" >&2; exit 1; }

awk '
/^KernelTimestampMonotonic=/   { split($0, a, "="); kern = a[2] }
/^UserspaceTimestampMonotonic=/ { split($0, a, "="); usr  = a[2] }
/^FinishTimestampMonotonic=/   { split($0, a, "="); fin  = a[2] }
/^MemTotal:/                   { tot  = $2 / 1024 }
/^MemAvailable:/               { avail = $2 / 1024 }
/^Mem:/                        { tot = $2; avail = $7 }          # free -m (stock)
/^== running services$/        { want = 1; next }
want == 1 && /^[0-9]+$/        { svc = $1; want = 0 }
/^\/dev\/mmcblk0p1/            { used = $3 }
/^== package count$/           { wantpkg = 1; next }
wantpkg == 1 && /^[0-9]+$/     { pkgs = $1; wantpkg = 0 }
END {
  if (fin != "") {
    printf "Boot, kernel start to boot finished : %.2f s (before systemd %.2f s, systemd startup %.2f s)\n", fin/1e6, usr/1e6, (fin-usr)/1e6
  } else {
    print "Boot, kernel start to boot finished : not in this file (stock: read the graphical.target line of systemd-analyze)"
  }
  if (tot != "") printf "RAM in use at idle                  : %.0f MB (total %.0f MB, available %.0f MB)\n", tot-avail, tot, avail
  if (svc != "")  printf "Running services                    : %s\n", svc
  if (pkgs != "") printf "Installed packages                  : %s\n", pkgs
  if (used != "") printf "Root filesystem used                : %s\n", used
}' "$f"
