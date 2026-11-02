#!/usr/bin/env bash
# Average power while the GPU is busy, GPU clocks and peak temperature, from a
# tegrastats log. Optionally also prints FPS per watt.
# Usage: scripts/summarize-power.sh LOGFILE [FPS]
#   e.g. scripts/summarize-power.sh results/stock/tegrastats-infer.log 22.16
#
# Power is POM_5V_IN, the module input rail (not the wall power). A sample counts
# as "busy" when GR3D_FREQ (GPU load) is at least 90%, so idle gaps between runs
# do not dilute the average.
set -euo pipefail
log="${1:?usage: summarize-power.sh LOGFILE [FPS]}"
fps="${2:-}"
[ -f "$log" ] || { echo "No such file: $log" >&2; exit 1; }

awk -v fps="$fps" '
{
  load = -1
  if (match($0, /GR3D_FREQ [0-9]+%@[0-9]+/)) {
    s = substr($0, RSTART, RLENGTH); sub(/GR3D_FREQ /, "", s)
    split(s, a, "%@"); load = a[1] + 0; clk = a[2]
  }
  pw = ""
  if (match($0, /POM_5V_IN [0-9]+/)) pw = substr($0, RSTART + 10, RLENGTH - 10) + 0
  if (match($0, /thermal@[0-9.]+/)) {
    t = substr($0, RSTART + 8, RLENGTH - 8) + 0
    if (t > peak) peak = t
  }
  total++
  if (load >= 90 && pw != "") { busy++; sum += pw; clocks[clk]++ }
}
END {
  printf "Samples: %d total, %d busy (GPU load >= 90%%)\n", total, busy
  if (busy == 0) { print "No busy samples found: was the benchmark running while the log was written?"; exit 1 }
  w = sum / busy / 1000
  printf "Average power while busy: %.2f W (module input rail)\n", w
  printf "Peak thermal zone temperature: %.2f C\n", peak
  printf "GPU clock while busy (MHz: samples):"
  for (c in clocks) printf " %s: %d", c, clocks[c]
  printf "\n"
  if (fps != "") printf "Efficiency: %.2f FPS per watt (%.2f FPS / %.2f W)\n", fps / w, fps, w
}' "$log"
