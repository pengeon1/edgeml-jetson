# Detector service

`edgeml-detector` reads frames from a USB webcam, runs a YOLOv5n FP16 TensorRT engine and publishes the detections as JSON over MQTT. Source: `meta-edgeml/recipes-edgeml/edgeml-detector/`.

## Where things are on the board

| What | Path |
| --- | --- |
| Program | `/usr/bin/edgeml-detector` |
| Service | `edgeml-detector.service` (enabled, starts at boot, restarts on failure) |
| Settings | `/etc/edgeml/detector.conf` |
| Engine file | `/var/lib/edgeml/yolov5n_fp16.engine` (copy it there; it is not in the repository) |

## Settings (`/etc/edgeml/detector.conf`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `EDGEML_BROKER` | `192.168.55.100` | MQTT broker (the laptop on the USB link; `10.42.0.1` with Ethernet sharing) |
| `EDGEML_PORT` | `1883` | Broker port |
| `EDGEML_TOPIC` | `edgeml/detections` | Topic |
| `EDGEML_ENGINE` | `/var/lib/edgeml/yolov5n_fp16.engine` | Serialized TensorRT engine |
| `EDGEML_CAMERA` | `/dev/video0` | V4L2 device |
| `EDGEML_CONF` | `0.35` | Confidence threshold |
| `EDGEML_NMS` | `0.45` | Overlap threshold for removing duplicate boxes |

## Message format

One JSON message per frame, QoS 0:

```
{"ts":1703415484637,"seq":5493,"frame":{"w":640,"h":480},"inference_ms":45.3,
 "detections":[{"label":"person","class":0,"conf":0.456,"box":[96,15,636,462]}]}
```

`ts` is the board's wall clock in milliseconds (correct only when the board has network time), `box` is `[x1,y1,x2,y2]` in camera pixels.

## Use

On the laptop (broker and viewer):

```
sudo apt install -y mosquitto mosquitto-clients
printf 'listener 1883 0.0.0.0\nallow_anonymous true\n' | sudo tee /etc/mosquitto/conf.d/edgeml.conf
sudo systemctl restart mosquitto
mosquitto_sub -h localhost -t 'edgeml/#' -v
```

On the board:

```
systemctl status edgeml-detector
journalctl -u edgeml-detector -n 15        # fps and timing lines every 2 s
systemctl stop edgeml-detector             # frees the camera for a manual run
edgeml-detector --frames 100 --no-mqtt     # 100 frames, timings only
systemctl reset-failed edgeml-detector && systemctl restart edgeml-detector
```

The timing line reads `fps=18.1 pre=9.4ms infer=45.0ms post+mqtt=0.7ms capture_to_publish=105ms dets/frame=1.00 mqtt=ok`.

## Requirements on the engine

One FP32 input `[1,3,S,S]` and one FP32 output `[1,N,5+classes]`: the standard YOLOv5 ONNX export (`--simplify`, opset 12, 640x640) built with `trtexec --fp16`. The program refuses other shapes with a message.
