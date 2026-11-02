SUMMARY = "EdgeML system configuration: wired DHCP (for network time) and resolver without LLMNR"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://20-wired.network \
           file://10-edgeml.conf"

S = "${WORKDIR}"

inherit allarch

do_install() {
    install -d ${D}${sysconfdir}/systemd/network
    install -m 0644 ${WORKDIR}/20-wired.network ${D}${sysconfdir}/systemd/network/
    install -d ${D}${sysconfdir}/systemd/resolved.conf.d
    install -m 0644 ${WORKDIR}/10-edgeml.conf ${D}${sysconfdir}/systemd/resolved.conf.d/
}

FILES:${PN} = "${sysconfdir}/systemd"
