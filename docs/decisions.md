# Decision log

Newest first. Each entry says what was decided, why, and what was rejected.

## 2026-11-06: hardening and read-only rootfs (systemd sandboxing, udev rules for GPU, SSH key-only, sysctl)

- **Service sandboxing:** `edgeml-detector.service` runs as an unprivileged dedicated system user (`edgeml:video`, UID 1200) instead of root. Hardened with `NoNewPrivileges=true`, `ProtectSystem=strict`, `ProtectHome=true`, `PrivateTmp=true`, `ProtectKernelTunables=true`, `ProtectKernelModules=true`, `ProtectControlGroups=true`, `RestrictRealtime=true`, `RestrictSUIDSGID=true`, `RestrictAddressFamilies=AF_UNIX AF_INET`, and `DevicePolicy=closed`. `systemd-analyze security edgeml-detector` dropped the exposure rating from **9.6 UNSAFE** to **3.2 OK** (67% reduction) while maintaining full 18.2 FPS inference throughput and MQTT publishing.
- **NVIDIA GPU device node and major 506 permissions:** In systemd's `DeviceAllow=`, `char-nvhost` only matches Major 242 (`/dev/nvhost-*`), which is insufficient for CUDA and TensorRT. On Jetson Nano (T210 / Maxwell), the primary GPU character device node is `char-57000000.gpu` (Major 506). Adding `DeviceAllow=char-57000000.gpu rw` is mandatory for the CUDA runtime to detect the GPU in sandboxed units. Furthermore, on minimal rootfs, `/dev/nvhost*` and `/dev/nvmap` default to `0600 root:root`. Installed `99-tegra-devices.rules` (`KERNEL=="nvhost*|nvmap", MODE="0660", GROUP="video"`) to grant the `video` group access without running as root.
- **Yocto useradd syntax:** When creating a dedicated user and group of the same name in Yocto recipes (`USERADD_PARAM`), `-g <group>` must be explicitly specified so `useradd` does not attempt to create a duplicate group and fail the build.
- **SSH hardening:** Password authentication is disabled entirely (`PasswordAuthentication no`, `PermitEmptyPasswords no`) and `PermitRootLogin prohibit-password` is enforced via an OpenSSH bbappend. The host public key is installed to `/home/root/.ssh/authorized_keys` with mode `0600`. Tested on the board: public key authentication succeeds immediately, while password login is rejected (`Permission denied (publickey)`).
- **Sysctl kernel hardening:** Packaged in `/etc/sysctl.d/99-edgeml-security.conf`: restricted dmesg access (`kernel.dmesg_restrict = 1`), hidden kernel pointers (`kernel.kptr_restrict = 2`), strict reverse path filtering against IP spoofing (`net.ipv4.conf.all.rp_filter = 1`), and disabled ICMP redirects.
- **Read-only rootfs:** Enabled `IMAGE_FEATURES += "read-only-rootfs"` in `kas/edgeml-cuda.yml`. Volatile data goes to tmpfs (`/var/volatile`), and model storage lives in `/var/lib/edgeml`. Remounting `/` as `ro` verified on live hardware: writes to system paths (`/usr`, `/etc`) are blocked while the detector runs uninterrupted.

## 2026-11-06: silence the serial console during boot, then trim the kernel from the real configuration

- **Console:** with the default command line (`console=ttyS0,115200n8` plus `earlyprintk`) the kernel's 65 KB of boot messages go out at about 11 KB/s, which holds up boot by several seconds. `quiet loglevel=3` leaves only errors on the console; nothing is lost because `dmesg` still has the whole log. Measured on the board: userspace starts at 1.9 s instead of 6.1 s, boot finishes at 4.6 s instead of 8.9 s. Set in the build through `UBOOT_EXTLINUX_KERNEL_ARGS`. Rejected: removing `console=ttyS0` entirely, because the serial console is the recovery path if the network is down.
- **Kernel trim method:** `linux-tegra` already accepts configuration fragments, so `edgeml-trim.cfg` (only `# CONFIG_X is not set` lines) is added by a bbappend instead of replacing `tegra_defconfig`. Every symbol in it was checked against the board's real configuration. Dependent options disappear with their parent (for example everything under `CONFIG_BT`). If another enabled option selects one of ours, the build keeps it and `kernel_configcheck` warns; `results/kernel/config-after.txt` records what really ended up off.
- **Kept deliberately:** Wi-Fi for the Intel 8265 card, Realtek Ethernet (PCIe and USB adapters), the USB device-mode network used for SSH, uvcvideo, overlayfs (planned read-only root), debugfs (tegrastats and the NVIDIA drivers use it), netfilter (planned firewall), device-tree and nvhost camera plumbing (removal is riskier than its size gain).
- **Not in this iteration:** display (DRM, framebuffer), the USB gadget function drivers, and compile-time options such as the stack protector (hardening step).
- **Check the trim before building it:** a kernel build takes about 30 minutes, so the fragment is first applied to the real `tegra_defconfig` with `make alldefconfig` on the kernel source (set `KERNEL_OVERLAYS` to the `nvidia` and `nvidia/nvgpu` directories). That run reproduces the board's own configuration, so it shows every option the trim drops or changes indirectly through `select` and `depends on`. It found, before any build: `DEBUG_FS` (needed by NVIDIA's cpufreq code, which failed to compile once `DEBUG_KMEMLEAK` stopped selecting it), SCSI and USB storage (selected by `ATA`), STAGING and the INA3221 power sensor (selected by `CAN`), and 47 options that would have moved from built-in to modules (the USB core among them). Kept on, or pinned, as a result.
- **Out-of-tree vendor Kconfig gaps (SHIELD accessory audio):** Turning off `CONFIG_SOUND` exposed a missing dependency in NVIDIA's `nvidia/drivers/hid/Kconfig`, where `CONFIG_HID_SHIELD_REMOTE` compiles `hid-jarvis-remote.c` (Shield TV voice remote) that calls ALSA functions without `depends on SND`. Disabling `CONFIG_HID_SHIELD_REMOTE`, `CONFIG_HID_SHIELD_BLAKE`, and `CONFIG_HID_NVIDIA_STAND` cleanly resolved modpost linking errors.
- **If boot breaks:** recovery is a normal re-flash; the previous known-good configuration is `results/kernel/config-before.txt`.

