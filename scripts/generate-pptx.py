#!/usr/bin/env python3
"""
scripts/generate-pptx.py
Generates a 16:9 widescreen PowerPoint presentation (.pptx) for:
CS3000: Operating Systems (Dr. Raghavan Santhanam)
Project: Application-Specific Linux Distribution for Edge ML on Jetson Nano
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# Colors
BG_COLOR = RGBColor(13, 17, 23)        # #0D1117 GitHub Dark
CARD_BG = RGBColor(22, 27, 34)         # #161B22
CARD_BORDER = RGBColor(48, 54, 61)     # #30363D
TEXT_WHITE = RGBColor(240, 246, 252)   # #F0F6FC
TEXT_MUTED = RGBColor(139, 148, 158)   # #8B949E
ACCENT_GREEN = RGBColor(63, 185, 80)   # #3FB950
ACCENT_BLUE = RGBColor(88, 166, 255)   # #58A6FF
ACCENT_YELLOW = RGBColor(210, 153, 34) # #D29922
ACCENT_PURPLE = RGBColor(187, 128, 247)# #BB80F7

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.color.rgb = BG_COLOR
        return bg

    def add_header(slide, title_text, category_text="CS3000: OPERATING SYSTEMS | DR. RAGHAVAN SANTHANAM"):
        # Category / Subtitle
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_BLUE

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.6))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE

    def add_footer(slide, current_idx, total_slides=9):
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.0), Inches(11.7), Inches(0.3))
        tf = footer_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = f"edgeml-jetson: Tailoring Embedded Linux for Edge ML   |   Slide {current_idx} of {total_slides}"
        p.font.size = Pt(10)
        p.font.color.rgb = TEXT_MUTED

    def add_card(slide, left, top, width, height, bg_rgb=CARD_BG, border_rgb=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_rgb
        card.line.color.rgb = border_rgb
        card.line.width = Pt(1.2)
        return card

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Accent top border
    top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = ACCENT_GREEN
    top_bar.line.fill.background()

    # Title Card
    add_card(s1, Inches(1.0), Inches(1.2), Inches(11.333), Inches(5.2))
    
    # Title Text
    tbox = s1.shapes.add_textbox(Inches(1.4), Inches(1.6), Inches(10.5), Inches(2.2))
    tf = tbox.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = "CS3000 OPERATING SYSTEMS — FINAL PROJECT DEMO"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_BLUE

    p1 = tf.add_paragraph()
    p1.text = "edgeml-jetson: Tailoring Embedded Linux for Real-Time Edge ML Inference"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_before = Pt(8)

    p2 = tf.add_paragraph()
    p2.text = "A hardened, reproducible, read-only Yocto distribution on the NVIDIA Jetson Nano"
    p2.font.size = Pt(16)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(6)

    # Badges row
    badges = [
        ("TARGET", "Jetson Nano (Maxwell GPU)", ACCENT_BLUE),
        ("BUILD", "Yocto Poky Kirkstone", ACCENT_PURPLE),
        ("PIPELINE", "20.0 FPS YOLOv5n FP16", ACCENT_GREEN),
        ("ROOTFS", "1.4 GB Immutable (ro)", ACCENT_YELLOW)
    ]
    for i, (b_title, b_val, b_col) in enumerate(badges):
        bx = Inches(1.4 + i * 2.65)
        by = Inches(4.2)
        add_card(s1, bx, by, Inches(2.5), Inches(1.0), bg_rgb=RGBColor(26, 32, 44), border_rgb=b_col)
        bbox = s1.shapes.add_textbox(bx + Inches(0.15), by + Inches(0.12), Inches(2.2), Inches(0.75))
        btf = bbox.text_frame
        btf.word_wrap = True
        bp0 = btf.paragraphs[0]
        bp0.text = b_title
        bp0.font.size = Pt(10)
        bp0.font.bold = True
        bp0.font.color.rgb = b_col
        bp1 = btf.add_paragraph()
        bp1.text = b_val
        bp1.font.size = Pt(12)
        bp1.font.bold = True
        bp1.font.color.rgb = TEXT_WHITE

    # Author & Guide footer
    meta_box = s1.shapes.add_textbox(Inches(1.4), Inches(5.5), Inches(10.5), Inches(0.6))
    mtf = meta_box.text_frame
    mp = mtf.paragraphs[0]
    mp.text = "Presenter: Piyush   |   Course Instructor: Dr. Raghavan Santhanam   |   Demo Duration: 10 Minutes"
    mp.font.size = Pt(12)
    mp.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 2: Problem Statement & Motivation
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "The Problem: General-Purpose Desktop OS on Edge Hardware")
    add_footer(s2, 2)

    # Left Column: The 4 OS Failures of Stock JetPack
    add_card(s2, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2))
    lbox = s2.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.4), Inches(4.8))
    ltf = lbox.text_frame
    ltf.word_wrap = True
    
    lp0 = ltf.paragraphs[0]
    lp0.text = "Why Stock Ubuntu 18.04 / JetPack Fails on Edge Devices:"
    lp0.font.size = Pt(15)
    lp0.font.bold = True
    lp0.font.color.rgb = ACCENT_YELLOW

    points_s2 = [
        ("Storage & Package Bloat", "Occupies 12 GB with 2,351 packages (LibreOffice, X11, CUPS). Wastes 88% of flash storage on desktop utilities."),
        ("Unified Memory Pressure", "Consumes 670 MB RAM at idle. In Jetson's unified architecture, CPU and GPU compete for the same 4 GB physical bus."),
        ("Prolonged Boot Delays", "Takes 15.5 s to boot due to serial console baud rate bottlenecks (65 KB boot log over 115200 baud)."),
        ("Storage Fragility (Power Cuts)", "Standard writable ext4 filesystem corrupts journal and inode structures on unexpected power disconnection.")
    ]
    for title, desc in points_s2:
        p_t = ltf.add_paragraph()
        p_t.text = f"• {title}: "
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = ltf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # Right Column: Chart Image
    add_card(s2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart1 = "results/charts/footprint_comparison.png"
    if os.path.exists(chart1):
        s2.shapes.add_picture(chart1, Inches(6.95), Inches(1.7), width=Inches(5.4))

    # =========================================================================
    # SLIDE 3: Kernel Customization & Boot Optimization
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Kernel Customization & Boot Time Optimization")
    add_footer(s3, 3)

    # Left Column: OS Kernel Insights
    add_card(s3, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2))
    kbox = s3.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.4), Inches(4.8))
    ktf = kbox.text_frame
    ktf.word_wrap = True

    kp0 = ktf.paragraphs[0]
    kp0.text = "Tailoring Linux 4.9.337 with Config Fragments:"
    kp0.font.size = Pt(15)
    kp0.font.bold = True
    kp0.font.color.rgb = ACCENT_BLUE

    points_s3 = [
        ("Kernel Configuration Trim", "Pruned 625 unnecessary options (-26% options). Dropped sound (ALSA), Bluetooth, CSI sensors, legacy DRM, and profiling (DEBUG_KMEMLEAK, FTRACE)."),
        ("Storage Reductions", "Kernel Image: 38.5 MB -> 28.5 MB (-26%). Modules: 85.2 MB -> 52.1 MB (-39%). Total kernel storage: 80.6 MB vs 112.5 MB stock (-28.4%)."),
        ("Retained Drivers", "Preserved uvcvideo (webcam), host1x / nvgpu (Maxwell GPU), overlayfs, USB network gadget, and INA3221 power sensor."),
        ("Console Silencing (quiet loglevel=3)", "Kernel handover to userspace dropped from 6.1 s to 1.87 s (-69%). Total boot finished in 4.6 s vs 15.5 s stock (70% faster).")
    ]
    for title, desc in points_s3:
        p_t = ktf.add_paragraph()
        p_t.text = f"• {title}: "
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = ktf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # Right Column: Boot Chart
    add_card(s3, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart2 = "results/charts/boot_timeline.png"
    if os.path.exists(chart2):
        s3.shapes.add_picture(chart2, Inches(6.95), Inches(1.7), width=Inches(5.4))

    # =========================================================================
    # SLIDE 4: Process Concurrency: Multithreaded Triple Buffering
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Process Concurrency: Pipelined Triple-Buffering")
    add_footer(s4, 4)

    # Top Card: The Pipeline Concept
    add_card(s4, Inches(0.8), Inches(1.5), Inches(11.7), Inches(2.2))
    pbox = s4.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.3), Inches(1.9))
    ptf = pbox.text_frame
    ptf.word_wrap = True
    
    pp0 = ptf.paragraphs[0]
    pp0.text = "Overcoming the Sequential Bottleneck in edgeml-detector.cpp"
    pp0.font.size = Pt(16)
    pp0.font.bold = True
    pp0.font.color.rgb = ACCENT_GREEN

    pp1 = ptf.add_paragraph()
    pp1.text = "• Naive Sequential Loop:  T_pre (11.0 ms) + T_infer (48.2 ms) + T_post (1.8 ms) = 61.0 ms  =>  18.3 FPS (stalling Maxwell GPU)"
    pp1.font.size = Pt(13)
    pp1.font.color.rgb = RGBColor(248, 81, 73)
    pp1.space_before = Pt(6)

    pp2 = ptf.add_paragraph()
    pp2.text = "• Asynchronous Pipelined Loop:  max(T_pre, T_infer) = max(11.0 ms, 48.2 ms) = 48.2 ms  =>  20.0 FPS Live Cap (+9.3% throughput gain)"
    pp2.font.size = Pt(13)
    pp2.font.color.rgb = ACCENT_GREEN
    pp2.space_before = Pt(4)

    # Bottom Left Card: Producer & Memory
    add_card(s4, Inches(0.8), Inches(3.9), Inches(5.7), Inches(2.8))
    plbox = s4.shapes.add_textbox(Inches(1.0), Inches(4.05), Inches(5.3), Inches(2.5))
    pltf = plbox.text_frame
    pltf.word_wrap = True
    
    plp0 = pltf.paragraphs[0]
    plp0.text = "Stage 1: Producer Thread (Cortex-A57 Core 1)"
    plp0.font.size = Pt(14)
    plp0.font.bold = True
    plp0.font.color.rgb = ACCENT_BLUE

    p_items_l = [
        ("V4L2 Zero-Copy Mmap", "Captures camera frames directly from kernel memory buffers without userspace copy."),
        ("CPU Bilinear Letterbox", "Executes YUYV -> Planar RGB FP32 scaling (11.0 ms) into pinned host memory (cudaMallocHost)."),
        ("Stale Frame Dropping", "Automatically drops older unconsumed frames to keep glass-to-publish latency under 116 ms.")
    ]
    for it, idesc in p_items_l:
        pi = pltf.add_paragraph()
        pi.text = f"• {it}: {idesc}"
        pi.font.size = Pt(12)
        pi.font.color.rgb = TEXT_WHITE
        pi.space_before = Pt(4)

    # Bottom Right Card: Consumer & Sync
    add_card(s4, Inches(6.8), Inches(3.9), Inches(5.7), Inches(2.8))
    prbox = s4.shapes.add_textbox(Inches(7.0), Inches(4.05), Inches(5.3), Inches(2.5))
    prtf = prbox.text_frame
    prtf.word_wrap = True

    prp0 = prtf.paragraphs[0]
    prp0.text = "Stage 2: Consumer Thread (Maxwell GPU + Core 0)"
    prp0.font.size = Pt(14)
    prp0.font.bold = True
    prp0.font.color.rgb = ACCENT_PURPLE

    p_items_r = [
        ("Asynchronous DMA Copy", "cudaMemcpyAsync transfers input tensor over internal bus concurrently with capture."),
        ("TensorRT GPU Enqueue", "IExecutionContext::enqueueV2 executes FP16 network inference on 128 Maxwell cores."),
        ("Sync Primitives", "std::mutex & std::condition_variable manage 3 host buffer slots with zero lock contention.")
    ]
    for it, idesc in p_items_r:
        pi = prtf.add_paragraph()
        pi.text = f"• {it}: {idesc}"
        pi.font.size = Pt(12)
        pi.font.color.rgb = TEXT_WHITE
        pi.space_before = Pt(4)

    # =========================================================================
    # SLIDE 5: Memory Management & Power-Performance Modes
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Memory Management & Power-Performance Trade-offs")
    add_footer(s5, 5)

    # Left: RAM Chart & Findings
    add_card(s5, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart3 = "results/charts/ram_comparison.png"
    if os.path.exists(chart3):
        s5.shapes.add_picture(chart3, Inches(0.95), Inches(1.65), width=Inches(5.4))
    
    rbox = s5.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(5.3), Inches(1.2))
    rtf = rbox.text_frame
    rtf.word_wrap = True
    rp = rtf.paragraphs[0]
    rp.text = "Reclaiming Unified Memory Headroom:\n• Idle RAM dropped from 670 MB to 217 MB (-67.6%).\n• Reclaims +450 MB unified RAM for large computer vision models."
    rp.font.size = Pt(11)
    rp.font.color.rgb = TEXT_WHITE

    # Right: Power vs FPS Chart & Findings
    add_card(s5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart4 = "results/charts/power_vs_fps.png"
    if os.path.exists(chart4):
        s5.shapes.add_picture(chart4, Inches(6.95), Inches(1.65), width=Inches(5.4))

    pwr_box = s5.shapes.add_textbox(Inches(7.0), Inches(5.4), Inches(5.3), Inches(1.2))
    pwrtf = pwr_box.text_frame
    pwrtf.word_wrap = True
    pwrp = pwrtf.paragraphs[0]
    pwrp.text = "DVFS & Power Mode Comparison:\n• MAXN (10 W): 20.0 FPS @ 6.22 W = 3.22 FPS/W.\n• 5 W Mode (nvpmodel -m 1): 12.5 FPS @ 3.84 W = 3.26 FPS/W (+10.8% eff.)."
    pwrp.font.size = Pt(11)
    pwrp.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 6: Security Isolation & The Principle of Least Privilege
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Security Hardening: Sandboxing & Device Nodes")
    add_footer(s6, 6)

    # Left Column: Service Sandboxing & GPU Major 506
    add_card(s6, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2))
    sec_lbox = s6.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.4), Inches(4.8))
    sltf = sec_lbox.text_frame
    sltf.word_wrap = True

    sp0 = sltf.paragraphs[0]
    sp0.text = "Systemd Sandboxing (UID 1200 edgeml:video):"
    sp0.font.size = Pt(15)
    sp0.font.bold = True
    sp0.font.color.rgb = ACCENT_GREEN

    points_s6_l = [
        ("Process Isolation", "NoNewPrivileges=true, ProtectSystem=strict, ProtectHome=true, PrivateTmp=true, ProtectKernelTunables=true, RestrictRealtime=true."),
        ("The Maxwell GPU Major 506 Discovery", "Standard char-nvhost only allows Major 242. Jetson Nano's Maxwell GPU character node is Major 506 (char-57000000.gpu)."),
        ("Udev Device Permissions", "Installed 99-tegra-devices.rules (MODE=0660, GROUP=video) to grant non-root GPU access to UID 1200."),
        ("Security Exposure Score", "systemd-analyze security dropped rating from 9.6 UNSAFE to 3.2 OK (-67% attack exposure reduction).")
    ]
    for title, desc in points_s6_l:
        p_t = sltf.add_paragraph()
        p_t.text = f"• {title}: "
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = sltf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # Right Column: Network Hardening & Attack Surface
    add_card(s6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    sec_rbox = s6.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(4.8))
    srtf = sec_rbox.text_frame
    srtf.word_wrap = True

    srp0 = srtf.paragraphs[0]
    srp0.text = "Minimizing Network Attack Surface:"
    srp0.font.size = Pt(15)
    srp0.font.bold = True
    srp0.font.color.rgb = ACCENT_BLUE

    points_s6_r = [
        ("SSH Hardening (OpenSSH)", "Enforced PasswordAuthentication no, PermitRootLogin prohibit-password, and PermitEmptyPasswords no. Password brute-forcing is mathematically impossible."),
        ("Closing Listening Ports", "Stock ran 8 listening sockets. Our image runs 1 external socket (SSH port 22). LLMNR port 5355 closed via systemd-resolved drop-in."),
        ("Kernel Sysctl Hardening", "Installed 99-edgeml-security.conf: rp_filter=1 (anti-spoofing reverse path filtering), kptr_restrict=2 (hidden kernel pointers), dmesg_restrict=1 (dmesg root-only)."),
        ("Immutable Storage", "Root filesystem mounted read-only (ro) prevents malware persistence or system file modification.")
    ]
    for title, desc in points_s6_r:
        p_t = srtf.add_paragraph()
        p_t.text = f"• {title}: "
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = srtf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 7: VFS Design & Power-Cut Resilience
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "VFS Architecture & Power-Cut Fault Tolerance")
    add_footer(s7, 7)

    # Top Card: VFS Architecture
    add_card(s7, Inches(0.8), Inches(1.5), Inches(11.7), Inches(2.4))
    vbox = s7.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.3), Inches(2.1))
    vtf = vbox.text_frame
    vtf.word_wrap = True

    vp0 = vtf.paragraphs[0]
    vp0.text = "Filesystem Layout: Read-Only Root + Ephemeral Tmpfs"
    vp0.font.size = Pt(16)
    vp0.font.bold = True
    vp0.font.color.rgb = ACCENT_YELLOW

    v_points = [
        ("Immutable Root (/)", "Root partition /dev/mmcblk0p1 mounted ro. System binaries, libraries, and configs cannot be modified or corrupted."),
        ("Volatile State on Tmpfs", "/run, /tmp, and /var/volatile are mounted on tmpfs (RAM). All transient writes disappear cleanly on reboot."),
        ("Isolated Model Partition", "Serialized TensorRT engine stored in dedicated /var/lib/edgeml directory."),
        ("Write Protection Verified", "Live writes to /usr, /etc, or /bin are immediately rejected with 'Read-only file system'.")
    ]
    for vt, vd in v_points:
        p = vtf.add_paragraph()
        p.text = f"• {vt}: {vd}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(3)

    # Bottom Card: Power-Cut Stress Harness Results
    add_card(s7, Inches(0.8), Inches(4.1), Inches(11.7), Inches(2.6))
    pcut_box = s7.shapes.add_textbox(Inches(1.0), Inches(4.25), Inches(11.3), Inches(2.3))
    pctf = pcut_box.text_frame
    pctf.word_wrap = True

    pcp0 = pctf.paragraphs[0]
    pcp0.text = "Empirical Validation: 5 / 5 Power-Cut Recovery Test (scripts/test-power-cut.sh)"
    pcp0.font.size = Pt(15)
    pcp0.font.bold = True
    pcp0.font.color.rgb = ACCENT_GREEN

    pcut_log = [
        "Cycle 1: Recovery in ~4s  |  Mount: ro  |  EXT4 errors: 0  |  Auto-start: ACTIVE  |  MQTT: RESUMED (44.6 ms)",
        "Cycle 2: Recovery in ~4s  |  Mount: ro  |  EXT4 errors: 0  |  Auto-start: ACTIVE  |  MQTT: RESUMED (44.7 ms)",
        "Cycle 3: Recovery in ~3s  |  Mount: ro  |  EXT4 errors: 0  |  Auto-start: ACTIVE  |  MQTT: RESUMED (44.7 ms)",
        "Cycle 4: Recovery in ~3s  |  Mount: ro  |  EXT4 errors: 0  |  Auto-start: ACTIVE  |  MQTT: RESUMED (44.8 ms)",
        "Cycle 5: Recovery in ~3s  |  Mount: ro  |  EXT4 errors: 0  |  Auto-start: ACTIVE  |  MQTT: RESUMED (44.8 ms)",
        "RESULT: 5 / 5 ungraceful power interruptions survived with zero filesystem corruption."
    ]
    for line in pcut_log:
        p = pctf.add_paragraph()
        p.text = line
        p.font.size = Pt(11)
        p.font.color.rgb = ACCENT_GREEN if "RESULT" in line else TEXT_MUTED
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 8: Master Evaluation & Defending Baseline B
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Master Evaluation & Defending Against 'Baseline B'")
    add_footer(s8, 8)

    # Left: Master Summary Chart
    add_card(s8, Inches(0.8), Inches(1.5), Inches(6.5), Inches(5.2))
    chart5 = "results/charts/master_summary_dashboard.png"
    if os.path.exists(chart5):
        s8.shapes.add_picture(chart5, Inches(0.95), Inches(1.65), width=Inches(6.2))

    # Right: The Baseline B Defense Card
    add_card(s8, Inches(7.5), Inches(1.5), Inches(5.0), Inches(5.2))
    b_box = s8.shapes.add_textbox(Inches(7.7), Inches(1.7), Inches(4.6), Inches(4.8))
    btf = b_box.text_frame
    btf.word_wrap = True

    bp0 = btf.paragraphs[0]
    bp0.text = "Refuting 'Baseline B' (Minimised Stock):"
    bp0.font.size = Pt(14)
    bp0.font.bold = True
    bp0.font.color.rgb = ACCENT_YELLOW

    bp_sub = btf.add_paragraph()
    bp_sub.text = "'Couldn't you just disable GNOME via systemctl set-default multi-user.target on Ubuntu?'"
    bp_sub.font.size = Pt(11)
    bp_sub.font.italic = True
    bp_sub.font.color.rgb = TEXT_MUTED
    bp_sub.space_before = Pt(4)

    b_points = [
        ("Storage Waste", "Baseline B still occupies 10.2 GB on disk (vs 1.4 GB ours). All desktop packages remain installed."),
        ("Package Exposure", "Retains >2,000 unneeded packages and unpinned apt repos that cannot be audited."),
        ("Kernel Bloat", "Boots the monolithic 112.5 MB stock kernel with 2,388 options enabled and slow console logging."),
        ("Zero Power-Cut Immunity", "Operates on writable ext4; vulnerable to catastrophic filesystem corruption on power cuts.")
    ]
    for btitle, bdesc in b_points:
        p_t = btf.add_paragraph()
        p_t.text = f"• {btitle}:"
        p_t.font.size = Pt(12)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(6)
        
        p_d = btf.add_paragraph()
        p_d.text = f"  {bdesc}"
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 9: Live Demo Walkthrough (10-Minute Pacing)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Live Demo Walkthrough & Operating Systems Takeaways")
    add_footer(s9, 9)

    # 3 Steps Cards across the screen
    demo_steps = [
        ("DEMO PART 1 (1 Min)", "7-Point Health & Security Audit", [
            "Run ./scripts/smoke-test.sh nano-usb",
            "Verify UID 1200 unprivileged execution",
            "Verify read-only rootfs mount (ro)",
            "Verify systemd security score (3.2 OK)",
            "Verify Maxwell GPU char node (Major 506)"
        ], ACCENT_BLUE),
        ("DEMO PART 2 (1.5 Mins)", "Live Pipelined Telemetry", [
            "Open http://localhost:8080 in browser",
            "Stream live 20.0 FPS camera detection",
            "Demonstrate overlapped letterboxing",
            "Show rolling latency sparklines (<50 ms)",
            "Demonstrate MQTT JSON publishing"
        ], ACCENT_GREEN),
        ("DEMO PART 3 (1.5 Mins)", "Live Power-Cut Survival", [
            "Trigger emergency reset: SysRq 'b'",
            "Watch board drop and reboot in ~4s",
            "Observe zero EXT4 filesystem corruption",
            "Observe detector service auto-resume",
            "Verify MQTT detections resume instantly"
        ], ACCENT_YELLOW)
    ]

    for i, (step_hdr, step_title, step_bullets, step_col) in enumerate(demo_steps):
        cx = Inches(0.8 + i * 3.95)
        cy = Inches(1.5)
        add_card(s9, cx, cy, Inches(3.8), Inches(4.2), border_rgb=step_col)

        dbox = s9.shapes.add_textbox(cx + Inches(0.2), cy + Inches(0.2), Inches(3.4), Inches(3.8))
        dtf = dbox.text_frame
        dtf.word_wrap = True

        dp0 = dtf.paragraphs[0]
        dp0.text = step_hdr
        dp0.font.size = Pt(11)
        dp0.font.bold = True
        dp0.font.color.rgb = step_col

        dp1 = dtf.add_paragraph()
        dp1.text = step_title
        dp1.font.size = Pt(14)
        dp1.font.bold = True
        dp1.font.color.rgb = TEXT_WHITE
        dp1.space_before = Pt(4)

        for b in step_bullets:
            dp_b = dtf.add_paragraph()
            dp_b.text = f"• {b}"
            dp_b.font.size = Pt(11)
            dp_b.font.color.rgb = TEXT_MUTED
            dp_b.space_before = Pt(5)

    # Bottom Takeaway Card
    add_card(s9, Inches(0.8), Inches(5.9), Inches(11.7), Inches(0.9), bg_rgb=RGBColor(26, 32, 44), border_rgb=ACCENT_GREEN)
    tbox = s9.shapes.add_textbox(Inches(1.0), Inches(6.0), Inches(11.3), Inches(0.7))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    tp = ttf.paragraphs[0]
    tp.text = "CORE OS LESSON: Tailoring the operating system vertically—from kernel config to VFS mount policy, process concurrency, and systemd sandboxing—yields an 88% smaller, 70% faster, and corruption-immune edge appliance."
    tp.font.size = Pt(11)
    tp.font.bold = True
    tp.font.color.rgb = TEXT_WHITE

    # Save
    out_path = "presentation/cs3000-edgeml-presentation.pptx"
    prs.save(out_path)
    print(f"[SUCCESS] PowerPoint presentation saved to {out_path}")

if __name__ == "__main__":
    create_deck()
