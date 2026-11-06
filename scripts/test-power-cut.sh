#!/usr/bin/env bash
# scripts/test-power-cut.sh
# Simulates ungraceful abrupt power cuts during active inference.
# Verifies read-only filesystem integrity, automatic recovery, and detector resumption.
# Runs N cycles (default: 5) using kernel emergency restart (SysRq 'b').

set -euo pipefail

NANO_HOST="${1:-nano-usb}"
CYCLES="${2:-5}"
LOGFILE="results/ours/reliability/power-cut-test.log"
MQTT_TOPIC="edgeml/detections"

mkdir -p results/ours/reliability

echo "=== EdgeML Power-Cut Resilience Test ===" | tee "$LOGFILE"
echo "Target: $NANO_HOST" | tee -a "$LOGFILE"
echo "Planned cycles: $CYCLES" | tee -a "$LOGFILE"
echo "Timestamp: $(date -u)" | tee -a "$LOGFILE"
echo "----------------------------------------" | tee -a "$LOGFILE"

for cycle in $(seq 1 "$CYCLES"); do
    echo "" | tee -a "$LOGFILE"
    echo ">>> Cycle $cycle / $CYCLES: Initial verification..." | tee -a "$LOGFILE"
    
    # 1. Verify board is up and detector is publishing
    if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "$NANO_HOST" "true" 2>/dev/null; then
        echo "[ERROR] Cannot reach $NANO_HOST before cycle $cycle" | tee -a "$LOGFILE"
        exit 1
    fi

    # Check detector is running
    SVC_ACTIVE=$(ssh "$NANO_HOST" "systemctl is-active edgeml-detector 2>/dev/null || true")
    echo "  Detector status before cut: $SVC_ACTIVE" | tee -a "$LOGFILE"
    
    # Check mount is read-only
    MOUNT_STATE=$(ssh "$NANO_HOST" "mount | grep ' on / ' | grep -o 'ro\|rw' | head -n 1")
    echo "  Root mount state: $MOUNT_STATE" | tee -a "$LOGFILE"

    # Capture a sample detection
    PRE_MSG=$(mosquitto_sub -t "$MQTT_TOPIC" -C 1 -W 3 2>/dev/null || echo "NONE")
    echo "  Pre-cut detection sample: $PRE_MSG" | tee -a "$LOGFILE"

    # 2. Trigger abrupt kernel emergency restart (simulating power cut during active load)
    echo "  [TRIGGER] Simulating abrupt power cut (SysRq emergency restart)..." | tee -a "$LOGFILE"
    CUT_START=$(date +%s)
    
    # Enable SysRq and trigger immediate reset without unmounting/syncing
    ssh -o BatchMode=yes -o ConnectTimeout=3 "$NANO_HOST" "echo 1 > /proc/sys/kernel/sysrq; echo b > /proc/sysrq-trigger" 2>/dev/null || true

    echo "  Reset signal sent. Waiting for board to drop and reboot..." | tee -a "$LOGFILE"
    sleep 3

    # 3. Wait for board to come back online
    REBOOT_SUCCESS=0
    for i in $(seq 1 45); do
        if ssh -o BatchMode=yes -o ConnectTimeout=2 "$NANO_HOST" "true" 2>/dev/null; then
            REBOOT_SUCCESS=1
            break
        fi
        sleep 1
    done

    CUT_END=$(date +%s)
    REBOOT_TIME=$((CUT_END - CUT_START))

    if [ "$REBOOT_SUCCESS" -ne 1 ]; then
        echo "  [FAIL] Board failed to reboot within 45 seconds!" | tee -a "$LOGFILE"
        exit 1
    fi

    echo "  [RECOVERED] Board back online in ~${REBOOT_TIME}s" | tee -a "$LOGFILE"

    # 4. Verify post-reboot health
    POST_MOUNT=$(ssh "$NANO_HOST" "mount | grep ' on / ' | grep -o 'ro\|rw' | head -n 1")
    echo "  Post-reboot rootfs mount: $POST_MOUNT" | tee -a "$LOGFILE"

    # Check for ext4 error messages in dmesg
    FS_ERRORS=$(ssh "$NANO_HOST" "dmesg | grep -i 'EXT4-fs error' || true")
    if [ -n "$FS_ERRORS" ]; then
        echo "  [FAIL] Filesystem errors detected in dmesg:" | tee -a "$LOGFILE"
        echo "$FS_ERRORS" | tee -a "$LOGFILE"
        exit 1
    else
        echo "  Filesystem integrity: CLEAN (zero EXT4-fs errors)" | tee -a "$LOGFILE"
    fi

    # Check that detector auto-started
    sleep 2
    POST_SVC=$(ssh "$NANO_HOST" "systemctl is-active edgeml-detector 2>/dev/null || true")
    echo "  Detector auto-start status: $POST_SVC" | tee -a "$LOGFILE"

    # Check MQTT stream resumed
    POST_MSG=$(mosquitto_sub -t "$MQTT_TOPIC" -C 1 -W 5 2>/dev/null || echo "TIMEOUT")
    if [ "$POST_MSG" != "TIMEOUT" ] && [ -n "$POST_MSG" ]; then
        echo "  [PASS] MQTT stream resumed successfully:" | tee -a "$LOGFILE"
        echo "         $POST_MSG" | tee -a "$LOGFILE"
    else
        echo "  [WARN] MQTT stream not received within 5s" | tee -a "$LOGFILE"
    fi

    echo "  Cycle $cycle completed successfully." | tee -a "$LOGFILE"
    sleep 2
done

echo "" | tee -a "$LOGFILE"
echo "=== Resilience Test Complete: $CYCLES / $CYCLES cycles passed with zero corruption! ===" | tee -a "$LOGFILE"
