SUMMARY = "EdgeML system configuration: wired DHCP, resolver without LLMNR, sysctl security, SSH keys"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://20-wired.network \
           file://10-edgeml.conf \
           file://99-edgeml-security.conf \
           file://authorized_keys"

S = "${WORKDIR}"

inherit allarch

do_install() {
    install -d ${D}${sysconfdir}/systemd/network
    install -m 0644 ${WORKDIR}/20-wired.network ${D}${sysconfdir}/systemd/network/
    install -d ${D}${sysconfdir}/systemd/resolved.conf.d
    install -m 0644 ${WORKDIR}/10-edgeml.conf ${D}${sysconfdir}/systemd/resolved.conf.d/
    install -d ${D}${sysconfdir}/sysctl.d
    install -m 0644 ${WORKDIR}/99-edgeml-security.conf ${D}${sysconfdir}/sysctl.d/
    install -d ${D}/home/root/.ssh
    install -m 0600 ${WORKDIR}/authorized_keys ${D}/home/root/.ssh/authorized_keys
}

FILES:${PN} = "${sysconfdir}/systemd ${sysconfdir}/sysctl.d /home/root/.ssh"
