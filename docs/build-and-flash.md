# Build and flash guide

How to build the image, put the Jetson Nano in recovery mode, flash it and log in. Everything runs on the laptop unless stated.

## 1. Prerequisites

- Ubuntu 22.04 host with 16 GB RAM. The BSP-only build used about 23 GB in `build/` (`tmp` 16 GB, `downloads` 3.7 GB, `sstate-cache` 3.7 GB) plus the layer clones. Keep at least 50 GB free, since CUDA will add more.
- Host packages and kas (see the README for the exact commands).
- Not inside a Python virtual environment: run `deactivate` first.
- A micro-USB **data** cable and a 5 V 4 A barrel-jack supply, with the **J48** jumper fitted so the board powers from the barrel jack.
- A microSD card for the Nano. **Flashing erases it.**

## 2. Build

```
scripts/build.sh
```

This runs `kas build kas/edgeml-dev.yml`. kas clones poky, meta-openembedded and meta-tegra at the commits pinned in the YAML file, then builds `core-image-minimal` for machine `jetson-nano-devkit`.

- The first build from scratch took under two hours on the laptop. Rebuilds that change only the image take minutes because of the shared state cache (`build/sstate-cache`).
- The result is `build/tmp/deploy/images/jetson-nano-devkit/core-image-minimal-jetson-nano-devkit.tegraflash.tar.gz`.
- The development configuration adds OpenSSH, Avahi, `kernel-modules`, `l4t-usb-device-mode` and `debug-tweaks` (empty root password). **These are for development only and are removed or replaced in the hardening stage.**

If kas warns that a repository has no commit, you are using an unpinned config. Use `kas/edgeml-dev.yml`, which pins all three layers.

## 3. Put the Nano in recovery mode

The jumper must be in place **before** power is applied.

1. Unplug the barrel-jack power.
2. Insert the SD card.
3. Fit a jumper across the **FRC** pin and the **GND** pin next to it on the button header (the pins labelled `DIS`, `RST`, `FRC`, `ON` on the underside of the board). Do not bridge any other pair: the neighbouring pairs reset or power-cycle the board. A jumper made of two single-pin connectors joined by a wire works if each connector sits on one of those two pins.
4. Connect micro-USB from the Nano to a laptop USB port (not a hub).
5. Connect the barrel-jack power. The board turns on by itself.
6. On the laptop, check:
   ```
   lsusb -d 0955:
   ```
   You should see an `NVIDIA Corp.` line (an APX device). The board shows no lights or display output in this mode.

## 4. Flash

```
scripts/flash.sh
```

The script checks for the recovery device, asks for confirmation, unpacks the package into a clean `~/tegraflash` folder, and runs `sudo ./doflash.sh`, which writes the bootloader to the Nano's QSPI flash and the root filesystem to the SD card. Do not unplug anything until it finishes.

Then remove the FRC jumper and power-cycle the Nano.

NVIDIA does not officially support flashing L4T R32.x from an Ubuntu 22.04 host, but it worked on this laptop. If a flash fails on yours, do the flash step from an Ubuntu 18.04 container or VM.

Flashing also rewrites the Nano's QSPI bootloader, which every SD card shares. A card with stock JetPack 4.6.1 should still boot, but confirm this before relying on it.

## 5. Log in

The image presents a USB network, as stock JetPack does. Wait about a minute after power-up, then:

```
ssh root@192.168.55.1
```

There is no password in the development image.

SSH will warn that the remote host identification has changed after every re-flash, because a new OS generates new host keys. Fix it with:

```
ssh-keygen -f ~/.ssh/known_hosts -R 192.168.55.1
```

For the direct USB link only, this shortcut in `~/.ssh/config` avoids the warning. Remove it when the system is hardened:

```
Host nano-usb
  HostName 192.168.55.1
  User root
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  LogLevel ERROR
```

Then use `ssh nano-usb`. Ethernet works too: `ssh root@jetson-nano-devkit.local` (Avahi).

## 6. Check it is our image

On the Nano:

```
cat /etc/os-release       # Poky (Yocto Project Reference Distro) 4.0, kirkstone
uname -r                  # 4.9.337-l4t-r32.7.6+...
ls /dev/nvhost*           # GPU device nodes present
```

Then take the idle measurements, as described in [measurement-method.md](measurement-method.md).

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `lsusb -d 0955:` prints nothing | The Nano is not in recovery mode. A board that has been on for minutes booted normally: unplug the power, confirm the jumper is on both FRC pins, connect micro-USB, and only then connect power. Try another cable or port |
| SSH: "REMOTE HOST IDENTIFICATION HAS CHANGED" | Expected after a re-flash. Run the `ssh-keygen -R` command above |
| `systemd-analyze: not found` on the image | It is a separate package in Yocto. Boot time is read from `systemctl show` instead (see `measure-image.sh`) |
| `head -30` or `ps | head -25` fails on the image | BusyBox `head` takes no `-N` option. Use `sed -n '1,30p'` |
| Date shows 2023 | No real-time clock and no network time yet. It resets at each boot until NTP is working |
| `kas` command not found | `pip3 install --user kas` and add `~/.local/bin` to `PATH` |
| `kas build` fails inside a virtual environment | Run `deactivate` first |
| Flash stops or hangs | Re-check recovery mode, use a direct USB port, and retry. If it fails repeatedly, use the Ubuntu 18.04 container fallback |
