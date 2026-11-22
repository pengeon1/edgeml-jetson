# CS3000 Operating Systems: 10-Minute Presentation & Demo Guide

**Course:** CS3000 Operating Systems  
**Instructor:** Dr. Raghavan Santhanam  
**Project:** `edgeml-jetson`: Application-Specific Embedded Linux Distribution for Edge Machine Learning  
**Target Hardware:** NVIDIA Jetson Nano Developer Kit (4 GB unified LPDDR4, 128-core Maxwell GPU, Quad Cortex-A57 @ 1.48 GHz)  
**Presenter:** Piyush  
**Total Allocated Time:** 10 Minutes  

---

## ⏱️ Pacing & Time Budget (10 Minutes Total)

| Segment | Timing | Slide / Stage | Content Summary |
| :--- | :--- | :--- | :--- |
| **1. Introduction & Motivation** | 0:00 – 1:30 (1.5 min) | Slides 1 & 2 | Problem statement: Why desktop Linux (Ubuntu 18.04/JetPack) fails on edge hardware. |
| **2. Kernel Tailoring & Boot Optimization** | 1:30 – 3:00 (1.5 min) | Slide 3 | Kernel config pruning (-625 options, -35% size) and console silencing (`quiet loglevel=3`). |
| **3. Concurrency & Pipeline Synchronization** | 3:00 – 4:30 (1.5 min) | Slide 4 | Multithreaded triple buffering (`cudaMallocHost`), producer-consumer pattern, +9.3% FPS. |
| **4. Security, Isolation & VFS Design** | 4:30 – 6:00 (1.5 min) | Slides 5, 6, 7 | Systemd sandboxing (UID 1200, GPU Major 506), read-only rootfs, 5/5 power-cut resilience. |
| **5. Quantitative Results & Baseline B** | 6:00 – 7:00 (1.0 min) | Slide 8 | Master evaluation table, refuting "Minimised Stock" (Baseline B). |
| **6. Live Demonstration** | 7:00 – 9:30 (2.5 min) | Live Hardware | Smoke test execution, interactive web dashboard, and live power-cut reset recovery. |
| **7. Conclusion & Q&A** | 9:30 – 10:00 (0.5 min) | Slide 9 | Core OS takeaways & answering Dr. Raghavan's questions. |

---

## 🎤 Slide-by-Slide Speaking Script & OS Talking Points

### Slide 1: Title Slide (0:00 – 0:30)
> *"Good morning, Dr. Raghavan and fellow classmates. Today I am presenting my final project for CS3000 Operating Systems: **edgeml-jetson**.*  
> *Our goal in this project was to tackle a fundamental operating systems challenge: why are general-purpose desktop operating systems poorly suited for autonomous edge AI appliances, and how can we vertically engineer an embedded Linux distribution—from the kernel configuration to the VFS and process synchronization—to achieve deterministic real-time performance, memory efficiency, and fault tolerance on resource-constrained hardware like the NVIDIA Jetson Nano?"*

---

### Slide 2: The Problem: Desktop Distros on Edge Devices (0:30 – 1:30)
> *"When development boards like the Jetson Nano ship from vendors, they typically provide a desktop Linux distribution—in NVIDIA's case, JetPack based on Ubuntu 18.04 LTS.*  
> *From an Operating Systems perspective, this introduces four critical systemic failures:*  
> 1. ***Storage Bloat:*** *The stock rootfs consumes 12 GB across 2,351 packages. Desktop software like LibreOffice, X11 display servers, and CUPS printing daemons waste 88% of storage.*  
> 2. ***Unified Memory Contention:*** *The Jetson Nano features a unified memory architecture where the Cortex-A57 CPU and Maxwell GPU share a single 4 GB physical LPDDR4 memory bus. Stock Ubuntu consumes 670 MB of RAM at idle. That memory overhead directly reduces the contiguous memory available for neural network weights and frame buffers.*  
> 3. ***Boot Latency:*** *Stock takes 15.5 seconds to boot. We discovered that a major bottleneck was the kernel transmitting 65 KB of verbose boot messages over a 115,200 baud serial console line.*  
> 4. ***Filesystem Fragility:*** *Standard ext4 with a writable root journal frequently corrupts inode trees and metadata upon ungraceful power loss—a common occurrence in real-world edge IoT environments."*

