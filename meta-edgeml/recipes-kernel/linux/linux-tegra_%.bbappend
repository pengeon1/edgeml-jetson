# EdgeML: trim the L4T 4.9 kernel configuration (see files/edgeml-trim.cfg).
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://edgeml-trim.cfg"
