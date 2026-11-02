# meta-edgeml

Project layer. Holds our own recipes and configuration, so that the build is reproducible from this repository.

| Recipe | What it does |
| --- | --- |
| edgeml-config | Wired Ethernet with DHCP (gives the board network time through systemd-timesyncd) and a resolver drop-in that turns LLMNR off (closes port 5355). |
