# Results

Raw measurement logs. Never edit a log by hand: re-run the measurement and save the new file.

## Layout

```
results/
├── stock/         Stock JetPack 4.6.1 (L4T R32.7.1) idle, size, and TRT inference logs
├── cuda-image/    Our Yocto image with CUDA 10.2 / TensorRT 8.2 (runs, power, tegrastats)
├── kernel/        Kernel configs before/after trim, diffs, console silencing logs
├── ours/          
│   ├── manifests/   BitBake license and package manifests (image_license, license, package)
│   ├── reliability/ Power-cut resilience stress logs (SysRq emergency reset verification)
│   └── security/    Read-only rootfs tests, SSH hardening tests, sysctl, nmap port scans
└── charts/        Publication-quality benchmark charts (PNG and vector SVG)
```

## Files

| File | What it is |
| --- | --- |
| `stock/baseline-idle.txt` | Idle baseline: boot, RAM, disk, packages, services, ports, kernel size, idle power |
| `stock/baseline-sizes.txt` | Largest folders under `/usr` and largest packages by installed size |
| `stock/trtexec-stock.txt` | Engine build log and first inference run of YOLOv5n FP16 (656.6 s build) |
| `stock/trtexec-run1.txt` ... `trtexec-run5.txt` | Five inference runs from the saved engine |
| `stock/tegrastats-infer.log` | `tegrastats` log covering the five runs |
| `ours/baseline-ours-v0.txt` | Idle baseline of our first flashed image, no CUDA yet |

Not every file may be present yet: the baselines were saved from `~/baseline` on the Nano with `scp`.

## Summaries

```
scripts/summarize-measure.sh results/stock/baseline-idle.txt
scripts/summarize-measure.sh results/ours/baseline-ours-v0.txt
scripts/summarize-runs.sh    results/stock
scripts/summarize-power.sh   results/stock/tegrastats-infer.log 22.16
```

`summarize-runs.sh` reads `trtexec-run*.txt`, so keep each run in its own file.

## Headline numbers

See the tables in the top-level README. They are regenerated from these logs after each measurement step.
