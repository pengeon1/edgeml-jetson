# edgeml-jetson

An application-specific Linux distribution for **edge ML inference on the NVIDIA Jetson Nano**, built with Yocto (meta-tegra) and compared against stock JetPack. This is **Track A** of the "Application-Specific Linux Distribution for ML, IoT, CUDA and FPGA Platforms" assignment.

**Goal:** a headless, reproducible, read-only Linux image that boots straight into a camera → TensorRT object detector → MQTT service, with a measured comparison against stock JetPack on image size, RAM, boot time, package count, security exposure and inference performance.

## Status (updated 2 November 2026)

| Milestone | State |
| --- | --- |
| Requirements and plan | Done |
| Stock JetPack baseline (size, boot, RAM, power, inference) | Done |
| Yocto build for the Nano (no CUDA) | Done |
| Flash and first boot of our image, SSH over USB | Done |
| CUDA, cuDNN and TensorRT in the image (`kas/edgeml-cuda.yml`) | Done |
| 5-run benchmark and power on our image | Done (same speed and power as stock) |
| Detector service with camera and MQTT (`meta-edgeml`, `edgeml-detector`) | Done: starts at boot, detections reach the laptop broker |
| Kernel trimming (before and after numbers) | Next |
| Clock fixed and LLMNR (port 5355) closed (`meta-edgeml`) | Done |
| Read-only root, hardening, auto-start service | To do |
| Final benchmarks, report, demo video | To do |

## Hardware and host

| Item | Details |
| --- | --- |
| Board | Jetson Nano Developer Kit (P3450, rev A02, 4 GB), heatsink only, no fan |
| Storage | Two identical SanDisk 64 GB A1 microSD cards: one with stock JetPack, one for our image |
| Camera | Logitech C270 USB webcam (UVC) |
| Build host | Dell G15 5530, Ubuntu 22.04, Core i5-13450HX, 16 GB RAM |
| Stock baseline | JetPack 4.6.1 (L4T R32.7.1, kernel 4.9.253, Ubuntu 18.04) |
| Our image | Poky 4.0 (kirkstone) with meta-tegra L4T R32.7.6 (kernel 4.9.337) |

Layers are pinned by commit in `kas/edgeml-bsp.yml` and `kas/edgeml-dev.yml`:

| Layer | Branch | Commit |
| --- | --- | --- |
| poky | kirkstone | `445a6223929b9a7a62b575093659e3d9e1aba982` |
| meta-openembedded | kirkstone | `ce8539c941f6fcbecaca4d16640ac105c0595589` |
| meta-tegra | kirkstone-l4t-r32.7.x | `94e3db3146dc273ec1df463426c0fcaeacc51b5f` |

## Results so far

### Stock JetPack 4.6.1 baseline

| Metric | Value |
| --- | --- |
| Compressed image (official zip) | 6.56 GB |
| Used root filesystem | 12 GB |
| Installed packages | 2351 |
| Running services | 39 |
| Boot, kernel start to graphical.target | 15.5 s |
| RAM in use at idle (total minus available) | 670 MB |
| Idle power (module input rail) | about 1.47 W |
| YOLOv5n 640x640 FP16, TensorRT 8.2.1, MAXN | 22.16 ± 0.02 inferences/s, 45.12 ± 0.04 ms mean latency (5 runs) |
| Power during inference | 6.41 W (module input rail), 3.46 FPS per watt |
| GPU clock and temperature | Held at 921 MHz, peak 43.75 °C, no throttling |

### Our CUDA image versus stock JetPack 4.6.1

Same Nano, same SD card model, same engine file (YOLOv5n FP16, 640x640), MAXN with `jetson_clocks`, 5 runs of 30 s, mean ± sample SD. Power is the module input rail averaged while GPU load is at least 90%.

| Metric | Stock | Our image | Change |
| --- | --- | --- | --- |
| Used root filesystem | 12 GB | 1.4 GB (with CUDA 10.2, cuDNN 8.2.1, TensorRT 8.2.1 runtime) | 88% less |
| Boot, kernel start to boot finished | 15.5 s | 8.9 s | 43% faster |
| RAM in use at idle | 670 MB | 217 MB | 68% less |
| Running services | 39 | 14 | 64% fewer |
| Listening sockets | 8 | 3 (SSH, plus two DNS stubs bound to localhost) | 5 fewer; only SSH is reachable from outside |
| Kernel image | 34.5 MB | 38.5 MB | 12% larger (untrimmed) |
| Kernel modules | 78 MB | 85.2 MB | 9% larger (untrimmed) |
| TensorRT throughput | 22.16 ± 0.021 inferences/s | 22.22 ± 0.037 inferences/s | same, within 0.3% |
| Latency, 99th percentile | 45.26 ± 0.023 ms | 45.14 ± 0.089 ms | same |
| Power while busy | 6.41 W | 6.41 W | same |
| Efficiency | 3.46 FPS/W | 3.47 FPS/W | same |
| Peak temperature | 43.75 °C | 42.75 °C | 1 °C lower |

