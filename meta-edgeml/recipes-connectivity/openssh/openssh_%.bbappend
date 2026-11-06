# SSH hardening: enforce keys-only login, disable password authentication and empty passwords
do_install:append() {
    sed -i 's/^#*PermitRootLogin .*/PermitRootLogin prohibit-password/' ${D}${sysconfdir}/ssh/sshd_config
    sed -i 's/^#*PasswordAuthentication .*/PasswordAuthentication no/' ${D}${sysconfdir}/ssh/sshd_config
    sed -i 's/^#*PermitEmptyPasswords .*/PermitEmptyPasswords no/' ${D}${sysconfdir}/ssh/sshd_config
}

