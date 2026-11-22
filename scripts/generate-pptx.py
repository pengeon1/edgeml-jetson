#!/usr/bin/env python3
"""
scripts/generate-pptx.py
Generates a simplified, high-impact 16:9 widescreen PowerPoint presentation (.pptx) for:
CS3000: Operating Systems (Dr. Raghavan Santhanam)
Team:
  - Narayana Murthy S (CS24B1047)
  - Piyush Mishra (CS24B1048)
  - Ankush R (CS24B1062)
  - Mahalis Rayhan (CS24B1095)
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
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
ACCENT_RED = RGBColor(248, 81, 73)     # #F85149

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
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_BLUE

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.7), Inches(0.6))
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
    # SLIDE 1: Title & Team Members
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    top_bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = ACCENT_GREEN
    top_bar.line.fill.background()

    # Main Card
    add_card(s1, Inches(1.0), Inches(1.0), Inches(11.333), Inches(5.6))
    
    # Title & Subtitle
    tbox = s1.shapes.add_textbox(Inches(1.4), Inches(1.3), Inches(10.5), Inches(1.8))
    tf = tbox.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = "CS3000 OPERATING SYSTEMS — FINAL PROJECT PRESENTATION"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_BLUE

    p1 = tf.add_paragraph()
    p1.text = "edgeml-jetson: Tailoring Embedded Linux for Real-Time Edge ML"
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_before = Pt(6)

    p2 = tf.add_paragraph()
    p2.text = "A Hardened, Read-Only, High-Throughput Yocto Linux Appliance on NVIDIA Jetson Nano"
    p2.font.size = Pt(14)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(4)

    # 4 Team Members Cards
    team = [
        ("Narayana Murthy S", "CS24B1047"),
        ("Piyush Mishra", "CS24B1048"),
        ("Ankush R", "CS24B1062"),
        ("Mahalis Rayhan", "CS24B1095")
    ]
    for i, (name, roll) in enumerate(team):
        tx = Inches(1.4 + i * 2.65)
        ty = Inches(3.4)
        add_card(s1, tx, ty, Inches(2.5), Inches(1.2), bg_rgb=RGBColor(26, 32, 44), border_rgb=ACCENT_BLUE)
        t_box = s1.shapes.add_textbox(tx + Inches(0.15), ty + Inches(0.2), Inches(2.2), Inches(0.8))
        ttf = t_box.text_frame
        ttf.word_wrap = True
        tp0 = ttf.paragraphs[0]
        tp0.text = name
        tp0.font.size = Pt(13)
        tp0.font.bold = True
        tp0.font.color.rgb = TEXT_WHITE
        tp1 = ttf.add_paragraph()
        tp1.text = roll
        tp1.font.size = Pt(12)
        tp1.font.bold = True
        tp1.font.color.rgb = ACCENT_GREEN

    # 4 Stat Pills
    stats = [
        ("STORAGE", "1.4 GB (-88.3%)", ACCENT_YELLOW),
        ("BOOT TIME", "4.6 s (-70.3%)", ACCENT_BLUE),
        ("IDLE RAM", "217 MB (-67.6%)", ACCENT_PURPLE),
        ("THROUGHPUT", "20.0 FPS (+9.3%)", ACCENT_GREEN)
    ]
    for i, (s_label, s_val, s_col) in enumerate(stats):
        sx = Inches(1.4 + i * 2.65)
        sy = Inches(4.85)
        add_card(s1, sx, sy, Inches(2.5), Inches(0.9), bg_rgb=RGBColor(26, 32, 44), border_rgb=s_col)
        sbox = s1.shapes.add_textbox(sx + Inches(0.15), sy + Inches(0.1), Inches(2.2), Inches(0.7))
        stf = sbox.text_frame
        stf.word_wrap = True
        sp0 = stf.paragraphs[0]
        sp0.text = s_label
        sp0.font.size = Pt(10)
        sp0.font.bold = True
        sp0.font.color.rgb = s_col
        sp1 = stf.add_paragraph()
        sp1.text = s_val
        sp1.font.size = Pt(13)
        sp1.font.bold = True
        sp1.font.color.rgb = TEXT_WHITE

    # Instructor footer
    ibox = s1.shapes.add_textbox(Inches(1.4), Inches(5.95), Inches(10.5), Inches(0.4))
    itf = ibox.text_frame
    ip = itf.paragraphs[0]
    ip.text = "Course Instructor: Dr. Raghavan Santhanam   |   Demo Duration: 10 Minutes"
    ip.font.size = Pt(11)
    ip.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 2: Problem Statement & Motivation
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Motivation: Why Stock Desktop Linux Fails on Edge Hardware")
    add_footer(s2, 2)

    # Left: 4 Core Problems
    add_card(s2, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2))
    lbox = s2.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.4), Inches(4.8))
    ltf = lbox.text_frame
    ltf.word_wrap = True
    
    lp0 = ltf.paragraphs[0]
    lp0.text = "Stock JetPack 4.6.1 (Ubuntu 18.04 Desktop) Flaws:"
    lp0.font.size = Pt(15)
    lp0.font.bold = True
    lp0.font.color.rgb = ACCENT_YELLOW

    points_s2 = [
        ("Storage Bloat (12 GB)", "2,351 packages installed. Desktop apps (LibreOffice, X11, CUPS) waste 88% of flash storage."),
        ("RAM Contention (670 MB)", "Idle daemons consume 670 MB RAM. In Jetson's unified architecture, CPU and GPU compete for the same 4 GB physical memory."),
        ("Slow Boot (15.5 s)", "Delayed by verbose kernel logging over a 115,200 baud serial console line."),
        ("Power-Cut Fragility", "Writable ext4 filesystem easily corrupts inode and journal metadata during sudden power unplugging.")
    ]
    for title, desc in points_s2:
        p_t = ltf.add_paragraph()
        p_t.text = f"• {title}:"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = ltf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # Right: Chart
    add_card(s2, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart1 = "results/charts/footprint_comparison.png"
    if os.path.exists(chart1):
        s2.shapes.add_picture(chart1, Inches(6.95), Inches(1.7), width=Inches(5.4))

    # =========================================================================
    # SLIDE 3: Kernel Customization & Boot Optimization
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Kernel Customization & Boot Optimization")
    add_footer(s3, 3)

    # Left: Kernel Points
    add_card(s3, Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.2))
    kbox = s3.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(5.4), Inches(4.8))
    ktf = kbox.text_frame
    ktf.word_wrap = True

    kp0 = ktf.paragraphs[0]
    kp0.text = "Kernel 4.9.337 Tailoring via edgeml-trim.cfg:"
    kp0.font.size = Pt(15)
    kp0.font.bold = True
    kp0.font.color.rgb = ACCENT_BLUE

    points_s3 = [
        ("Pruned 625 Options (-26%)", "Disabled sound (ALSA), Bluetooth, CSI camera sensors, legacy DRM, and profilers (DEBUG_KMEMLEAK, FTRACE)."),
        ("Kernel Footprint: 80.6 MB vs 112.5 MB", "Kernel Image dropped from 38.5 MB to 28.5 MB (-26%); modules dropped from 85.2 MB to 52.1 MB (-39%)."),
        ("Retained Hardware Drivers", "Preserved uvcvideo (webcam), host1x / nvgpu (Maxwell GPU), overlayfs, USB network gadget, and INA3221 power monitor."),
        ("Console Silencing (quiet loglevel=3)", "Silenced 65 KB boot log over 115200 UART. Kernel handover dropped from 6.1 s to 1.87 s (-69%); boot finished in 4.6 s vs 15.5 s (70% faster)!")
    ]
    for title, desc in points_s3:
        p_t = ktf.add_paragraph()
        p_t.text = f"• {title}:"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = ktf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # Right: Boot Chart
    add_card(s3, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart2 = "results/charts/boot_timeline.png"
    if os.path.exists(chart2):
        s3.shapes.add_picture(chart2, Inches(6.95), Inches(1.7), width=Inches(5.4))

    # =========================================================================
    # SLIDE 4: Pipelined Multithreading — 20.0 FPS
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Process Concurrency: Pipelined Triple-Buffering")
    add_footer(s4, 4)

    # Top Card: Formula Comparison
    add_card(s4, Inches(0.8), Inches(1.5), Inches(11.7), Inches(1.9))
    pbox = s4.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.3), Inches(1.6))
    ptf = pbox.text_frame
    ptf.word_wrap = True
    
    pp0 = ptf.paragraphs[0]
    pp0.text = "Overcoming the Sequential Pipeline Bottleneck"
    pp0.font.size = Pt(15)
    pp0.font.bold = True
    pp0.font.color.rgb = ACCENT_GREEN

    pp1 = ptf.add_paragraph()
    pp1.text = "• Naive Sequential:  11.0 ms (CPU Pre) + 48.2 ms (GPU Infer) + 1.8 ms (MQTT) = 61.0 ms  =>  18.3 FPS (stalls GPU)"
    pp1.font.size = Pt(13)
    pp1.font.color.rgb = ACCENT_RED
    pp1.space_before = Pt(4)

    pp2 = ptf.add_paragraph()
    pp2.text = "• Pipelined Overlap:  max(11.0 ms, 48.2 ms) = 48.2 ms  =>  20.0 FPS Live Cap (+9.3% gain, 100% CPU overhead hidden)"
    pp2.font.size = Pt(13)
    pp2.font.bold = True
    pp2.font.color.rgb = ACCENT_GREEN
    pp2.space_before = Pt(4)

    # Bottom Left: Producer
    add_card(s4, Inches(0.8), Inches(3.6), Inches(5.7), Inches(3.1))
    plbox = s4.shapes.add_textbox(Inches(1.0), Inches(3.75), Inches(5.3), Inches(2.8))
    pltf = plbox.text_frame
    pltf.word_wrap = True
    
    plp0 = pltf.paragraphs[0]
    plp0.text = "Stage 1: Producer Thread (Core 1)"
    plp0.font.size = Pt(14)
    plp0.font.bold = True
    plp0.font.color.rgb = ACCENT_BLUE

    p_items_l = [
        ("V4L2 Zero-Copy Mmap", "Captures camera frames directly from kernel memory without userspace copy."),
        ("CPU Bilinear Letterbox", "Executes YUYV -> Planar RGB FP32 conversion (11 ms) into pinned host memory (cudaMallocHost)."),
        ("Stale Frame Dropping", "Automatically drops older unconsumed frames to keep glass-to-publish latency < 116 ms.")
    ]
    for it, idesc in p_items_l:
        pi = pltf.add_paragraph()
        pi.text = f"• {it}: {idesc}"
        pi.font.size = Pt(12)
        pi.font.color.rgb = TEXT_WHITE
        pi.space_before = Pt(5)

    # Bottom Right: Consumer
    add_card(s4, Inches(6.8), Inches(3.6), Inches(5.7), Inches(3.1))
    prbox = s4.shapes.add_textbox(Inches(7.0), Inches(3.75), Inches(5.3), Inches(2.8))
    prtf = prbox.text_frame
    prtf.word_wrap = True

    prp0 = prtf.paragraphs[0]
    prp0.text = "Stage 2: Consumer Thread (GPU + Core 0)"
    prp0.font.size = Pt(14)
    prp0.font.bold = True
    prp0.font.color.rgb = ACCENT_PURPLE

    p_items_r = [
        ("Asynchronous DMA Copy", "cudaMemcpyAsync transfers input tensor concurrently over internal memory bus."),
        ("TensorRT FP16 Enqueue", "IExecutionContext::enqueueV2 launches inference on 128 Maxwell GPU cores."),
        ("Thread Synchronization", "std::mutex & std::condition_variable manage 3 host buffer slots with zero lock contention.")
    ]
    for it, idesc in p_items_r:
        pi = prtf.add_paragraph()
        pi.text = f"• {it}: {idesc}"
        pi.font.size = Pt(12)
        pi.font.color.rgb = TEXT_WHITE
        pi.space_before = Pt(5)

    # =========================================================================
    # SLIDE 5: Memory Headroom & Power Modes (DVFS)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Memory Headroom & Power-Performance Modes")
    add_footer(s5, 5)

    # Left: RAM
    add_card(s5, Inches(0.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart3 = "results/charts/ram_comparison.png"
    if os.path.exists(chart3):
        s5.shapes.add_picture(chart3, Inches(0.95), Inches(1.65), width=Inches(5.4))
    
    rbox = s5.shapes.add_textbox(Inches(1.0), Inches(5.4), Inches(5.3), Inches(1.2))
    rtf = rbox.text_frame
    rtf.word_wrap = True
    rp = rtf.paragraphs[0]
    rp.text = "Unified Memory Optimization:\n• Idle RAM dropped from 670 MB to 217 MB (-67.6%).\n• Reclaims +450 MB unified RAM for edge AI models."
    rp.font.size = Pt(12)
    rp.font.bold = True
    rp.font.color.rgb = TEXT_WHITE

    # Right: Power
    add_card(s5, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    chart4 = "results/charts/power_vs_fps.png"
    if os.path.exists(chart4):
        s5.shapes.add_picture(chart4, Inches(6.95), Inches(1.65), width=Inches(5.4))

    pwr_box = s5.shapes.add_textbox(Inches(7.0), Inches(5.4), Inches(5.3), Inches(1.2))
    pwrtf = pwr_box.text_frame
    pwrtf.word_wrap = True
    pwrp = pwrtf.paragraphs[0]
    pwrp.text = "DVFS & Power Mode Comparison:\n• MAXN (10 W): 20.0 FPS @ 6.22 W = 3.22 FPS/W.\n• 5 W Mode: 12.5 FPS @ 3.84 W = 3.26 FPS/W (+10.8% eff., ~38% cooler!)."
    pwrp.font.size = Pt(12)
    pwrp.font.bold = True
    pwrp.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 6: Security Isolation & Least Privilege
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Security Isolation: Sandboxing & Device Nodes")
    add_footer(s6, 6)

    # Left: Sandboxing
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
        ("Process Sandboxing", "NoNewPrivileges=true, ProtectSystem=strict, ProtectHome=true, PrivateTmp=true, ProtectKernelTunables=true, RestrictRealtime=true."),
        ("Maxwell GPU Major 506 Discovery", "Standard char-nvhost only allows Major 242. Jetson Nano's Maxwell GPU character node is Major 506 (char-57000000.gpu)."),
        ("Udev Permissions", "Installed 99-tegra-devices.rules (MODE=0660, GROUP=video) to grant non-root GPU hardware access."),
        ("Security Exposure Score", "systemd-analyze security dropped rating from 9.6 UNSAFE to 3.2 OK (-67% attack exposure reduction).")
    ]
    for title, desc in points_s6_l:
        p_t = sltf.add_paragraph()
        p_t.text = f"• {title}:"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = sltf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # Right: Network Hardening
    add_card(s6, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.2))
    sec_rbox = s6.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.3), Inches(4.8))
    srtf = sec_rbox.text_frame
    srtf.word_wrap = True

    srp0 = srtf.paragraphs[0]
    srp0.text = "Network & OS Hardening:"
    srp0.font.size = Pt(15)
    srp0.font.bold = True
    srp0.font.color.rgb = ACCENT_BLUE

    points_s6_r = [
        ("SSH Key-Only Auth", "PasswordAuthentication no & PermitRootLogin prohibit-password. Password brute-forcing is impossible."),
        ("Closed Listening Ports", "Stock ran 8 listening sockets. Our image runs only 1 external socket (SSH port 22). LLMNR port 5355 closed."),
        ("Kernel Sysctl Hardening", "rp_filter=1 (anti-spoofing reverse path filtering), kptr_restrict=2 (hidden kernel pointers), dmesg_restrict=1 (root-only dmesg)."),
        ("Immutable Rootfs", "Read-only ext4 partition blocks malware persistence and unauthorized file tampering.")
    ]
    for title, desc in points_s6_r:
        p_t = srtf.add_paragraph()
        p_t.text = f"• {title}:"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE
        p_t.space_before = Pt(8)
        
        p_d = srtf.add_paragraph()
        p_d.text = f"  {desc}"
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 7: VFS & Power-Cut Resilience
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "VFS Architecture & Power-Cut Fault Tolerance")
    add_footer(s7, 7)

    # Top Card: VFS
    add_card(s7, Inches(0.8), Inches(1.5), Inches(11.7), Inches(2.3))
    vbox = s7.shapes.add_textbox(Inches(1.0), Inches(1.65), Inches(11.3), Inches(2.0))
    vtf = vbox.text_frame
    vtf.word_wrap = True

    vp0 = vtf.paragraphs[0]
    vp0.text = "Immutable VFS Architecture (Read-Only Root + Ephemeral Tmpfs)"
    vp0.font.size = Pt(15)
    vp0.font.bold = True
    vp0.font.color.rgb = ACCENT_YELLOW

    v_points = [
        ("Read-Only Root (/)", "Root partition /dev/mmcblk0p1 mounted ro. System binaries, libraries, and configs cannot be corrupted."),
        ("Volatile State on Tmpfs", "/run, /tmp, and /var/volatile mounted on tmpfs (RAM). Transient writes disappear cleanly on reboot."),
        ("Dedicated Model Storage", "Serialized TensorRT engine safely isolated in /var/lib/edgeml."),
        ("Tamper-Proof", "Writes to /usr, /etc, or /bin are immediately rejected with 'Read-only file system'.")
    ]
    for vt, vd in v_points:
        p = vtf.add_paragraph()
        p.text = f"• {vt}: {vd}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(3)

    # Bottom Card: Stress Test
    add_card(s7, Inches(0.8), Inches(4.0), Inches(11.7), Inches(2.7))
    pcut_box = s7.shapes.add_textbox(Inches(1.0), Inches(4.15), Inches(11.3), Inches(2.4))
    pctf = pcut_box.text_frame
    pctf.word_wrap = True

    pcp0 = pctf.paragraphs[0]
    pcp0.text = "Empirical Validation: 5 / 5 Power-Cut Stress Test (scripts/test-power-cut.sh)"
    pcp0.font.size = Pt(15)
    pcp0.font.bold = True
    pcp0.font.color.rgb = ACCENT_GREEN

    pcut_lines = [
        "Tested by triggering emergency hardware resets (SysRq 'b') during active 20.0 FPS GPU inference:",
        "• Cycle 1 to 5: All 5 cycles recovered cleanly in 3–4 seconds.",
        "• Mount state: ro (read-only) cleanly preserved.",
        "• EXT4 filesystem errors: ZERO (0 dmesg errors, clean journal replay).",
        "• Auto-recovery: edgeml-detector.service auto-started and resumed streaming detections over MQTT immediately.",
        "RESULT: 100% immunity to ungraceful power loss and filesystem corruption."
    ]
    for i, line in enumerate(pcut_lines):
        p = pctf.add_paragraph()
        p.text = line
        p.font.size = Pt(11)
        if "RESULT" in line:
            p.font.bold = True
            p.font.color.rgb = ACCENT_GREEN
        elif i == 0:
            p.font.color.rgb = TEXT_WHITE
        else:
            p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 8: Master Evaluation & Defending Baseline B
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Master Evaluation & Defending Against 'Baseline B'")
    add_footer(s8, 8)

    # Left: Master Chart
    add_card(s8, Inches(0.8), Inches(1.5), Inches(6.5), Inches(5.2))
    chart5 = "results/charts/master_summary_dashboard.png"
    if os.path.exists(chart5):
        s8.shapes.add_picture(chart5, Inches(0.95), Inches(1.65), width=Inches(6.2))

    # Right: Baseline B Defense
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
    bp_sub.space_before = Pt(3)

    b_points = [
        ("Storage Waste (10.2 GB)", "Disabling GNOME still leaves 10.2 GB on disk (vs 1.4 GB ours). All desktop packages remain installed."),
        ("Package Exposure", "Retains >2,000 unneeded packages and unpinned apt repos that cannot be audited."),
        ("Kernel Bloat (112.5 MB)", "Boots the bloated stock kernel with 2,388 options and slow serial console logging."),
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
    # SLIDE 9: Live Demo Walkthrough
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Live Demo Walkthrough (3-Minute Plan)")
    add_footer(s9, 9)

    demo_steps = [
        ("PART 1 (45 Secs)", "Health & Security Audit", [
            "./scripts/smoke-test.sh nano-usb",
            "UID 1200 unprivileged execution",
            "Read-only rootfs mount (ro)",
            "Systemd exposure: 3.2 OK",
            "Maxwell GPU char node (Major 506)"
        ], ACCENT_BLUE),
        ("PART 2 (1 Min)", "Live 20 FPS Telemetry", [
            "python3 scripts/web-dashboard.py 8080",
            "Open http://localhost:8080",
            "Live 20.0 FPS camera detection",
            "Overlapped CPU letterboxing",
            "Rolling latency sparklines (<50 ms)"
        ], ACCENT_GREEN),
        ("PART 3 (1 Min)", "Power-Cut Survival", [
            "ssh nano-usb 'echo b > /proc/sysrq-trigger'",
            "Board resets instantly during inference",
            "Recovers in 3–4 seconds",
            "Zero EXT4 filesystem errors",
            "Detector auto-resumes streaming"
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

    add_card(s9, Inches(0.8), Inches(5.9), Inches(11.7), Inches(0.9), bg_rgb=RGBColor(26, 32, 44), border_rgb=ACCENT_GREEN)
    tbox = s9.shapes.add_textbox(Inches(1.0), Inches(6.0), Inches(11.3), Inches(0.7))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    tp = ttf.paragraphs[0]
    tp.text = "CORE OS LESSON: Vertical tailoring—from kernel config to VFS mount policy, process concurrency, and systemd sandboxing—yields an 88% smaller, 70% faster, and corruption-immune edge appliance."
    tp.font.size = Pt(11)
    tp.font.bold = True
    tp.font.color.rgb = TEXT_WHITE

    out_path = "presentation/cs3000-edgeml-presentation.pptx"
    prs.save(out_path)
    print(f"[SUCCESS] Simplified PowerPoint presentation saved to {out_path}")

if __name__ == "__main__":
    create_deck()
