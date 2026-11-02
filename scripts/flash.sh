#!/usr/bin/env bash
# Flash the Jetson Nano from the Yocto build. THIS ERASES THE SD CARD IN THE NANO.
# Usage: scripts/flash.sh [image-name]      (default: core-image-minimal)
# Optional: FLASH_DIR=/some/folder to change where the package is unpacked
#           (default: ~/tegraflash, deleted and recreated each time).
#
# Before running: power the Nano off, fit the FRC jumper, connect micro-USB to
# this laptop, then connect the barrel-jack power. See docs/build-and-flash.md.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="${1:-core-image-minimal}"
DEPLOY=build/tmp/deploy/images/jetson-nano-devkit
PKG="$DEPLOY/${IMAGE}-jetson-nano-devkit.tegraflash.tar.gz"
OUT="${FLASH_DIR:-$HOME/tegraflash}"

if [ ! -f "$PKG" ]; then
  echo "Flashing package not found: $PKG" >&2
  echo "Build first with scripts/build.sh" >&2
  exit 1
fi

if ! lsusb -d 0955: | grep -q .; then
  echo "No NVIDIA device found in recovery mode (lsusb -d 0955: is empty)." >&2
  echo "Power the Nano off, fit the jumper across FRC, connect micro-USB, then connect power." >&2
  echo "The jumper must be in place BEFORE power is applied." >&2
  exit 1
fi
lsusb -d 0955:

echo "Package : $PKG"
echo "Unpack  : $OUT (will be deleted and recreated)"
echo
echo "This erases the SD card in the Nano. Press Enter to continue, Ctrl+C to cancel."
read -r _

rm -rf "$OUT"
mkdir -p "$OUT"
# Use tar from a terminal; graphical extractors can produce broken results.
tar -xf "$PKG" -C "$OUT"

cd "$OUT"
sudo ./doflash.sh

echo
echo "Flashing finished. Remove the FRC jumper, power-cycle the Nano,"
echo "wait about a minute, then: ssh root@192.168.55.1"
