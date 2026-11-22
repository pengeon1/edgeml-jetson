# CS3000 Operating Systems: 10-Minute Presentation & Demo Guide

**Course:** CS3000 Operating Systems  
**Instructor:** Dr. Raghavan Santhanam  
**Project:** `edgeml-jetson`: Application-Specific Embedded Linux Distribution for Edge Machine Learning  
**Target Hardware:** NVIDIA Jetson Nano Developer Kit (4 GB unified LPDDR4, 128-core Maxwell GPU, Quad Cortex-A57 @ 1.48 GHz)  

### 👥 Team Members
1. **Narayana Murthy S** (CS24B1047)
2. **Piyush Mishra** (CS24B1048)
3. **Ankush R** (CS24B1062)
4. **Mahalis Rayhan** (CS24B1095)

**Total Time Budget:** 10 Minutes (~7.0 mins slide talk + ~3.0 mins live demo)

---

## ⏱️ 4-Person Presentation Flow & Speaking Plan

```
[0:00 - 2:00]  PRESENTER 1: Narayana Murthy S (Slides 1 & 2: Intro, Problem & Motivation)
[2:00 - 4:30]  PRESENTER 2: Piyush Mishra (Slides 3 & 4: Kernel Trimming, Boot & Concurrency)
[4:30 - 6:00]  PRESENTER 3: Ankush R (Slides 5 & 6: Memory, Power & Security Isolation)
[6:00 - 7:30]  PRESENTER 4: Mahalis Rayhan (Slides 7 & 8: VFS Fault Tolerance & Master Results)
[7:30 - 10:00] ALL 4 TEAM MEMBERS (Slide 9 & Live Hardware Demonstration)
```

---

## 🎤 Detailed Slide-by-Slide Script (Simple & Results-Focused)

---

### PART 1: Motivation & Problem Statement (0:00 – 2:00)
**Presenter: Narayana Murthy S (CS24B1047)**

#### Slide 1: Title & Team Overview (0:00 – 0:45)
> *"Good morning Dr. Raghavan. Today, our team—Narayana Murthy, Piyush Mishra, Ankush, and Mahalis Rayhan—is presenting our CS3000 Operating Systems final project: **edgeml-jetson**.*  
> *Our goal was to solve a core systems problem: why general-purpose desktop operating systems fail on resource-constrained edge AI hardware, and how vertically tailoring an embedded Linux distribution from source delivers a 10x smaller, faster, and crash-proof appliance on the NVIDIA Jetson Nano."*

#### Slide 2: The Problem: Desktop Distros on Edge Devices (0:45 – 2:00)
> *"When boards like the Jetson Nano ship from vendors, they provide a desktop distribution like stock JetPack (Ubuntu 18.04 LTS). This introduces four critical operating system failures:*  
> 1. ***Storage Bloat:*** *Consumes **12 GB** of flash with **2,351 packages**. Desktop apps like LibreOffice, X11, and CUPS waste 88% of storage.*  
> 2. ***Memory Contention:*** *Uses **670 MB RAM** at idle. In the Jetson Nano's unified memory architecture, the CPU and GPU share the same 4 GB physical bus—idle OS daemons directly starve deep learning models.*  
> 3. ***Boot Delays:*** *Takes **15.5 seconds** to boot due to serial console congestion over a slow 115,200 baud UART line.*  
> 4. ***Storage Fragility:*** *Standard writable ext4 rootfs corrupts file system journals upon abrupt power cuts.*  
> *Now Piyush will explain how we tailored the kernel and process concurrency."*

---

### PART 2: Kernel Tailoring & Process Concurrency (2:00 – 4:30)
**Presenter: Piyush Mishra (CS24B1048)**

#### Slide 3: Kernel Customization & Boot Optimization (2:00 – 3:15)
> *"Starting from NVIDIA’s monolithic `tegra_defconfig` (2,388 options), we tailored Linux 4.9.337 using kernel config fragments (`edgeml-trim.cfg`):*  
> - ***Pruned 625 Options (-26%):*** *We eliminated ALSA sound, Bluetooth, CSI camera sensors, legacy DRM, and tracing profilers (`DEBUG_KMEMLEAK`, `FTRACE`).*  
> - ***Total Kernel Size:*** *Reduced from **112.5 MB to 80.6 MB (-28.4%)**.*  
> - ***Boot Acceleration:*** *By injecting `quiet loglevel=3`, we silenced 65 KB of verbose boot logging over the 115,200 baud serial UART line. Kernel handover dropped from 6.1 s to **1.87 s (-69%)**, and total boot time dropped from 15.5 s to **4.6 s (70% faster)**."*

