# Measurement method

Every comparison between stock JetPack and our image uses the same procedure, so a difference means something. Raw logs are saved in `results/` and committed.

## Rules for fair comparisons

- Same board, same SD card model, same camera, same model file and same TensorRT engine settings (FP16, batch 1, 640x640 input).
- Fix the power mode and clocks before inference runs: `nvpmodel -m 0` (MAXN) and `jetson_clocks`. State this in the report. If the tools are missing on our image, say so.
- Idle measurements: wait about 5 minutes after boot with nothing running.
- Repeat inference runs at least 5 times, report mean ± sample standard deviation.
- Change one variable at a time, and save the log of every run.
- Report units and what was measured. For example, power here is the **module input rail**, not wall power.

## Metrics

| Metric | How it is measured | Script |
| --- | --- | --- |
| Image size | Compressed image file size, and used root filesystem from `df -h /` | `measure-*.sh` |
| Package count | Stock: `dpkg -l`. Yocto: lines in the image's `.manifest` file | `measure-stock.sh`, build output |
| Running services | `systemctl list-units --type=service --state=running` | `measure-*.sh` |
| Listening ports | `ss -tlnp` (or `netstat -tln` on BusyBox) | `measure-*.sh` |
| Idle RAM in use | `MemTotal` minus `MemAvailable` (or `free -m` total minus available) | `summarize-measure.sh` |
| Boot time | Seconds from kernel start to boot finished (see below) | `summarize-measure.sh` |
| Kernel size | Size of `/boot/Image*` and of `/lib/modules/*` | `measure-*.sh` |
| Inference latency and throughput | `trtexec --loadEngine` on the same engine, 30 s per run, 2 s warm-up | `bench-trtexec.sh`, `summarize-runs.sh` |
| Power and efficiency | `tegrastats` `POM_5V_IN`, averaged only while GPU load is at least 90% | `summarize-power.sh` |
| Thermals and throttling | `tegrastats` thermal zone and `GR3D_FREQ` clock | `summarize-power.sh` |

## Boot time

- **Stock:** `systemd-analyze` reports a kernel time and a userspace time. Use the time to `graphical.target` plus the kernel time. Do **not** use the "Startup finished" total: background jobs such as `apt-daily.service` ran for over 3 minutes and inflated it to several minutes.
- **Our image:** `systemd-analyze` is not installed, so read the timestamps from systemd directly. `FinishTimestampMonotonic` (microseconds since kernel start) is the time to boot finished. `UserspaceTimestampMonotonic` shows how much of that passed before systemd started.
- Measure the **third** boot after a fresh flash. The first boot does one-off work such as generating SSH keys.
- The final project metric is power-on to first inference. It needs a stopwatch or video, since the clock before the kernel starts cannot be read from inside the system.

## Idle RAM

Use available memory, not free memory, because file caches count as available. In use = total minus available. Stock and our image report slightly different totals, so compare the "in use" figure.

## Inference benchmark

On the Nano, with the engine file already built:

```
scripts/bench-trtexec.sh ~/yolov5n_fp16.engine ~/results-<label> 5 30
```

Then on any machine with the logs:

```
scripts/summarize-runs.sh  results/<label>
scripts/summarize-power.sh results/<label>/tegrastats.log 22.16    # second argument = mean FPS
```

`trtexec` measures the model only, with random input. It does not include camera capture, pre-processing, non-maximum suppression or drawing, so end-to-end FPS in the application will be lower. The application benchmark will be reported separately.

The TensorRT engine is tied to the TensorRT version and the GPU, so build it on the Nano. A build takes about 11 minutes for YOLOv5n, so the image builds the engine once and stores it, instead of rebuilding at boot.

## Known limitations

- The module input rail does not include the whole board's consumption. An external USB power meter is the ground truth for the final report.
- 30-second runs may not heat the board enough to show throttling. Peak temperature and GPU clock are logged so any throttling is visible.
- Stock and our image run different L4T releases (R32.7.1 and R32.7.6). State this next to any comparison.
