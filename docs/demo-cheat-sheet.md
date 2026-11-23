# CS3000 Operating Systems: Live Demo Cheat Sheet

**Target:** NVIDIA Jetson Nano (`192.168.55.1` via USB)  
**Host:** Laptop running Ubuntu (`192.168.55.100`)  
**Duration:** ~3 Minutes during the 10-Minute Presentation  

---

## 🔌 Step 0: Pre-Demo Setup (Before Calling Dr. Raghavan)

1. **Hardware Connections:**
   - **J48 Jumper:** Fitted across both pins (so the board uses the 5V 4A barrel jack).
   - **Power:** Connect 5V 4A barrel jack supply.
   - **Data Cable:** Connect Micro-USB from Jetson Nano to your laptop USB port.
   - **Camera:** Plug Logitech C270 USB webcam into any USB 3.0 port on the Jetson Nano.
2. **Laptop Mosquitto Broker Check:**
   Open a terminal on your laptop:
   ```bash
   sudo systemctl restart mosquitto
   ```
3. **Quick Ping Test:**
   ```bash
   ssh nano-usb "echo 'Nano is READY'"
   ```

---

## 🎬 Live Demo Commands (Step-by-Step)

---

### Step 1: Run the 7-Point Automated Health & Security Audit (45s)
**Who presents:** Narayana Murthy S / Team  
**Where to run:** Terminal on your Laptop  

```bash
cd ~/edgeml-jetson
./scripts/smoke-test.sh nano-usb
```

**What Dr. Raghavan will see on screen:**
- `[PASS] SSH connection successful`
- `[PASS] GPU device nodes (/dev/nvmap, /dev/nvhost-gpu) present`
- `[PASS] edgeml-detector.service is active`
- `[PASS] edgeml-detector is running under unprivileged UID: 1200 (edgeml)`
- `[PASS] Root filesystem is mounted read-only (ro)`
- `[PASS] → Overall exposure level: 3.2 OK 🙂`
- `[PASS] Received live detections over MQTT`

**What to say:**
> *"Dr. Raghavan, our automated smoke test validates 7 OS checkpoints across the USB network: unprivileged execution under UID 1200, an immutable read-only rootfs, access to the Maxwell GPU device nodes, and a systemd security rating of 3.2 OK—reduced from 9.6 UNSAFE."*

---

### Step 2: Show the Live Pipelined Web Telemetry Dashboard (1 min)
**Who presents:** Piyush Mishra / Team  
**Where to run:** Terminal on your Laptop  

```bash
python3 scripts/web-dashboard.py 8080
```
Then open your browser to: **`http://localhost:8080`**

**What Dr. Raghavan will see on screen:**
- Live camera viewport with bounding boxes around people in front of the webcam.
- **20.0 FPS** instantaneous throughput gauge.
- **48.0 ms** inference latency bar.
- Rolling sparkline charts showing real-time framerate stability.
- System badges confirming `UID: 1200`, `Rootfs: ro`, and `Score: 3.2 OK`.

**What to say:**
> *"Here is our live zero-dependency telemetry dashboard consuming detections over MQTT.*  
> *Notice that we are streaming at a steady **20.0 FPS**. In a sequential loop, the system stalled at 18.3 FPS. By implementing multithreaded triple-buffering in C++, our producer thread overlaps CPU letterboxing (11 ms) on Core 1 concurrently with GPU TensorRT inference (48 ms) on Core 0, hiding 100% of the CPU pre-processing overhead."*

---

### Step 3: Trigger a Live Emergency Power-Cut Reset (1 min)
**Who presents:** Ankush R & Mahalis Rayhan / Team  
**Where to run:** A second terminal on your Laptop  

Trigger an immediate emergency kernel reset during active GPU inference:
```bash
ssh nano-usb "echo 1 > /proc/sys/kernel/sysrq; echo b > /proc/sysrq-trigger"
```

*The SSH connection immediately terminates. Count out loud:*  
> *"1... 2... 3... 4 seconds!"*

Now reconnect and verify the filesystem health:
```bash
ssh nano-usb "mount | grep ' on / '; dmesg | grep -i 'EXT4-fs'"
```

**What Dr. Raghavan will see on screen:**
- `/dev/mmcblk0p1 on / type ext4 (ro,relatime,data=ordered)`
- Zero EXT4 filesystem or journal corruption errors!

Look back at the browser tab (`http://localhost:8080`):
- The MQTT detection feed has automatically resumed streaming!

**What to say:**
> *"We just triggered an ungraceful hardware reset (`SysRq 'b'`) while the GPU was inferencing at 20 FPS. The board dropped and rebooted in only 4 seconds. Because our root filesystem is mounted strictly read-only with volatile state on `tmpfs`, `dmesg` reports zero EXT4 corruption errors, and `edgeml-detector.service` automatically resumed streaming without manual intervention."*

---

## 🔍 Backup Commands (If Dr. Raghavan Asks to Inspect the System)

#### If he asks: *"Can you show me the trimmed kernel?"*
```bash
ssh nano-usb "uname -r; ls -lh /boot/Image"
```
*(Shows Linux 4.9.337 with a **28.5 MB** kernel image, pruned down from 38.5 MB).*

#### If he asks: *"How much memory is really free?"*
```bash
ssh nano-usb "free -m"
```
*(Shows **217 MB** used, **~3.7 GB free** for AI models).*

#### If he asks: *"Show me the sandboxed systemd configuration."*
```bash
ssh nano-usb "systemctl cat edgeml-detector.service"
```
*(Shows `User=edgeml`, `NoNewPrivileges=true`, `ProtectSystem=strict`, and `DeviceAllow=char-57000000.gpu rw`).*

#### If he asks: *"Can you prove that the filesystem cannot be modified?"*
```bash
ssh nano-usb "touch /etc/hacked.txt"
```
*(Fails immediately with `touch: /etc/hacked.txt: Read-only file system`).*

#### If he asks: *"Can you switch to 5 W mode?"*
```bash
ssh nano-usb "nvpmodel -m 1"
```
*(Switches from 10 W MAXN to 5 W mode; draws 3.84 W while sustaining 12.5 FPS).*
