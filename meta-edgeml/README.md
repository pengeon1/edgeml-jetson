# meta-edgeml

Project layer. Holds our own recipes and configuration, so that the build is reproducible from this repository.

| Recipe | What it does |
| --- | --- |
| edgeml-config | Wired Ethernet with DHCP (gives the board network time through systemd-timesyncd) and a resolver drop-in that turns LLMNR off (closes port 5355). |
| edgeml-detector | Webcam (V4L2) to YOLOv5n TensorRT engine to MQTT. C++ program, systemd service `edgeml-detector.service`, settings in `/etc/edgeml/detector.conf`, engine file in `/var/lib/edgeml/`. |
| linux-tegra bbappend | Kernel configuration trim (`recipes-kernel/linux/files/edgeml-trim.cfg`): switches off debugging, Bluetooth, sound, unused camera, network, USB and filesystem drivers. Generated from the running configuration; the groups and reasons are in the file. |