Reading the table: the image is 88% smaller than stock (the assignment asks for at least 40%) and inference speed and power are unchanged, so the savings cost nothing in performance. Run 1 of our benchmark was the fastest (22.28); without it the mean is 22.20, so claim parity, not a speedup. The kernel is not trimmed yet, so kernel size is the next place to gain. The RAM figure was taken 32 s after boot. Raw logs are in `results/stock/` and `results/cuda-image/`.

### Detector service on our image (webcam to MQTT)

Measured on the Nano with the service running at boot, a person in front of the Logitech C270 (640x480), engine `yolov5n_fp16.engine`, MQTT broker on the laptop.

| Metric | Value |
| --- | --- |
| End-to-end rate | 18.1 frames/s |
| Preprocessing (CPU, YUYV to RGB and letterbox) | 9.5 ms |
| GPU inference | 45.0 ms |
| Post-processing and MQTT publish | 0.7 ms |
| Capture to publish latency | about 105 ms |
| RAM in use with the service running | about 1.15 GB of 4 GB (217 MB idle) |
| Power while the GPU is busy | 6.29 W (module input rail) |
| Efficiency | 2.88 FPS/W |
| Peak temperature | 50.5 °C, GPU held at 921 MHz |

The rate is below the 22.2 inferences/s of the plain `trtexec` benchmark because preprocessing and inference run one after the other. Overlapping them is the planned optimisation.

### Whole system with the detector running

Camera, YOLOv5n FP16 engine, MQTT publish to the laptop; person in front of the camera; 108 one-second samples of `tegrastats` (all samples counted, because the detector keeps the GPU about 80% busy rather than above 90%).

| Metric | Value |
| --- | --- |
| End-to-end rate | 18.1 frames/s (camera 30 fps; preprocessing and inference run one after the other) |
| Time per frame | preprocessing 9.4 ms (CPU), inference 45.0 ms (GPU), post-processing and MQTT under 1 ms |
| Capture to publish latency | about 105 ms |
| Power, module input rail | 6.22 W, 2.91 frames/s per watt |
| CPU load | about 12% per core on average (0.46 of one core in total) |
| RAM in use | about 1.15 GB (MemTotal minus MemAvailable; CUDA, cuDNN and TensorRT libraries, engine, camera buffers) |
| GPU clock, peak temperature | 921 MHz, 50.5 °C |

Stock was not measured with the same workload, so only the idle figures (670 MB stock, 217 MB ours) are compared directly. The frame rate is below the 22 inferences/s of `trtexec` because the program does not overlap preprocessing with inference yet.

## Repository layout

```
kas/             Build configurations (pinned layers, image settings)
meta-edgeml/     Our own Yocto layer (system configuration, later the detector service)
scripts/         Build, flash, measurement and summary scripts
docs/            Build and flash guide, measurement method, decision log
results/         Raw measurement logs (stock/ and ours/)
README.md        This file
```

Directories created by the build (`build/`, `poky/`, `meta-openembedded/`, `meta-tegra/`) are ignored by Git. NVIDIA downloads are never committed.

### Scripts

| Script | Runs on | What it does |
| --- | --- | --- |
| `scripts/build.sh` | Laptop | Builds the image with kas from `kas/edgeml-dev.yml` and lists the flashing package |
| `scripts/flash.sh` | Laptop | Checks that the Nano is in recovery mode, unpacks the flashing package into a clean folder and runs `doflash.sh` |
| `scripts/measure-stock.sh` | Nano (stock JetPack) | Idle baseline: boot, RAM, disk, packages, services, ports, kernel size |
| `scripts/measure-image.sh` | Nano (our image) | The same measurements using BusyBox-safe commands |
| `scripts/summarize-measure.sh` | Laptop | Prints headline numbers (boot, RAM, services, disk) from either measurement file |
| `scripts/bench-trtexec.sh` | Nano | Fixes the clocks, logs power, runs `trtexec` several times |
| `scripts/summarize-runs.sh` | Laptop or Nano | Mean ± standard deviation of throughput and latency over the runs |
| `scripts/summarize-power.sh` | Laptop or Nano | Average power while the GPU is busy (or all samples with a third argument of 0), GPU clocks, peak temperature, FPS per watt |

## Reproduce the build

On an Ubuntu 22.04 host, outside any Python virtual environment:

