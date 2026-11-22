# Prompt for Claude: Generate Modern Canva Presentation for CS3000

Copy and paste the entire prompt below into Claude:

```markdown
You are an expert presentation designer and embedded systems engineer. I need you to create a complete, publication-grade, modern slide deck outline and design blueprint for a presentation in Canva.

### Presentation Context:
- **Course:** CS3000 Operating Systems
- **Instructor:** Dr. Raghavan Santhanam
- **Presentation Time:** 10 Minutes (6.5 mins talk + 3.5 mins live demo)
- **Project Name:** edgeml-jetson: Tailoring Embedded Linux for Real-Time Edge ML Inference
- **Target Hardware:** NVIDIA Jetson Nano Developer Kit (4 GB LPDDR4 Unified Memory, 128-core Maxwell GPU, Quad-core ARM Cortex-A57 @ 1.48 GHz)
- **Design Aesthetic:** Modern Dark-Mode Tech / Developer Keynote (Deep Charcoal/Navy `#0D1117`, Card Containers `#161B22`, Neon Emerald `#3FB950`, Cyber Blue `#58A6FF`, Warning Gold `#D29922`, High-Contrast White `#F0F6FC`). High visual impact, big callout statistics, minimal text, card-based layouts, and direct comparison tables.

### Team Members (4 Presenters):
1. Narayana Murthy S (CS24B1047)
2. Piyush Mishra (CS24B1048)
3. Ankush R (CS24B1062)
4. Mahalis Rayhan (CS24B1095)

---

### Core Technical Achievements & Data:
- **Storage Footprint:** Flashing archive reduced from 6.56 GB to 738 MB (-88.7%); used rootfs reduced from 12.0 GB to 1.4 GB (-88.3%); packages pruned from 2,351 to 781 (-66.8%).
- **Boot Optimization:** Boot finished in 4.6 s vs 15.5 s stock (70.3% faster); kernel handover accelerated from 6.1 s to 1.87 s (-69%) by silencing 65 KB UART log over 115200 baud via `quiet loglevel=3`.
- **Memory Optimization:** Idle RAM dropped from 670 MB to 217 MB (-67.6%), freeing +450 MB unified RAM headroom (3.78 GB free for AI models).
- **Process Concurrency:** Refactored naive sequential pipeline (18.3 FPS) into multithreaded triple-buffering (`cudaMallocHost`), overlapping 11.0 ms CPU letterboxing concurrently with GPU inference to hit 20.0 FPS (+9.3% boost).
- **Power & Energy:** MAXN 10W (20.0 FPS @ 6.22 W = 3.22 FPS/W) vs 5W Mode (12.5 FPS @ 3.84 W = 3.26 FPS/W, +10.8% efficiency, ~38% cooler).
- **Security & Sandboxing:** Systemd service sandboxed under UID 1200 (`edgeml:video`), resolved Maxwell GPU Major 506 device node access (`char-57000000.gpu`), systemd exposure dropped from 9.6 UNSAFE to 3.2 OK (-67%), SSH key-only auth, closed port 5355.
- **Fault Tolerance:** Read-only rootfs (`ro`) with volatile paths on `tmpfs`; survived 5/5 abrupt emergency power cuts (`SysRq 'b'`) during active inference with 0 EXT4 journal errors and automatic 4-second recovery.
- **Baseline B Defense:** Refuted "Minimised Stock Ubuntu (multi-user.target)" by proving it still wastes 10.2 GB disk, leaves 2,000+ unpinned packages, boots a 112.5 MB bloated kernel, and lacks power-cut immunity.

---

### Your Task:
Please generate an 8-to-9 slide Canva presentation blueprint. For every single slide, provide:
1. **Slide Title & Category Header** (e.g., "SLIDE 3: KERNEL CUSTOMIZATION | PRESENTER: PIYUSH MISHRA")
2. **Canva Layout Instructions:** Detailed visual structure (e.g., "Left 50%: 3 stat cards stacked vertically; Right 50%: Big visual timeline comparison").
3. **Exact Slide Copy / Text:** Minimal, punchy bullet points, bold stat numbers (e.g., "-88.3% Storage"), and subtext.
4. **Color & Styling Cues:** Specific hex colors for cards, borders, badges, and text highlights.
5. **Graphic / Element Suggestions:** Specific icons or illustrations to search in Canva (e.g., "Canva Element: 'microchip outline neon green', 'stopwatch minimal blue'").
6. **Presenter Speaking Cue:** A 30-to-45 second spoken script for that specific team member focusing on Operating Systems principles.

Make it look like an elite conference presentation (think Apple WWDC / Google I/O meets operating systems engineering paper). Deliver the full slide-by-slide blueprint now.
```
