# Release v1.0.0: EdgeML Jetson Nano Production OS

Production-grade, reproducible, read-only Yocto Linux appliance engineered from source for the **NVIDIA Jetson Nano Developer Kit** (4 GB, Maxwell GPU, Model P3450 Rev A02). 

This release fulfills all requirements for **Track A** of the *Application-Specific Linux Distribution for ML, IoT, CUDA and FPGA Platforms* assignment.

---

## 🚀 Key Highlights & Benchmarks

| Metric | Stock JetPack 4.6.1 | Minimised Stock (B) | **EdgeML OS (v1.0.0)** | Improvement vs Stock |
| :--- | :--- | :--- | :--- | :--- |
| **Flashing Archive** | 6.56 GB (zip) | 5.80 GB (tar.gz) | **738 MB** (tegraflash) | **-88.7% smaller** |
| **Root Filesystem** | 12.0 GB | 10.2 GB | **1.4 GB** (ext4) | **-88.3% reduction** |
| **Installed Packages**| 2,351 pkgs | ~2,050 pkgs | **781 pkgs** | **-66.8% fewer pkgs** |
| **Total Boot Time** | 15.5 s | 11.2 s | **4.6 s** | **-70.3% faster** |
| **Kernel Handover** | 2.3 s | 2.3 s | **1.87 s** | **-18.7% faster** |
| **Idle RAM in Use** | 670 MB | 510 MB | **217 MB** | **-67.6% less RAM** |
| **Unified RAM Free** | 3.33 GB | 3.45 GB | **3.78 GB** | **+450 MB ML headroom** |
| **Kernel Storage** | 112.5 MB | 112.5 MB | **80.6 MB** | **-28.4% smaller** (-625 options) |
| **Live Pipeline FPS** | N/A | N/A | **20.0 FPS** (pipelined) | Overlapped CPU letterboxing |
| **Energy Efficiency** | 3.46 FPS/W | 3.46 FPS/W | **3.26 FPS/W** (5 W mode) | 3.84 W power draw |
| **Security Exposure** | 9.6 UNSAFE | 9.2 UNSAFE | **3.2 OK** (systemd) | **-66.7% exposure** (UID 1200) |
| **Power-Cut Resilience**| Vulnerable (`rw`) | Vulnerable (`rw`) | **Immune (`ro`)** | **5/5 ungraceful resets passed** |

---

## 📦 Release Assets & Checksum

- **Asset:** `core-image-minimal-jetson-nano-devkit.tegraflash.tar.gz` (738 MB)
- **Target Machine:** `jetson-nano-devkit` (P3450 / Tegra210)
- **SHA-256 Checksum:**
  ```text
  703ec07a87d8e3bee514b99809e690e7ec98028cb9c2a526afdddb9bbfbb8f22
  ```

---

## ⚡ How to Flash

1. Put your Jetson Nano into **Force Recovery Mode** (fit a jumper across the `FRC` and `GND` pins on the button header before powering on).
2. Connect the micro-USB data cable and 5V 4A barrel jack power supply.
3. On your Ubuntu host machine, clone the repository and execute:
   ```bash
   git clone https://github.com/pengeon1/edgeml-jetson.git
   cd edgeml-jetson
   ./scripts/flash.sh
   ```
4. Remove the recovery jumper and power cycle the board.

---

## 🖥️ Live Telemetry & Visualizers

- **Interactive Web Dashboard:**
  ```bash
  python3 scripts/web-dashboard.py 8080
  # Open http://localhost:8080 in your browser
  ```
- **Terminal ASCII Dashboard:**
  ```bash
  python3 scripts/demo-dashboard.py
  ```
- **Automated Smoke Test:**
  ```bash
  ./scripts/smoke-test.sh nano-usb
  ```