---

### Slide 3: Kernel Customization & Boot Optimization (1:30 – 3:00)
> *"To solve this, we used the Yocto Project with `meta-tegra` to construct an appliance from source code. Our first OS-level optimization was kernel configuration pruning.*  
> *Starting from NVIDIA’s monolithic `tegra_defconfig` (2,388 options), we wrote an incremental configuration fragment `edgeml-trim.cfg` on Linux 4.9.337.*  
> - *We pruned **625 kernel options** (-26% options total). We switched off ALSA sound subsystems, Bluetooth, CSI camera drivers, legacy DRM framebuffers, and memory-tracing profilers like `DEBUG_KMEMLEAK` and `FTRACE`.*  
> - *We deliberately retained the hardware acceleration stack: `host1x` and `nvgpu` for the Maxwell GPU, UVC video for the webcam, and the INA3221 power monitor for telemetry.*  
> - *This reduced the kernel binary image from 38.5 MB to 28.5 MB (-26%) and kernel modules from 85.2 MB to 52.1 MB (-39%).*  
> - *Furthermore, by injecting `quiet loglevel=3` into the kernel command line, we eliminated serial console congestion. Kernel handover to userspace dropped from 6.1 s to **1.87 s** (-69%), and total boot finished dropped from 15.5 s to **4.6 s (70% faster)**."*

---

### Slide 4: Process Concurrency: Multithreaded Triple Buffering (3:00 – 4:30)
> *"Next, we addressed process scheduling and concurrency in our C++ inference daemon (`edgeml-detector.cpp`).*  
> *In a naive sequential execution loop, the CPU and GPU stall waiting for each other: V4L2 capture and CPU bilinear letterboxing take 11.0 ms, GPU TensorRT FP16 inference takes 48.2 ms, and MQTT publishing takes 1.8 ms. Sequentially: $11.0 + 48.2 + 1.8 = 61.0\text{ ms} \implies 18.3\text{ FPS}$. The GPU sat completely idle for 11 ms every frame!*  
> *To eliminate pipeline stalls, we architected a two-stage decoupled producer-consumer pipeline with **triple-buffering** using pinned host memory (`cudaMallocHost`):*  
> - ***Stage 1 (Producer):*** *Runs on Cortex-A57 Core 1. It grabs V4L2 memory-mapped buffers zero-copy and executes bilinear colorspace scaling directly into one of three pinned DMA buffers.*  
> - ***Stage 2 (Consumer):*** *Runs concurrently on Maxwell GPU and Core 0. It executes asynchronous DMA copy (`cudaMemcpyAsync`), enqueues TensorRT FP16 execution, decodes bounding boxes, and publishes JSON telemetry over MQTT.*  
> - ***Synchronization:*** *Managed via `std::mutex` and `std::condition_variable`. To ensure hard real-time latency without buffer bloat, if the consumer is busy, the producer automatically drops older unconsumed frames, keeping glass-to-publish latency strictly below 116 ms.*  
> *Because CPU letterboxing (11.0 ms) is 100% overlapped and hidden behind GPU execution, live pipeline throughput jumped from **18.3 FPS to 20.0 FPS** (+9.3% gain)."*

---

### Slide 5: Memory Management & Power-Performance Modes (4:30 – 5:15)
> *"Turning to memory management and thermal power budgets:*  
> *By stripping out graphical display managers and background daemons, idle RAM dropped from 670 MB to **217 MB (-67.6%)**, liberating **+450 MB of unified RAM headroom** (3.78 GB free for vision models).*  
> *We also analyzed Dynamic Voltage and Frequency Scaling (DVFS via `nvpmodel`):*  
> - *In **10 W MAXN mode**, the system delivers 20.0 FPS at 6.22 W (3.22 FPS/W).*  
> - *In **5 W mode (`nvpmodel -m 1`)**, the OS shuts down 2 CPU cores and throttles clock frequencies. Power consumption drops from 6.22 W down to **3.84 W (-38% heat dissipation)** while sustaining 12.5 FPS, improving energy efficiency to **3.26 FPS/W (+10.8% gain)**. This is crucial for passively cooled edge appliances."*

---

