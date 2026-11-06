#!/usr/bin/env python3
"""
scripts/plot-benchmarks.py
Generates publication-quality comparison charts for the Track A report & presentation.
Outputs both vector SVG and 300-DPI PNG figures into results/charts/:
1. footprint_comparison: Image archive and rootfs size
2. boot_timeline: Kernel handover and userspace boot duration
3. ram_comparison: Idle RAM usage and headroom on 4 GB platform
4. power_vs_fps: FPS vs Power across MAXN and 5W modes
5. master_summary: 4-panel publication dashboard
"""

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = "results/charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Styling configuration
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
    "axes.grid": True,
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
    "figure.autolayout": True
})

# Color palette
COLOR_STOCK = "#7f8c8d"      # Muted grey
COLOR_BASELINE_B = "#e67e22" # Orange
COLOR_OURS = "#27ae60"       # Vibrant green
COLOR_ACCENT = "#2980b9"     # Accent blue

def save_fig(fig, name):
    png_path = os.path.join(OUTPUT_DIR, f"{name}.png")
    svg_path = os.path.join(OUTPUT_DIR, f"{name}.svg")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[GENERATED] {png_path} and {svg_path}")

# ------------------------------------------------------------- 1. Footprint
def plot_footprint():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    categories = ["Stock JetPack 4.6.1", "Minimised Stock\n(Baseline B)", "Our EdgeML Image\n(Yocto / meta-tegra)"]
    archive_sizes = [6.56, 5.80, 0.74] # GB
    rootfs_sizes = [12.00, 10.20, 1.40] # GB

    x = np.arange(len(categories))
    width = 0.35

    rects1 = ax.bar(x - width/2, archive_sizes, width, label="Compressed Archive (GB)", color="#34495e")
    rects2 = ax.bar(x + width/2, rootfs_sizes, width, label="Used Rootfs (GB)", color=COLOR_OURS)

    ax.set_ylabel("Size in Gigabytes (GB)")
    ax.set_title("Storage Footprint: Compressed Archive & Root Filesystem")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.set_ylim(0, 14)

    # Bar value labels
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.2f} GB", xy=(rect.get_x() + rect.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.2f} GB", xy=(rect.get_x() + rect.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    save_fig(fig, "footprint_comparison")

# --------------------------------------------------------- 2. Boot Timeline
def plot_boot_timeline():
    fig, ax = plt.subplots(figsize=(8, 4))
    configurations = [
        "Stock JetPack (15.5 s)",
        "Untrimmed Yocto (Verbose, 8.9 s)",
        "Our Image (Trimmed & Quiet, 4.6 s)"
    ]
    kernel_handover = [2.30, 6.10, 1.87] # seconds
    userspace = [13.20, 2.80, 2.73]       # seconds

    y = np.arange(len(configurations))
    height = 0.45

    p1 = ax.barh(y, kernel_handover, height, label="Kernel Handover to Userspace", color="#e74c3c")
    p2 = ax.barh(y, userspace, height, left=kernel_handover, label="Userspace Initialization", color=COLOR_ACCENT)

    ax.set_xlabel("Boot Duration (seconds)")
    ax.set_title("Boot Time Breakdown: Kernel Handover vs Userspace")
    ax.set_yticks(y)
    ax.set_yticklabels(configurations)
    ax.legend(loc="lower right")
    ax.set_xlim(0, 18)

    # Value annotations
    for i, (k, u) in enumerate(zip(kernel_handover, userspace)):
        total = k + u
        ax.text(total + 0.3, i, f"Total: {total:.1f} s", va="center", fontweight="bold", fontsize=10)
        ax.text(k / 2, i, f"{k:.2f}s", va="center", ha="center", color="white", fontweight="bold", fontsize=9)
        ax.text(k + (u / 2), i, f"{u:.2f}s", va="center", ha="center", color="white", fontweight="bold", fontsize=9)

    save_fig(fig, "boot_timeline")

# ------------------------------------------------------------- 3. RAM Usage
def plot_ram():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    states = [
        "Stock JetPack\n(Idle)",
        "Our EdgeML\n(Idle)",
        "Our EdgeML\n(Active Pipeline)"
    ]
    used_ram = [670, 217, 1019]       # MB
    total_ram = 3964                  # MB (Jetson Nano 4 GB platform)
    free_ram = [total_ram - u for u in used_ram]

    x = np.arange(len(states))
    width = 0.45

    p1 = ax.bar(x, used_ram, width, label="Used System RAM (MB)", color="#c0392b")
    p2 = ax.bar(x, free_ram, width, bottom=used_ram, label="Available Unified Headroom (MB)", color=COLOR_OURS)

    ax.set_ylabel("RAM in Megabytes (MB)")
    ax.set_title("Unified RAM Utilization & ML Headroom (4 GB Total)")
    ax.set_xticks(x)
    ax.set_xticklabels(states)
    ax.set_ylim(0, 4500)
    ax.legend(loc="upper right")

    for i, u in enumerate(used_ram):
        ax.text(i, u / 2, f"{u} MB", ha="center", va="center", color="white", fontweight="bold")
        ax.text(i, u + (free_ram[i] / 2), f"{free_ram[i]} MB Free", ha="center", va="center", color="white", fontweight="bold")

    save_fig(fig, "ram_comparison")

# ------------------------------------------------------- 4. Power vs Throughput
def plot_power_vs_fps():
    fig, ax = plt.subplots(figsize=(7, 4.5))
    modes = [
        "MAXN (10 W)\nRaw TRT Benchmark",
        "MAXN (10 W)\nLive Sync Pipeline",
        "MAXN (10 W)\nLive Pipelined (Ours)",
        "5 W Mode\nLive Pipelined (Ours)"
    ]
    fps_vals = [22.22, 18.30, 20.00, 12.50]
    power_vals = [6.41, 6.22, 6.22, 3.84] # Watts
    efficiency = [f / p for f, p in zip(fps_vals, power_vals)] # FPS / Watt

    x = np.arange(len(modes))
    width = 0.35

    rects1 = ax.bar(x - width/2, fps_vals, width, label="Throughput (FPS)", color=COLOR_ACCENT)
    rects2 = ax.bar(x + width/2, efficiency, width, label="Efficiency (FPS / Watt)", color=COLOR_OURS)

    ax.set_ylabel("Value")
    ax.set_title("Throughput & Energy Efficiency Across Power Modes")
    ax.set_xticks(x)
    ax.set_xticklabels(modes)
    ax.legend(loc="upper right")
    ax.set_ylim(0, 26)

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.1f} FPS", xy=(rect.get_x() + rect.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.2f} FPS/W", xy=(rect.get_x() + rect.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    save_fig(fig, "power_vs_fps")

# ------------------------------------------------------- 5. Master Dashboard
def plot_master_dashboard():
    fig, axs = plt.subplots(2, 2, figsize=(13, 9))

    # Panel 1: Storage
    ax = axs[0, 0]
    cats = ["Stock", "Baseline B", "Ours"]
    roots = [12.0, 10.2, 1.4]
    ax.bar(cats, roots, color=["#7f8c8d", "#e67e22", "#27ae60"], width=0.5)
    ax.set_ylabel("Used Rootfs (GB)")
    ax.set_title("A. Used Root Filesystem (GB)")
    for i, v in enumerate(roots):
        ax.text(i, v + 0.3, f"{v} GB", ha="center", fontweight="bold")
    ax.set_ylim(0, 14)

    # Panel 2: Boot Time
    ax = axs[0, 1]
    boots = [15.5, 8.9, 4.6]
    ax.bar(cats, boots, color=["#7f8c8d", "#f39c12", "#27ae60"], width=0.5)
    ax.set_ylabel("Seconds (s)")
    ax.set_title("B. Total Boot Time (seconds)")
    for i, v in enumerate(boots):
        ax.text(i, v + 0.3, f"{v} s", ha="center", fontweight="bold")
    ax.set_ylim(0, 18)

    # Panel 3: Idle RAM
    ax = axs[1, 0]
    rams = [670, 510, 217]
    ax.bar(cats, rams, color=["#c0392b", "#e67e22", "#27ae60"], width=0.5)
    ax.set_ylabel("RAM Used (MB)")
    ax.set_title("C. Idle RAM Consumption (MB)")
    for i, v in enumerate(rams):
        ax.text(i, v + 15, f"{v} MB", ha="center", fontweight="bold")
    ax.set_ylim(0, 800)

    # Panel 4: Security Score
    ax = axs[1, 1]
    scores = [9.6, 9.2, 3.2]
    colors = ["#c0392b", "#d35400", "#27ae60"]
    ax.bar(cats, scores, color=colors, width=0.5)
    ax.set_ylabel("Exposure Score (Lower is Safer)")
    ax.set_title("D. Systemd Security Exposure Rating")
    for i, v in enumerate(scores):
        ax.text(i, v + 0.2, f"{v}", ha="center", fontweight="bold")
    ax.axhline(5.0, color="grey", linestyle="--", alpha=0.7)
    ax.text(2.2, 5.2, "Safe Threshold (< 5.0)", color="dimgrey", fontsize=9)
    ax.set_ylim(0, 11)

    fig.suptitle("EdgeML Jetson Nano: Comprehensive System Evaluation", fontsize=15, fontweight="bold")
    save_fig(fig, "master_summary_dashboard")

if __name__ == "__main__":
    print(f"Generating benchmark charts into {OUTPUT_DIR}...")
    plot_footprint()
    plot_boot_timeline()
    plot_ram()
    plot_power_vs_fps()
    plot_master_dashboard()
    print("All charts successfully generated!")
