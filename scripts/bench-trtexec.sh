#!/usr/bin/env bash
# Repeated TensorRT inference benchmark with a power log. Run on the Nano.
# Usage: scripts/bench-trtexec.sh ENGINE OUTDIR [RUNS] [DURATION_S]
#        defaults: 5 runs of 30 s, 20 s cool-down between runs.
# Output: OUTDIR/trtexec-run1.txt ... trtexec-runN.txt and OUTDIR/tegrastats.log
#
# For a fair comparison, use the same engine file, the same clocks (MAXN with
# jetson_clocks) and the same SD card model on every image you compare.
# Then run scripts/summarize-runs.sh OUTDIR and scripts/summarize-power.sh.
set -u
TEGRA_PID=""
ENGINE="${1:?usage: bench-trtexec.sh ENGINE OUTDIR [RUNS] [DURATION_S]}"
OUT="${2:?usage: bench-trtexec.sh ENGINE OUTDIR [RUNS] [DURATION_S]}"
RUNS="${3:-5}"
DUR="${4:-30}"
COOLDOWN="${COOLDOWN:-20}"
TRTEXEC="${TRTEXEC:-/usr/src/tensorrt/bin/trtexec}"

SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

[ -f "$ENGINE" ] || { echo "Engine not found: $ENGINE" >&2; exit 1; }
[ -x "$TRTEXEC" ] || { echo "trtexec not found at $TRTEXEC (set TRTEXEC=...)" >&2; exit 1; }
mkdir -p "$OUT"

if command -v nvpmodel >/dev/null 2>&1; then
  $SUDO nvpmodel -m 0
else
  echo "WARNING: nvpmodel not found, power mode not fixed. Record this in the report." >&2
fi
if command -v jetson_clocks >/dev/null 2>&1; then
  $SUDO jetson_clocks
else
  echo "WARNING: jetson_clocks not found, clocks not fixed. Record this in the report." >&2
fi

rm -f "$OUT"/tegrastats.log "$OUT"/trtexec-run*.txt
if command -v tegrastats >/dev/null 2>&1; then
  $SUDO tegrastats --interval 1000 --logfile "$OUT/tegrastats.log" &
  TEGRA_PID=$!
else
  echo "WARNING: tegrastats not found, no power log will be written." >&2
fi

i=1
while [ "$i" -le "$RUNS" ]; do
  echo "--- run $i of $RUNS"
  "$TRTEXEC" --loadEngine="$ENGINE" --duration="$DUR" --warmUp=2000 2>&1 \
    | tee "$OUT/trtexec-run$i.txt" \
    | grep -E '\[I\] (Throughput|Latency:|GPU Compute Time)'
  i=$((i + 1))
  [ "$i" -le "$RUNS" ] && sleep "$COOLDOWN"
done

# BusyBox has no pkill, so stop tegrastats by PID.
[ -n "${TEGRA_PID:-}" ] && kill "$TEGRA_PID" 2>/dev/null
echo
echo "Done. Logs in $OUT"
echo "Summarise with: scripts/summarize-runs.sh $OUT"
