# meta-edgeml

Project layer. Holds our own recipes and configuration, so that the build is reproducible from this repository.

| Recipe / bbappend | What it does |
| --- | --- |
| `edgeml-config` | Wired Ethernet with DHCP (network time), resolver drop-in disabling LLMNR (closes port 5355), kernel sysctl hardening (`99-edgeml-security.conf`), and host SSH public key installation. |
| `edgeml-detector` | Multithreaded pipelined webcam (V4L2) to YOLOv5n TensorRT engine to MQTT. C++ program with triple-buffering (`cudaMallocHost`), sandboxed systemd service `edgeml-detector.service` running as `edgeml:video` (UID 1200, exposure 3.2 OK), and udev rules for NVIDIA GPU (Major 506) access. |
| `openssh` bbappend | Enforces public-key authentication only (`PasswordAuthentication no`, `PermitRootLogin prohibit-password`, `PermitEmptyPasswords no`). |
| `linux-tegra` bbappend | Kernel configuration trim (`recipes-kernel/linux/files/edgeml-trim.cfg`): switches off debugging, Bluetooth, sound, unused camera, network, USB and filesystem drivers (-625 options, -35% total kernel storage). |