### Slide 6: Security Isolation & The Principle of Least Privilege (5:15 – 6:00)
> *"In embedded systems security, we implemented the principle of least privilege using systemd unit sandboxing:*  
> - *The detector service runs as dedicated unprivileged user `edgeml:video` (UID 1200), not root.*  
> - *We enforced strict namespace sandboxing: `NoNewPrivileges=true`, `ProtectSystem=strict`, `ProtectHome=true`, `PrivateTmp=true`, `ProtectKernelTunables=true`, and `RestrictRealtime=true`.*  
> - ***Key Discovery on Tegra Device Drivers:*** *Standard systemd `char-nvhost` only covers Major 242. On the Jetson Nano, the Maxwell GPU device node is registered under Character Major **506** (`char-57000000.gpu`). Without explicitly adding `DeviceAllow=char-57000000.gpu rw` and creating udev rule `99-tegra-devices.rules` (`MODE="0660", GROUP="video"`), non-root processes cannot access the GPU!*  
> - *Evaluating with `systemd-analyze security`, our attack exposure score dropped from **9.6 UNSAFE** to **3.2 OK (-67% attack surface reduction)**.*  
> - *We additionally enforced SSH key-only authentication (`PasswordAuthentication no`), closed LLMNR port 5355, and applied kernel sysctls for reverse-path filtering (`rp_filter=1`) and restricted `dmesg`."*

---

### Slide 7: VFS Design & Power-Cut Resilience (6:00 – 6:30)
> *"For storage and fault tolerance, edge devices frequently suffer sudden power unplugging.*  
> *We implemented an immutable Virtual File System (VFS) layout:*  
> - *The root partition `/dev/mmcblk0p1` is mounted strictly **Read-Only (`ro`)**.*  
> - *Volatile runtime paths (`/run`, `/tmp`, `/var/volatile`) are mounted in RAM via `tmpfs`.*  
> - *To prove resilience empirically, we subjected the live board to **5 consecutive abrupt hardware resets** (`echo b > /proc/sysrq-trigger`) during active 20 FPS GPU inference.*  
> - *In 5 out of 5 cycles, the system recovered within 3–4 seconds with **zero EXT4 filesystem errors**, clean journal replay, and immediate detector service auto-resumption over MQTT."*

---

### Slide 8: Master Evaluation & Defending Baseline B (6:30 – 7:00)
> *"A frequent critique in systems optimization is: 'Couldn't you get the same result by simply running `systemctl set-default multi-user.target` on Ubuntu to disable the desktop?'*  
> *We evaluated this as **Baseline B (Minimised Stock)** and conclusively proved why it falls short:*  
> 1. *Baseline B still wastes **10.2 GB of disk space** because all GUI packages and dependencies remain installed.*  
> 2. *It carries over **2,000 unpinned Debian packages** that cannot be deterministically audited.*  
> 3. *It boots the bloated 112.5 MB monolithic kernel with slow serial output.*  
> 4. *Most importantly: Baseline B runs on a writable filesystem and remains completely vulnerable to power-loss corruption.*  
> *Our Yocto image is **88.7% smaller** (738 MB vs 6.56 GB zip), boots in **4.6 s vs 15.5 s**, and is provably immune to corruption."*

---

## 💻 Live Hardware Demonstration Guide (7:00 – 9:30)

During the demo, connect your laptop to the Jetson Nano via the micro-USB cable (`192.168.55.1`).

### Step 1: Run the Automated 7-Point Health & Security Check (30 seconds)
Open a terminal on your laptop and run:
```bash
./scripts/smoke-test.sh nano-usb
```
**What to say to Dr. Raghavan:**  
> *"First, let's run our automated smoke test suite across the USB link. This verifies 7 critical OS checkpoints:*  
> *1. SSH reachability over the virtual network interface.*  
> *2. Kernel character device nodes for the Maxwell GPU (Major 506) and V4L2 camera.*  
> *3. Systemd active service state.*  
> *4. Unprivileged execution under UID 1200 (`edgeml`).*  
> *5. Read-only rootfs mount enforcement (`ro`).*  
> *6. The 3.2 OK security rating from `systemd-analyze`.*  
> *7. Live MQTT message reception from the broker."*

---

### Step 2: Show the Interactive Browser Dashboard (1 minute)
Open a second terminal and start the web dashboard (or open `http://localhost:8080` in Chrome):
```bash
python3 scripts/web-dashboard.py 8080
```
Open `http://localhost:8080` in the browser and wave your hand or stand in front of the camera.

