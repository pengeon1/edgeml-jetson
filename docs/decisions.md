# Decision log

Newest first. Each entry says what was decided, why, and what was rejected.

## 2026-11-02: CUDA stack comes from meta-tegra recipes and NVIDIA's public Jetson feed

The pinned meta-tegra branch has recipes for the stack the Nano needs: CUDA 10.2 (`cuda-cudart`, `libcublas`, `cuda-nvrtc` and others), cuDNN 8.2.1.32 and TensorRT 8.2.1 (`tensorrt-core`, `tensorrt-plugins-prebuilt`, `tensorrt-trtexec-prebuilt`). How the files are fetched:

- cuDNN and TensorRT use the `l4t_deb_pkgfeed` class, whose default feed is NVIDIA's public Jetson repository (`https://repo.download.nvidia.com/jetson`). No NVIDIA login is needed.
- CUDA 10.2 recipes use the same class but default `L4T_DEB_FEED_BASE` to `file://`. Tested from the build host with `curl -I`: `cuda-cudart-10-2_10.2.300-1_arm64.deb`, `libcudnn8_8.2.1.32-1+cuda10.2_arm64.deb` and `libnvinfer8_8.2.1-1+cuda10.2_arm64.deb` all return HTTP 200 from `https://repo.download.nvidia.com/jetson/common/pool/main/`. So the CUDA packages are downloadable without a login too, and `kas/edgeml-cuda.yml` sets `L4T_DEB_FEED_BASE` to the public feed explicitly.
- `NVIDIA_DEVNET_MIRROR` is defined by `nvidia_devnet_downloads.bbclass`, but no recipe on this branch inherits that class, so it is not needed here.
- Runtime image set: `cuda-cudart`, `libcublas`, `cudnn`, `tensorrt-core`, `tensorrt-plugins-prebuilt` and `tensorrt-trtexec-prebuilt`. The `-dev`, samples and documentation packages stay out of the runtime image, which is where most of the stock image's size goes.
- The machine already carries the `cuda` override and prefers `tensorrt-plugins-prebuilt` and `tensorrt-trtexec-prebuilt`, so nothing is compiled with CUDA (which would need gcc 8 and the host-side CUDA tools).
- The TensorRT recipes require the `opengl` distro feature, which poky enables by default. This may pull in graphics libraries, so image size is checked after the build.

Rejected: running NVIDIA SDK Manager, because it does not offer JetPack 4.x on an Ubuntu 22.04 host and is not needed now. The trimmed L4T rootfs remains the fallback if CUDA integration under Yocto fails.

## 2026-11-02: boot time and RAM are read from systemd and `/proc/meminfo`

Our minimal image has no `systemd-analyze`, no `sudo`, no `dpkg` and a BusyBox userland. Boot time comes from `systemctl show` timestamps, and RAM from `/proc/meminfo`. The scripts use portable commands (`sed -n`, not `head -N`).

## 2026-11-01: development image keeps convenience features until hardening

The first image had no way in (no SSH, no network, no modules). The development image adds OpenSSH, Avahi, USB device-mode networking, `kernel-modules` and an empty root password (`debug-tweaks`). The hardening stage removes the empty password and shell conveniences, adds key-only SSH and a firewall, and trims the module set. Rejected: serial-only access, because there is no USB-serial adapter.

## 2026-11-01: a second SD card for our image

Our image uses a second, identical SanDisk 64 GB A1 card so the stock card stays untouched for later comparisons, such as a minimised stock baseline. Flashing rewrites the shared QSPI bootloader, so stock booting is to be confirmed.

## 2026-11-01: pin layers by commit

All three layers are pinned to the commits that built successfully, so the build can be reproduced later. Using bare branch names would pick up later commits.

| Layer | Branch | Commit |
| --- | --- | --- |
| poky | kirkstone | `445a6223929b9a7a62b575093659e3d9e1aba982` |
| meta-openembedded | kirkstone | `ce8539c941f6fcbecaca4d16640ac105c0595589` |
| meta-tegra | kirkstone-l4t-r32.7.x | `94e3db3146dc273ec1df463426c0fcaeacc51b5f` |

## 2026-11-01: meta-tegra branch `kirkstone-l4t-r32.7.x`

The Nano's last supported release is L4T R32.7.x (JetPack 4.6.x). meta-tegra supports it on the `kirkstone-l4t-r32.7.x` and `dunfell` branches. Kirkstone was chosen because it is newer and builds on the Ubuntu 22.04 host. The machine is `jetson-nano-devkit` (formerly `jetson-nano-qspi-sd`). This builds L4T R32.7.6, newer than the stock image's R32.7.1, which the report must state.

## 2026-11-01: model export with `--simplify`

YOLOv5n exported with PyTorch 2.x failed to parse in TensorRT 8.2 on the Nano (a `Resize` node computing a shape tensor). Re-exporting with `--simplify` (onnx-simplifier) at opset 12 and a fixed 640x640 input fixed it. The export recipe is kept so the model can be reproduced.

## 2026-11-01: TensorRT engine built on the device, once

The engine takes about 11 minutes to build on the Nano and depends on the TensorRT version and GPU. The image will build it on first run and store it on a writable data partition, instead of rebuilding at each boot.

## 2026-11-01: build system is Yocto with meta-tegra

| Option | Verdict |
| --- | --- |
| Yocto + meta-tegra | Chosen. Smallest image, scripted and pinned build, per-package licence manifest, community support for the Nano |
| Trimmed L4T rootfs (NVIDIA flash tools) | Kept as the fallback if CUDA integration under Yocto fails. It uses NVIDIA's own flow and packages |
| Buildroot | Rejected: no maintained Nano or CUDA support |
| Debian live-build | Rejected: not suitable for Tegra boards |

## 2026-11-01: Track A on the original Jetson Nano 4 GB

The board is a Jetson Nano Developer Kit (P3450, rev A02). It is stuck on JetPack 4.6.x (kernel 4.9, CUDA 10.2, TensorRT 8.2), which constrains tool choices and strengthens the case against the stock desktop image.
