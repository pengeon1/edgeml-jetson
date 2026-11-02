SUMMARY = "Camera object detector: V4L2 webcam, YOLOv5 TensorRT engine, MQTT output"
DESCRIPTION = "Reads frames from a USB webcam, runs a serialized YOLOv5 TensorRT engine and publishes the detections as JSON over MQTT. Started at boot by systemd."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://edgeml-detector.cpp \
           file://edgeml-detector.service \
           file://detector.conf"

S = "${WORKDIR}"

# TensorRT and CUDA are NVIDIA binaries from meta-tegra. The CUDA headers and
# libraries are used directly, no nvcc is needed.
DEPENDS = "tensorrt-core cuda-cudart cuda-nvcc-headers cudnn libcublas"
CUDA_VERSION ??= "10.2"
CUDA_ROOT = "${STAGING_DIR_HOST}${prefix}/local/cuda-${CUDA_VERSION}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "edgeml-detector.service"
SYSTEMD_AUTO_ENABLE = "enable"

do_compile() {
    ${CXX} ${CXXFLAGS} -std=c++14 -O2 \
        -I${CUDA_ROOT}/include \
        ${S}/edgeml-detector.cpp -o ${B}/edgeml-detector \
        ${LDFLAGS} \
        -L${CUDA_ROOT}/${baselib} \
        -Wl,-rpath-link,${CUDA_ROOT}/${baselib} \
        -Wl,--allow-shlib-undefined \
        -lnvinfer -lcudart -lpthread
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${B}/edgeml-detector ${D}${bindir}/
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/edgeml-detector.service ${D}${systemd_system_unitdir}/
    install -d ${D}${sysconfdir}/edgeml
    install -m 0644 ${WORKDIR}/detector.conf ${D}${sysconfdir}/edgeml/
    install -d ${D}${localstatedir}/lib/edgeml
}

FILES:${PN} += "${sysconfdir}/edgeml ${localstatedir}/lib/edgeml"
CONFFILES:${PN} = "${sysconfdir}/edgeml/detector.conf"
RDEPENDS:${PN} = "tensorrt-core cuda-cudart cudnn libcublas"
PACKAGE_ARCH = "${MACHINE_ARCH}"
COMPATIBLE_MACHINE = "(tegra)"