#### Slide 4: Concurrency: Multithreaded Triple-Buffering at 20.0 FPS (3:15 – 4:30)
> *"Next, we tackled process concurrency in our C++ detector daemon (`edgeml-detector.cpp`).*  
> *In naive sequential execution, the CPU and GPU stall waiting for each other:*  
> $$\text{Sequential: } 11.0\text{ ms (CPU)} + 48.2\text{ ms (GPU)} + 1.8\text{ ms (MQTT)} = 61.0\text{ ms} \implies 18.3\text{ FPS}$$  
> *To eliminate pipeline stalls, we architected a two-stage decoupled producer-consumer pipeline with **triple-buffering** using pinned host memory (`cudaMallocHost`):*  
> - ***Stage 1 (Producer on Core 1):*** *Captures V4L2 frames zero-copy and executes bilinear letterbox scaling into pinned host memory.*  
> - ***Stage 2 (Consumer on GPU + Core 0):*** *Issues async DMA copy (`cudaMemcpyAsync`), enqueues TensorRT FP16 inference, and publishes MQTT JSON.*  
> - ***Synchronization:*** *Managed via `std::mutex` and `std::condition_variable`. Stale frames are automatically dropped if the consumer is busy to guarantee real-time latency (< 116 ms).*  
> *Because CPU letterboxing is 100% overlapped behind GPU compute, live streaming throughput jumped from **18.3 FPS to 20.0 FPS** (+9.3% gain).*  
> *Now Ankush will cover memory management and security isolation."*

---

### PART 3: Memory Headroom & Security Isolation (4:30 – 6:00)
**Presenter: Ankush R (CS24B1062)**

#### Slide 5: Memory Headroom & Power Modes (4:30 – 5:15)
> *"Looking at system memory and power:*  
> - ***Memory Headroom:*** *Idle RAM dropped from 670 MB to **217 MB (-67.6%)**, liberating **+450 MB of unified RAM** (3.78 GB free for large models).*  
> - ***Power Modes (DVFS):*** *In MAXN (10 W), the system achieves 20.0 FPS at 6.22 W. In **5 W mode (`nvpmodel -m 1`)**, the OS shuts down 2 CPU cores and throttles clocks: power drops from 6.22 W down to **3.84 W (-38% heat)** while sustaining 12.5 FPS, boosting energy efficiency to **3.26 FPS/W (+10.8%)**."*

#### Slide 6: Security Isolation & Least Privilege (5:15 – 6:00)
> *"For system security, we applied the principle of least privilege:*  
> - ***Service Sandboxing:*** *`edgeml-detector.service` runs under dedicated unprivileged user `edgeml:video` (UID 1200), not root, with `NoNewPrivileges=true`, `ProtectSystem=strict`, and `PrivateTmp=true`.*  
> - ***Maxwell GPU Major 506 Discovery:*** *Standard systemd `char-nvhost` only matches Major 242. On Jetson Nano, the Maxwell GPU character node is Major **506** (`char-57000000.gpu`). We configured `DeviceAllow` and custom udev rule `99-tegra-devices.rules` (mode 0660) to allow non-root GPU hardware acceleration.*  
> - ***Exposure Rating:*** *`systemd-analyze security` dropped from **9.6 UNSAFE to 3.2 OK (-67% attack exposure)**.*  
> - *We additionally enforced SSH key-only authentication, closed port 5355, and applied kernel sysctls for IP anti-spoofing.*  
> *Now Mahalis will present VFS fault tolerance and our master benchmark results."*

---

### PART 4: VFS Fault Tolerance & Master Results (6:00 – 7:30)
**Presenter: Mahalis Rayhan (CS24B1095)**

