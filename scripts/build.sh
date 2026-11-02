#!/usr/bin/env bash
# Build the development image with kas.
# Usage: scripts/build.sh [kas-config]     (default: kas/edgeml-dev.yml)
# Run from a normal shell, not inside a Python virtual environment.
set -euo pipefail
cd "$(dirname "$0")/.."

CONFIG="${1:-kas/edgeml-dev.yml}"

if [ -n "${VIRTUAL_ENV:-}" ]; then
  echo "Leave the Python virtual environment first (run: deactivate), then retry." >&2
  exit 1
fi
if ! command -v kas >/dev/null 2>&1; then
  echo "kas not found. Install it with: pip3 install --user kas" >&2
  echo "and make sure ~/.local/bin is on your PATH." >&2
  exit 1
fi

kas build "$CONFIG"

DEPLOY=build/tmp/deploy/images/jetson-nano-devkit
echo
echo "Build finished. Flashing package(s):"
ls -lh "$DEPLOY"/*.tegraflash.tar.gz
echo
echo "Next: put the Nano in recovery mode, then run scripts/flash.sh"