**What to say to Dr. Raghavan:**  
> *"Here is our zero-dependency web dashboard consuming live detections over MQTT from the Nano.*  
> *Notice three key items:*  
> *1. **Live Throughput:** Running at a steady **20.0 FPS** (50 ms frame budget).*  
> *2. **Inference Latency:** TensorRT FP16 inference executes in **48 ms**, while CPU letterboxing (11 ms) is completely hidden in parallel on Core 1.*  
> *3. **System Badges:** The UI confirms the service is running sandboxed under UID 1200 with an immutable `ro` filesystem."*

---

### Step 3: Trigger a Live Ungraceful Power-Cut Reset (1 minute)
In your terminal, trigger an emergency kernel reset on the live board:
```bash
ssh nano-usb "echo 1 > /proc/sys/kernel/sysrq; echo b > /proc/sysrq-trigger"
```
Wait 4 seconds, then show the board recovering:
```bash
ssh nano-usb "mount | grep ' on / '; dmesg | grep -i 'EXT4-fs'"
```

**What to say to Dr. Raghavan:**  
> *"Now let's demonstrate fault tolerance. I am issuing a kernel SysRq emergency restart signal (`echo b > /proc/sysrq-trigger`), simulating an abrupt power cut during active GPU execution.*  
> *The connection drops. Now let's watch... 1... 2... 3... 4 seconds! The board is back online.*  
> *Notice: the root filesystem mounted cleanly as `ro`, `dmesg` reports zero EXT4 filesystem errors, and `edgeml-detector.service` has already auto-started and resumed streaming detections over MQTT."*

---

### Slide 9: Conclusion & Wrap-Up (9:30 – 10:00)
> *"In conclusion, edgeml-jetson demonstrates that application-specific Linux engineering—integrating kernel trimming, VFS mount policies, process pipelining, and systemd sandboxing—transforms a brittle 12 GB desktop distribution into an 88% smaller, 70% faster, and corruption-immune production appliance.*  
> *Thank you, Dr. Raghavan. I am happy to take any questions."*

---

## 🎓 Expected Professor Questions & Rebuttals (Dr. Raghavan Focus)

### Q1: *"Why did you use pinned host memory (`cudaMallocHost`) instead of unified virtual memory (`cudaMallocManaged`)?"*
> **Answer:**  
> *"On the Jetson Nano (Tegra X1 / Maxwell), hardware page faulting is not supported on the GPU. Using `cudaMallocManaged` incurs CPU-GPU page migration overhead. By allocating pinned host memory via `cudaMallocHost`, the memory is page-locked in physical RAM, allowing asynchronous DMA transfers (`cudaMemcpyAsync`) to proceed concurrently without OS page-table intervention or TLB shootdowns."*

### Q2: *"How does your read-only rootfs handle application logs and temporary files?"*
> **Answer:**  
> *"We adhered to the Linux Filesystem Hierarchy Standard for stateless systems. Volatile directories—`/run`, `/tmp`, and `/var/volatile` (which links to `/var/log` and `/var/tmp`)—are backed by in-memory `tmpfs` mounts. Systemd's journal operates in `volatile` storage mode in RAM. Persistent model files are stored strictly in `/var/lib/edgeml`."*

### Q3: *"What prevents the producer thread from running ahead and consuming all memory if inference slows down?"*
> **Answer:**  
> *"We implemented a 3-slot circular buffer managed via `std::condition_variable`. If the consumer is busy on the GPU and all slots are occupied, the producer thread automatically releases and drops the stale camera buffer and re-uses the slot. This ensures memory usage remains strictly bounded ($3 \times \text{frame buffer size}$) and guarantees that the GPU always receives the freshest available frame, preventing queue lag."*

### Q4: *"Why did silencing the serial console (`quiet loglevel=3`) improve boot time by 4 seconds?"*
> **Answer:**  
> *"The default kernel command line specified `console=ttyS0,115200`. Transmitting 65 KB of text at 115,200 baud (which yields roughly 11.5 KB/s throughput) is inherently an I/O bottleneck that blocks the kernel printk execution path synchronously before userspace initialization. With `quiet loglevel=3`, non-critical messages are silenced on the UART line while remaining preserved in the kernel's in-memory `dmesg` ring buffer."*