#### Slide 7: VFS Architecture & Power-Cut Resilience (6:00 – 6:45)
> *"Edge appliances frequently experience sudden power disconnections.*  
> - ***Immutable VFS:*** *Root partition `/dev/mmcblk0p1` is mounted strictly **Read-Only (`ro`)**. Volatile runtime directories (`/run`, `/tmp`, `/var/volatile`) are mounted in RAM via `tmpfs`.*  
> - ***Empirical Validation:*** *We subjected the live board to **5 consecutive emergency hardware resets** (`SysRq 'b'`) during active 20 FPS GPU inference.*  
> - ***Results:*** *In **5 out of 5 cycles**, the board recovered within 3–4 seconds with **zero EXT4 filesystem errors**, clean journal replay, and automatic detector resumption over MQTT."*

#### Slide 8: Master Evaluation & Defending Baseline B (6:45 – 7:30)
> *"Looking at our master comparison:*  
> - *Flashing archive: **738 MB vs 6.56 GB (-88.7%)**.*  
> - *Used rootfs: **1.4 GB vs 12.0 GB (-88.3%)**.*  
> - *Total boot: **4.6 s vs 15.5 s (-70.3%)**.*  
> - *Idle RAM: **217 MB vs 670 MB (-67.6%)**.*  
> - *Refuting **Baseline B (Minimised Stock Ubuntu)**: Disabling the desktop GUI still wastes 10.2 GB on disk, leaves 2,000+ unpinned packages, boots a 112.5 MB kernel, and remains completely vulnerable to power-loss corruption.*  
> *Now our team will demonstrate the live system."*

---

### PART 5: Live Hardware Demonstration (7:30 – 10:00)
**Conducted by All 4 Team Members**

Connect the laptop to the Jetson Nano via micro-USB (`192.168.55.1`).

#### Demo Action 1: Automated Health & Security Audit (Narayana Murthy)
```bash
./scripts/smoke-test.sh nano-usb
```
> **Narayan speaks:** *"First, our automated smoke test audits 7 critical OS checkpoints: unprivileged execution under UID 1200, rootfs mounted strictly read-only (`ro`), systemd exposure score **3.2 OK**, and Maxwell GPU Major 506 device node access."*

#### Demo Action 2: Live Pipelined Telemetry (Piyush Mishra)
```bash
python3 scripts/web-dashboard.py 8080
```
Open `http://localhost:8080` in Chrome:
> **Piyush speaks:** *"Here is our live browser dashboard streaming detections over MQTT at **20.0 FPS** with latency sparklines under **48 ms**, demonstrating concurrent CPU letterbox overlapping on Core 1."*

#### Demo Action 3: Live Power-Cut Reset Demonstration (Ankush & Mahalis)
Trigger emergency reset:
```bash
ssh nano-usb "echo 1 > /proc/sys/kernel/sysrq; echo b > /proc/sysrq-trigger"
```
Wait 4 seconds, then show the board recovering cleanly:
```bash
ssh nano-usb "mount | grep ' on / '; dmesg | grep -i 'EXT4-fs'"
```
> **Ankush speaks:** *"We just triggered an emergency kernel reset simulating an abrupt power cut during active GPU inference. The connection drops... and within 4 seconds, the board is back online."*  
> **Mahalis speaks:** *"As you can see, the root filesystem mounted cleanly as `ro`, `dmesg` reports zero EXT4 errors, and the detector service auto-resumed publishing detections immediately.*  
> *Thank you Dr. Raghavan. We are now ready for your questions."*

---

## 🎓 Expected Professor Questions & Answers

1. **"Why did you use pinned memory (`cudaMallocHost`) instead of managed memory?"**  
   *Answer:* The Tegra X1 (Maxwell) does not support GPU hardware page faulting. `cudaMallocManaged` incurs page migration faults. Pinned host memory locks buffers in physical RAM, allowing asynchronous DMA (`cudaMemcpyAsync`) to proceed without OS page-table intervention.
2. **"How does your read-only rootfs handle application logs and transient files?"**  
   *Answer:* All volatile directories (`/run`, `/tmp`, `/var/volatile`) are backed by in-memory `tmpfs` mounts. Systemd's journal operates in volatile mode in RAM. Persistent model files are stored strictly in `/var/lib/edgeml`.
3. **"Why did serial console silencing save 4 seconds of boot time?"**  
   *Answer:* Transmitting 65 KB of text at 115,200 baud is an I/O bottleneck (~11.5 KB/s) that blocks kernel printk execution synchronously before userspace init. `quiet loglevel=3` silences UART output while preserving all messages in the in-memory `dmesg` buffer.
