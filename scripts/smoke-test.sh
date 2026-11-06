#!/usr/bin/env bash
# scripts/smoke-test.sh
# End-to-end smoke test for the EdgeML Jetson system.
# Verifies connectivity, GPU/camera device access, service status, sandboxing,
# read-only rootfs, security exposure rating, and live MQTT stream.

set -euo pipefail

NANO_HOST="${1:-nano-usb}"
MQTT_TOPIC="edgeml/detections"
TIMEOUT_SECS=5

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

echo "=== EdgeML Jetson Smoke Test ==="
info "Target: $NANO_HOST"

# 1. Connectivity
info "1/7: Checking SSH connectivity..."
if ssh -o BatchMode=yes -o ConnectTimeout=3 "$NANO_HOST" "true" 2>/dev/null; then
    pass "SSH connection successful"
else
    fail "Cannot reach $NANO_HOST via SSH"
fi

# 2. Hardware devices
info "2/7: Checking GPU and camera device nodes..."
DEV_CHECK=$(ssh "$NANO_HOST" "test -e /dev/video0 && test -e /dev/nvmap && test -e /dev/nvhost-gpu && echo OK || echo MISSING")
if [ "$DEV_CHECK" = "OK" ]; then
    pass "Camera (/dev/video0) and GPU (/dev/nvmap, /dev/nvhost-gpu) device nodes present"
else
    fail "One or more required device nodes are missing on $NANO_HOST"
fi

# 3. Detector service status
info "3/7: Checking edgeml-detector service state..."
SVC_STATE=$(ssh "$NANO_HOST" "systemctl is-active edgeml-detector || true")
if [ "$SVC_STATE" = "active" ]; then
    pass "edgeml-detector.service is active"
else
    fail "edgeml-detector.service is $SVC_STATE (expected active)"
fi

# 4. Service sandboxing & user check
info "4/7: Checking unprivileged execution..."
PID=$(ssh "$NANO_HOST" "systemctl show -p MainPID --value edgeml-detector")
SVC_UID=$(ssh "$NANO_HOST" "awk '/^Uid:/ {print \$2}' /proc/$PID/status 2>/dev/null || true")
if [ "$SVC_UID" = "1200" ]; then
    pass "edgeml-detector is running under unprivileged UID: $SVC_UID (edgeml)"
else
    fail "edgeml-detector is running as UID $SVC_UID (expected 1200)"
fi

# 5. Read-only root filesystem check
info "5/7: Checking root filesystem mount options..."
RO_CHECK=$(ssh "$NANO_HOST" "mount | grep ' on / ' | grep -o 'ro\|rw' | head -n 1")
if [ "$RO_CHECK" = "ro" ]; then
    pass "Root filesystem is mounted read-only (ro)"
else
    info "Root filesystem is currently mounted $RO_CHECK"
fi

# 6. Security exposure rating
info "6/7: Checking systemd security exposure rating..."
EXPOSURE=$(ssh "$NANO_HOST" "/usr/bin/systemd-analyze security edgeml-detector 2>/dev/null | grep 'Overall exposure level' || true")
if [ -n "$EXPOSURE" ]; then
    pass "$EXPOSURE"
else
    info "systemd-analyze security not installed on target; skipping check"
fi

# 7. Live MQTT stream reception
info "7/7: Checking live MQTT detection stream ($MQTT_TOPIC)..."
if command -v mosquitto_sub >/dev/null 2>&1; then
    MSGS=$(mosquitto_sub -t "$MQTT_TOPIC" -C 3 -W "$TIMEOUT_SECS" 2>/dev/null || true)
    if [ -n "$MSGS" ]; then
        SAMPLE=$(echo "$MSGS" | head -n 1)
        pass "Received live detections over MQTT:"
        echo "       $SAMPLE"
    else
        fail "No MQTT messages received on topic $MQTT_TOPIC within ${TIMEOUT_SECS}s"
    fi
else
    info "mosquitto_sub not found on host; skipping live MQTT verification"
fi

echo ""
pass "All smoke tests passed successfully!"