```
sudo apt install -y gawk wget git diffstat unzip texinfo gcc build-essential chrpath socat cpio \
  python3 python3-pip python3-pexpect xz-utils debianutils iputils-ping python3-git python3-jinja2 \
  libegl1-mesa libsdl1.2-dev python3-subunit mesa-common-dev zstd liblz4-tool lz4 file locales libacl1
pip3 install --user kas
scripts/build.sh            # builds kas/edgeml-dev.yml
```

Flashing and first login are in [docs/build-and-flash.md](docs/build-and-flash.md).

## How we measure

- **Boot time:** seconds from kernel start to boot finished, from `systemd-analyze` on stock and from the `systemctl show` timestamps on our image. The "Startup finished" total on stock is inflated by background jobs such as `apt-daily`, so it is not used.
- **RAM:** `MemTotal` minus `MemAvailable`, after the system has been idle for several minutes.
- **Inference:** `trtexec` on the same FP16 engine, `nvpmodel` MAXN with `jetson_clocks`, 30 s per run, 5 runs, mean ± standard deviation (`scripts/bench-trtexec.sh`, `scripts/summarize-runs.sh`).
- **Power:** `tegrastats` module input rail (`POM_5V_IN`), averaged only while the GPU is busy (`scripts/summarize-power.sh`).
- **Same hardware for every comparison:** same board, SD card model, model file and clocks.

## Licences and proprietary components

- NVIDIA L4T BSP, CUDA, cuDNN and TensorRT are proprietary and will be listed with their justification in the report. They are not stored in this repository.
- YOLOv5 code and weights are AGPL-3.0.
- Everything else comes from the Yocto Project and OpenEmbedded layers under their own open-source licences. The build produces a per-package licence manifest.

## Progress log

### 2026-11-02 (detector service)
- New recipe `edgeml-detector` in `meta-edgeml`: a C++ program (V4L2 capture, TensorRT inference, a small built-in MQTT client) and `edgeml-detector.service`, enabled at boot. Settings are in `/etc/edgeml/detector.conf`; the engine file lives in `/var/lib/edgeml/`. Broker: Mosquitto on the laptop, reached over the USB network (192.168.55.100).
- Tested on the board: detections of `person` arrive on `edgeml/detections` as JSON. The service starts by itself after a reboot and connects to the broker. Numbers are in the table above.
- Seen: without the engine file the service stops after five failed starts (by design, `StartLimitBurst`); copy the engine, then `systemctl reset-failed edgeml-detector && systemctl restart edgeml-detector`. A manual run while the service holds the camera fails with `Device or resource busy`.
- Next: kernel trimming, then read-only root and hardening, then the report.

### 2026-11-02 (detector service)
- New recipe `edgeml-detector` in `meta-edgeml`: a C++ program that reads the webcam through V4L2 (YUYV 640x480), letterboxes each frame to 640x640 on the CPU, runs the YOLOv5n FP16 TensorRT engine, decodes and filters the boxes (confidence 0.35, NMS 0.45) and publishes JSON over MQTT to `edgeml/detections`. It has its own small MQTT 3.1.1 publisher, so no extra library is in the image. A systemd unit starts it at boot; settings are in `/etc/edgeml/detector.conf`; the engine file lives in `/var/lib/edgeml/`.
- Tested on the board: detections of a person reached `mosquitto_sub` on the laptop (36 to 49% confidence), about 5,500 frames in one run. After a reboot the service started by itself and connected to the broker.
- Numbers are in the table "Whole system with the detector running". Power is 6.22 W at 18.1 frames/s.
- Found: the service fails five times if the engine file is not there at first boot and then stops (start limit). After copying the engine run `systemctl reset-failed edgeml-detector && systemctl restart edgeml-detector`. A manual run while the service is active fails with "Device or resource busy" because the camera is exclusive.
- Found: BusyBox has no `pkill`, so `bench-trtexec.sh` left `tegrastats` running; it now stops it by PID. The earlier benchmark numbers are not affected (idle samples are filtered out). `summarize-power.sh` got a third argument, the minimum GPU load (0 counts every sample).

### 2026-11-02 (clock and port 5355)
- New layer `meta-edgeml` with the recipe `edgeml-config`: wired Ethernet with DHCP (so `systemd-timesyncd` gets network time) and a `systemd-resolved` drop-in with `LLMNR=no` and `MulticastDNS=no`. It is listed in `kas/edgeml-cuda.yml` (a `repos:` entry with no URL refers to this repository) and installed through `IMAGE_INSTALL`.
- Cause of the wrong clock: Yocto sets file dates from the metadata commit date (December 2023) and the Nano has no battery clock, so without network time the board starts in 2023.
- Tested by sharing the laptop's internet (phone hotspot) to the Nano over a USB Ethernet adapter (NetworkManager `ipv4.method shared`). Result: the Nano got 10.42.0.254 on `eth0`, the date was correct within a minute of login, and port 5355 is gone. The only external listener left is SSH (port 22).
- The `fdtput: command not found` warning from the flash helper remains unexplained (`device-tree-compiler` is installed on the laptop). It does not stop the flash.

