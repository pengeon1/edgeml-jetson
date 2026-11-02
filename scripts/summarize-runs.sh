#!/usr/bin/env bash
# Mean and standard deviation over trtexec-run*.txt files (sample standard
# deviation, n-1). Works on the laptop or the Nano.
# Usage: scripts/summarize-runs.sh DIR
set -euo pipefail
dir="${1:?usage: summarize-runs.sh DIR}"
shopt -s nullglob
files=("$dir"/trtexec-run*.txt)
if [ "${#files[@]}" -eq 0 ]; then
  echo "No trtexec-run*.txt files in $dir" >&2
  exit 1
fi

awk '
function val(line, pat,    s) {            # number after "= " in the first match of pat
  # pat must be passed as a STRING: a bare /regex/ argument would be evaluated
  # against $0 and arrive as 0 or 1.
  if (match(line, pat)) { s = substr(line, RSTART, RLENGTH); sub(/.*= /, "", s); return s + 0 }
  return ""
}
/\[I\] Throughput:/ {
  for (i = 1; i <= NF; i++) if ($i == "Throughput:") { n++; tp[n] = $(i + 1) + 0 }
}
/\[I\] Latency:/ {
  lm[n] = val($0, "mean = [0-9.]+")
  lp[n] = val($0, "percentile\\(99%\\) = [0-9.]+")
}
/\[I\] GPU Compute Time:/ {
  gm[n] = val($0, "mean = [0-9.]+")
}
function stat(arr, n, label,    i, s, m, v) {
  s = 0; for (i = 1; i <= n; i++) s += arr[i]
  m = s / n
  v = 0; for (i = 1; i <= n; i++) v += (arr[i] - m) ^ 2
  v = (n > 1) ? sqrt(v / (n - 1)) : 0
  printf "%-28s %.2f ± %.3f\n", label, m, v
}
END {
  if (n == 0) { print "No summary lines found" > "/dev/stderr"; exit 1 }
  printf "Runs: %d\n", n
  stat(tp, n, "Throughput (inferences/s)")
  stat(lm, n, "Latency, mean (ms)")
  stat(lp, n, "Latency, 99th percentile (ms)")
  stat(gm, n, "GPU compute time, mean (ms)")
}' "${files[@]}"