## 2026-11-02: the detector is a C++ program with its own MQTT client, broker on the laptop

- **Why C++ and not Python:** the image has no Python, and the TensorRT Python bindings for JetPack 4 target Python 3.6, which kirkstone does not have. The C++ API uses the same `libnvinfer` that `trtexec` uses, and the program adds only a few MB to the image.
- **MQTT client:** about 100 lines (CONNECT, then QoS 0 PUBLISH, keep-alive off, reconnect every 3 s). It avoids adding libmosquitto and its dependencies, and a lost broker never blocks the inference loop (connect uses a 1 s timeout and retries at most every 3 s). It cannot subscribe, which the detector does not need.
- **Broker:** Mosquitto runs on the laptop (`192.168.55.100` on the USB link, `10.42.0.1` with Ethernet sharing), so the image carries no broker. Anonymous access is enabled for the lab demo and is to be tightened in the hardening step.
- **Camera:** YUYV 640x480, four memory-mapped buffers, always the newest frame (older ones are given back) so latency does not build up; `exposure_auto_priority=0` so dim light does not halve the frame rate.
- **Builds without nvcc:** the program only needs the CUDA runtime headers and `libcudart`, so the recipe uses `cuda-cudart`, `cuda-nvcc-headers`, `tensorrt-core` directly and never inherits the `cuda` class (which would pull in the CUDA compiler and host gcc 8).
- **Engine file:** built on the board with `trtexec` (about 11 minutes) and copied to `/var/lib/edgeml/`. It is not in the repository because it is tied to the board's GPU and TensorRT version. A build-from-ONNX helper comes with the final image.
- **Known limit:** preprocessing (9.4 ms on the CPU) runs before inference instead of overlapping it, which costs about 4 fps. To do: double-buffer the input, or move the conversion to the GPU.

## 2026-11-02: detector is a C++ program with its own minimal MQTT client; engine and broker stay outside the image

- **C++, not Python:** the image has no Python, and the TensorRT Python bindings of JetPack 4 target Python 3.6, while Yocto kirkstone ships 3.10. A C++ program links directly to `libnvinfer` and `libcudart` and adds almost nothing to the image.
- **Own MQTT client:** the program only needs CONNECT and QoS 0 PUBLISH (about 80 lines), so it avoids a library dependency. The program reconnects every 3 s without stalling the inference loop. Tested against a fake broker.
- **Engine file outside the image:** the TensorRT engine is built on the device for its GPU and TensorRT version (about 11 minutes), so it is stored in `/var/lib/edgeml/` and not in the image. Later it will live on a writable `/data` partition when the root becomes read-only. The ONNX model comes from Ultralytics YOLOv5 (AGPL-3.0), which goes in the licence list.
- **Broker on the laptop:** keeps the image small and makes the demo easy to show. Anonymous access is acceptable on the private USB link and will be tightened in the hardening step.
- **Runs as root for now.** A dedicated user in the `video` group and systemd sandbox options come with the hardening step.
- **Newest frame only:** the capture loop drops older queued frames, so latency does not grow when inference is slower than the camera.

## 2026-11-02: our own configuration lives in a project layer, `meta-edgeml`

Settings that are not packages (network, resolver) go into a layer inside this repository instead of `local_conf`, so they are versioned and the build stays reproducible. kas includes it with a `repos:` entry that has no URL.

- **Clock:** the Nano has no battery clock and Yocto dates files from the metadata commit (December 2023). `systemd-timesyncd` was already in the image but had no route to the internet, because the USB network (192.168.55.1) does not reach it. `edgeml-config` brings the wired port up with DHCP so the router (or the laptop sharing its internet) provides addresses and NTP servers. Without network time the board shows the 2023 date; the saved-time fix comes with the read-only root (a writable `/var/lib/systemd/timesync`).
- **Port 5355:** LLMNR was listening on all interfaces. The image does not use LLMNR, so `LLMNR=no` in a `resolved.conf.d` drop-in closes it. `MulticastDNS=no` leaves mDNS to avahi, which provides `.local` names.
- Result on the board: SSH is the only external listener (two DNS stubs listen on localhost only).

Rejected: chrony or ntpd (adds a package where `systemd-timesyncd` is already present), and editing `/etc` in the running image by hand (not reproducible).

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