### 2026-11-02 (benchmark on the CUDA image)
- The first CUDA image had no `nvpmodel`, `jetson_clocks`, `tegrastats` or `bash`, so the clocks could not be fixed and power could not be logged. Added `tegra-tools` and `tegra-nvpmodel` to `kas/edgeml-cuda.yml` (jetson_clocks pulls in bash), rebuilt and re-flashed.
- Five-run benchmark with the stock engine: 22.22 ± 0.037 inferences/s, p99 45.14 ± 0.089 ms, 6.41 W while busy, 3.47 FPS/W, GPU at 921 MHz, peak 42.75 °C. Stock: 22.16 ± 0.021, 45.26 ± 0.023 ms, 6.41 W, 3.46 FPS/W. Parity.
- Re-measured on this image: boot 8.9 s, RAM 217 MB, 14 services, 5 listening sockets, 1.4 GB used root filesystem. Logs in `results/cuda-image/`.
- Next: trim the kernel, add the detector service (camera and MQTT), read-only root and hardening, clock fix, close port 5355.

### 2026-11-02 (CUDA image)
- Added `kas/edgeml-cuda.yml` (dev image plus `L4T_DEB_FEED_BASE` and the runtime packages cuda-cudart, libcublas, cudnn, tensorrt-core, tensorrt-plugins-prebuilt, tensorrt-trtexec-prebuilt). The build downloaded everything from NVIDIA's public feed without a login. The manifest lists 781 packages including `tegra-libraries-cuda`.
- Flashed it. Used root filesystem is 1.4 GB (13 GB partition), against 12 GB on stock.
- The stock `yolov5n_fp16.engine` (TensorRT 8.2.1) loads and runs unchanged on our image: 22.127 inferences/s, mean latency 45.18 ms, GPU compute 43.88 ms (stock: 22.16, 45.12 ms, 43.83 ms). The 99th percentile of 68.8 ms comes from a single short run without fixed clocks; the 5-run benchmark will replace it.
- Stock inference logs and summaries are now in `results/stock/`.
- Fixes: `scripts/flash.sh` now removes the unpack folder with sudo (a previous sudo flash leaves root-owned files). On this image root's home is `/home/root`, so copy files with `scp FILE nano-usb:`. Libraries live in `/usr/lib`.
- Known: the flash helper prints `fdtput: command not found`; the flash still works.

### 2026-11-02 (later)
- Read the pinned meta-tegra recipes for the CUDA stack. The branch has recipes for CUDA 10.2, cuDNN 8.2.1.32 and TensorRT 8.2.1, matching the Nano's JetPack 4.6.x. The `NVIDIA_DEVNET_MIRROR` mechanism exists in the layer but no recipe on this branch uses it.
- cuDNN and TensorRT download from NVIDIA's public Jetson package feed (`https://repo.download.nvidia.com/jetson`), so they need no login. The CUDA 10.2 recipes default their feed to a local `file://` path, but a `curl -I` test from the build host shows the CUDA, cuDNN and TensorRT packages are all served by the public feed (HTTP 200), so no login or local copy is needed.
- `tensorrt-trtexec-prebuilt` installs `trtexec` to `/usr/src/tensorrt/bin`, the same place as on stock JetPack, so the benchmark script works unchanged.

### 2026-11-02
- First flashed image boots and accepts SSH over the USB network. It reaches "boot finished" in 8.9 s against 15.5 s on stock, uses 205 MB of RAM against 670 MB, and runs 14 services against 39. The GPU device nodes appear.
- Found: about 6.1 s of the boot passes before systemd starts (stock: 2.3 s), the clock is wrong without network time, and LLMNR port 5355 is open. All three are on the to-do list.
- Added scripts, the build and flash guide, and this README.

### 2026-11-01
- Requirements, build-system comparison and plan written.
- Stock JetPack 4.6.1 baseline measured: size, boot, RAM, services, ports, power.
- YOLOv5n exported to ONNX. The first export failed in TensorRT 8.2 (Resize node), and re-exporting with `--simplify` fixed it.
- Inference baseline: 22.16 ± 0.02 inferences/s, 45.12 ± 0.04 ms, 6.41 W, no throttling.
- First Yocto build finished (kirkstone, meta-tegra L4T R32.7.x), then a development image with SSH, USB networking and kernel modules.
- Flashed the Nano's second SD card.
