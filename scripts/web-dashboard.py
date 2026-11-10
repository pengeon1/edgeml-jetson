#!/usr/bin/env python3
"""
scripts/web-dashboard.py
Interactive Browser-Based Telemetry & Detection Dashboard for EdgeML Jetson Nano.

Subscribes to live MQTT detections from the Jetson Nano and serves a sleek,
dark-mode web visualizer at http://localhost:8080 with:
- Zero pip dependencies (uses Python standard library: http.server, threading, queue, subprocess)
- Zero external frontend dependencies (native HTML5 Canvas, EventSource SSE, CSS3)
- Live 640x480 camera viewport with real-time bounding boxes, labels, and confidence tags
- Real-time rolling FPS and Latency timeline charts
- System health, security isolation, and read-only status indicators

Usage:
    python3 scripts/web-dashboard.py [PORT]
    Then open http://localhost:8080 in your browser.
"""

import os
import sys
import json
import time
import queue
import threading
import subprocess
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
BROKER_HOST = os.environ.get("EDGEML_BROKER", "localhost")
BROKER_PORT = os.environ.get("EDGEML_PORT", "1883")
TOPIC = os.environ.get("EDGEML_TOPIC", "edgeml/detections")

# Global subscriber queues for Server-Sent Events
subscribers = []
subscribers_lock = threading.Lock()

# Rolling telemetry state
telemetry_lock = threading.Lock()
recent_ts = deque(maxlen=30)
current_telemetry = {
    "fps": 0.0,
    "seq": 0,
    "infer_ms": 0.0,
    "detections": [],
    "total_streamed": 0,
    "status": "waiting"
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EdgeML Jetson Nano — Live Telemetry Dashboard</title>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-bright: #f0f6fc;
      --accent-green: #2ea043;
      --accent-cyan: #388bfd;
      --accent-yellow: #d29922;
      --accent-red: #f85149;
      --accent-purple: #a371f7;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      padding: 18px 24px;
      line-height: 1.4;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 12px;
    }
    .header-title {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .status-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--accent-yellow);
      display: inline-block;
      box-shadow: 0 0 8px var(--accent-yellow);
      transition: background 0.3s, box-shadow 0.3s;
    }
    .status-dot.active {
      background: var(--accent-green);
      box-shadow: 0 0 10px var(--accent-green);
    }
    .status-dot.error {
      background: var(--accent-red);
      box-shadow: 0 0 10px var(--accent-red);
    }
    h1 {
      font-size: 20px;
      color: var(--text-bright);
      font-weight: 600;
      letter-spacing: -0.3px;
    }
    .badge-bar {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .pill {
      background: #21262d;
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 500;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .pill strong { color: var(--text-bright); }
    .pill.green { border-color: rgba(46, 160, 67, 0.4); color: #3fb950; }
    .pill.cyan { border-color: rgba(56, 139, 253, 0.4); color: #58a6ff; }
    .pill.purple { border-color: rgba(163, 113, 247, 0.4); color: #bc8cff; }

    .main-grid {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 20px;
      margin-bottom: 20px;
    }
    @media (max-width: 1024px) {
      .main-grid { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      position: relative;
    }
    .card-title {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #8b949e;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* Viewport Canvas */
    .viewport-container {
      position: relative;
      width: 100%;
      aspect-ratio: 640 / 480;
      background: #05070a;
      border-radius: 6px;
      overflow: hidden;
      border: 1px solid #21262d;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    canvas#viewportCanvas {
      width: 100%;
      height: 100%;
      display: block;
    }
    .viewport-overlay {
      position: absolute;
      top: 10px;
      left: 10px;
      font-family: monospace;
      font-size: 11px;
      color: rgba(255, 255, 255, 0.85);
      background: rgba(13, 17, 23, 0.75);
      padding: 4px 8px;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      pointer-events: none;
    }
    .viewport-rec {
      position: absolute;
      top: 10px;
      right: 10px;
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: monospace;
      font-size: 11px;
      color: var(--accent-red);
      background: rgba(13, 17, 23, 0.75);
      padding: 4px 8px;
      border-radius: 4px;
      border: 1px solid rgba(248, 81, 73, 0.3);
    }
    .viewport-rec-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-red);
      animation: pulse 1s infinite;
    }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

    /* Metrics Grid */
    .metrics-col {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .metrics-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }
    .metric-box {
      background: #0d1117;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .metric-label {
      font-size: 11px;
      color: #8b949e;
      text-transform: uppercase;
      margin-bottom: 6px;
    }
    .metric-value {
      font-size: 32px;
      font-weight: 700;
      color: var(--text-bright);
      font-family: monospace;
      line-height: 1;
    }
    .metric-unit {
      font-size: 14px;
      color: #8b949e;
      margin-left: 2px;
    }
    .metric-sub {
      font-size: 11px;
      color: #58a6ff;
      margin-top: 8px;
    }

    /* Latency Bar */
    .bar-container {
      width: 100%;
      height: 6px;
      background: #21262d;
      border-radius: 3px;
      overflow: hidden;
      margin-top: 8px;
    }
    .bar-fill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
      transition: width 0.15s ease-out;
    }

    /* Sparkline Charts */
    .chart-container {
      height: 65px;
      width: 100%;
      margin-top: 6px;
    }
    canvas.sparkline {
      width: 100%;
      height: 100%;
    }

    /* Detection Log Table */
    .table-container {
      max-height: 175px;
      overflow-y: auto;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #0d1117;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 11px;
      font-family: monospace;
    }
    th {
      background: #161b22;
      padding: 6px 10px;
      text-align: left;
      color: #8b949e;
      position: sticky;
      top: 0;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 6px 10px;
      border-bottom: 1px solid #21262d;
      color: var(--text);
    }
    tr:last-child td { border-bottom: none; }
    .tag-label {
      padding: 2px 6px;
      border-radius: 4px;
      background: rgba(56, 139, 253, 0.15);
      border: 1px solid rgba(56, 139, 253, 0.4);
      color: #58a6ff;
      font-weight: bold;
    }
    .tag-conf {
      color: #3fb950;
      font-weight: bold;
    }
  </style>
</head>
<body>

  <header>
    <div class="header-title">
      <div class="status-dot" id="statusDot"></div>
      <h1>EdgeML Jetson Nano — Live Pipeline Visualizer</h1>
    </div>
    <div class="badge-bar">
      <div class="pill green"><strong>Platform:</strong> Jetson Nano 4GB</div>
      <div class="pill cyan"><strong>Model:</strong> YOLOv5n FP16</div>
      <div class="pill purple"><strong>Pipeline:</strong> Pipelined (Triple-Buffered)</div>
      <div class="pill green"><strong>Rootfs:</strong> Read-Only (ro)</div>
      <div class="pill green"><strong>Sandbox:</strong> UID 1200 (Score: 3.2 OK)</div>
    </div>
  </header>

  <div class="main-grid">
    <!-- Camera Viewport Canvas -->
    <div class="card">
      <div class="card-title">
        <span>Live Camera Viewport (640 &times; 480)</span>
        <span id="canvasFpsBadge" style="font-family: monospace; color: var(--accent-green); font-size: 12px;">-- FPS</span>
      </div>
      <div class="viewport-container">
        <canvas id="viewportCanvas" width="640" height="480"></canvas>
        <div class="viewport-overlay" id="viewportMeta">Frame #0 | Resolution: 640x480</div>
        <div class="viewport-rec">
          <div class="viewport-rec-dot"></div> LIVE STREAM
        </div>
      </div>
    </div>

    <!-- Telemetry & Metrics -->
    <div class="metrics-col">
      <div class="metrics-row">
        <div class="metric-box">
          <div class="metric-label">Pipeline Throughput</div>
          <div><span class="metric-value" id="valFps">0.0</span><span class="metric-unit">FPS</span></div>
          <div class="metric-sub" id="fpsTarget">Budget: 20–22 FPS (Pipelined)</div>
          <div class="chart-container">
            <canvas id="chartFps" class="sparkline" width="220" height="65"></canvas>
          </div>
        </div>

        <div class="metric-box">
          <div class="metric-label">TRT Inference Latency</div>
          <div><span class="metric-value" id="valLatency">0.0</span><span class="metric-unit">ms</span></div>
          <div class="bar-container">
            <div class="bar-fill" id="latencyBar"></div>
          </div>
          <div class="chart-container">
            <canvas id="chartLatency" class="sparkline" width="220" height="65"></canvas>
          </div>
        </div>
      </div>

      <!-- Detection Activity & Log -->
      <div class="card" style="flex: 1;">
        <div class="card-title">
          <span>Real-Time Detection Feed</span>
          <span id="totalStreamedText" style="font-family: monospace; font-size: 11px;">Frames: 0</span>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Seq</th>
                <th>Class</th>
                <th>Confidence</th>
                <th>Bounding Box [x1, y1, x2, y2]</th>
              </tr>
            </thead>
            <tbody id="detectionTableBody">
              <tr>
                <td colspan="4" style="text-align: center; color: #8b949e; padding: 18px;">
                  Waiting for detection packets from Jetson Nano...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <script>
    const canvas = document.getElementById('viewportCanvas');
    const ctx = canvas.getContext('2d');
    const statusDot = document.getElementById('statusDot');
    const valFps = document.getElementById('valFps');
    const valLatency = document.getElementById('valLatency');
    const latencyBar = document.getElementById('latencyBar');
    const canvasFpsBadge = document.getElementById('canvasFpsBadge');
    const viewportMeta = document.getElementById('viewportMeta');
    const totalStreamedText = document.getElementById('totalStreamedText');
    const tableBody = document.getElementById('detectionTableBody');

    const chartFps = document.getElementById('chartFps').getContext('2d');
    const chartLatency = document.getElementById('chartLatency').getContext('2d');

    const fpsHistory = [];
    const latencyHistory = [];
    const MAX_POINTS = 35;

    let activeDetections = [];
    let lastSeq = 0;

    // Draw dark surveillance grid on canvas
    function drawBackground() {
      ctx.fillStyle = "#070b12";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.strokeStyle = "rgba(48, 54, 61, 0.35)";
      ctx.lineWidth = 1;

      // Draw grid
      const step = 40;
      ctx.beginPath();
      for (let x = 0; x < canvas.width; x += step) {
        ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height);
      }
      for (let y = 0; y < canvas.height; y += step) {
        ctx.moveTo(0, y); ctx.lineTo(canvas.width, y);
      }
      ctx.stroke();

      // Center crosshair
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      ctx.strokeStyle = "rgba(56, 139, 253, 0.4)";
      ctx.beginPath();
      ctx.moveTo(cx - 20, cy); ctx.lineTo(cx + 20, cy);
      ctx.moveTo(cx, cy - 20); ctx.lineTo(cx, cy + 20);
      ctx.stroke();

      // Corner brackets
      ctx.strokeStyle = "rgba(46, 160, 67, 0.6)";
      ctx.lineWidth = 2;
      const bLen = 20;
      // Top-left
      ctx.strokeRect(10, 10, bLen, 0); ctx.strokeRect(10, 10, 0, bLen);
      // Top-right
      ctx.strokeRect(canvas.width - 10 - bLen, 10, bLen, 0); ctx.strokeRect(canvas.width - 10, 10, 0, bLen);
      // Bottom-left
      ctx.strokeRect(10, canvas.height - 10, bLen, 0); ctx.strokeRect(10, canvas.height - 10 - bLen, 0, bLen);
      // Bottom-right
      ctx.strokeRect(canvas.width - 10 - bLen, canvas.height - 10, bLen, 0); ctx.strokeRect(canvas.width - 10, canvas.height - 10 - bLen, 0, bLen);
    }

    // Draw detected bounding boxes
    function drawDetections(dets) {
      drawBackground();
      if (!dets || dets.length === 0) return;

      dets.forEach((d, idx) => {
        const [x1, y1, x2, y2] = d.box;
        const w = x2 - x1;
        const h = y2 - y1;
        const confPercent = Math.round(d.conf * 100);

        // Box glow & fill
        ctx.fillStyle = "rgba(46, 160, 67, 0.12)";
        ctx.fillRect(x1, y1, w, h);

        ctx.strokeStyle = "#3fb950";
        ctx.lineWidth = 2;
        ctx.shadowColor = "#3fb950";
        ctx.shadowBlur = 6;
        ctx.strokeRect(x1, y1, w, h);
        ctx.shadowBlur = 0; // reset

        // Label banner
        const tagText = `${d.label.toUpperCase()} ${confPercent}%`;
        ctx.font = "bold 11px monospace";
        const tagWidth = ctx.measureText(tagText).width + 10;
        const tagHeight = 18;

        ctx.fillStyle = "#2ea043";
        ctx.fillRect(x1, Math.max(0, y1 - tagHeight), tagWidth, tagHeight);

        ctx.fillStyle = "#ffffff";
        ctx.fillText(tagText, x1 + 5, Math.max(12, y1 - 4));
      });
    }

    // Draw Sparkline charts on Canvas
    function drawSparkline(cCtx, data, maxVal, color) {
      const w = cCtx.canvas.width;
      const h = cCtx.canvas.height;
      cCtx.clearRect(0, 0, w, h);
      if (data.length < 2) return;

      cCtx.strokeStyle = color;
      cCtx.lineWidth = 2;
      cCtx.beginPath();

      const dx = w / (MAX_POINTS - 1);
      data.forEach((val, i) => {
        const x = i * dx;
        const y = h - (val / maxVal) * (h - 8) - 4;
        if (i === 0) cCtx.moveTo(x, y);
        else cCtx.lineTo(x, y);
      });
      cCtx.stroke();
    }

    // SSE connection to server
    const evtSource = new EventSource('/events');

    evtSource.onopen = () => {
      statusDot.className = "status-dot active";
    };

    evtSource.onerror = () => {
      statusDot.className = "status-dot error";
    };

    evtSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const seq = data.seq || 0;
        const fps = data.fps || 0;
        const inferMs = data.infer_ms || 0;
        const dets = data.detections || [];
        const total = data.total_streamed || 0;

        valFps.textContent = fps.toFixed(1);
        canvasFpsBadge.textContent = `${fps.toFixed(1)} FPS`;
        valLatency.textContent = inferMs.toFixed(1);

        const barPct = Math.min(100, (inferMs / 60) * 100);
        latencyBar.style.width = `${barPct}%`;

        viewportMeta.textContent = `Frame #${seq} | Inferences: ${total} | Detections: ${dets.length}`;
        totalStreamedText.textContent = `Frames: ${total.toLocaleString()}`;

        // Update charts
        fpsHistory.push(fps);
        if (fpsHistory.length > MAX_POINTS) fpsHistory.shift();
        drawSparkline(chartFps, fpsHistory, 25, "#3fb950");

        latencyHistory.push(inferMs);
        if (latencyHistory.length > MAX_POINTS) latencyHistory.shift();
        drawSparkline(chartLatency, latencyHistory, 65, "#58a6ff");

        // Render Canvas
        drawDetections(dets);

        // Update Table
        if (dets.length > 0) {
          let rowsHtml = "";
          dets.forEach(d => {
            const bx = `[${Math.round(d.box[0])}, ${Math.round(d.box[1])}, ${Math.round(d.box[2])}, ${Math.round(d.box[3])}]`;
            rowsHtml += `<tr>
              <td>#${seq}</td>
              <td><span class="tag-label">${d.label}</span></td>
              <td><span class="tag-conf">${(d.conf * 100).toFixed(1)}%</span></td>
              <td>${bx}</td>
            </tr>`;
          });
          tableBody.innerHTML = rowsHtml;
        }

      } catch (err) {
        console.error("Parse error:", err);
      }
    };

    // Initial background draw
    drawBackground();
  </script>
</body>
</html>
"""

class SSEHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(HTML_CONTENT.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))

        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            q = queue.Queue(maxsize=100)
            with subscribers_lock:
                subscribers.append(q)

            try:
                while True:
                    try:
                        msg = q.get(timeout=15.0)
                        self.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        # Keep-alive heartbeat
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with subscribers_lock:
                    if q in subscribers:
                        subscribers.remove(q)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def mqtt_collector_thread():
    """Background reader thread consuming live MQTT detection lines."""
    cmd = ["mosquitto_sub", "-h", BROKER_HOST, "-p", str(BROKER_PORT), "-t", TOPIC]
    print(f"[MQTT] Connecting to {BROKER_HOST}:{BROKER_PORT} on topic '{TOPIC}'...")

    while True:
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                now = time.time()
                recent_ts.append(now)

                if len(recent_ts) > 1:
                    fps = (len(recent_ts) - 1) / (recent_ts[-1] - recent_ts[0])
                else:
                    fps = 0.0

                infer_ms = data.get("inference_ms", 0.0)
                seq = data.get("seq", 0)
                dets = data.get("detections", [])

                with telemetry_lock:
                    current_telemetry["fps"] = fps
                    current_telemetry["seq"] = seq
                    current_telemetry["infer_ms"] = infer_ms
                    current_telemetry["detections"] = dets
                    current_telemetry["total_streamed"] += 1
                    current_telemetry["status"] = "streaming"
                    payload = json.dumps(current_telemetry)

                # Broadcast to active web SSE clients
                with subscribers_lock:
                    for q in list(subscribers):
                        try:
                            q.put_nowait(payload)
                        except queue.Full:
                            pass

        except Exception as e:
            print(f"[MQTT] Error in reader thread: {e}. Retrying in 2s...")
            time.sleep(2)

def main():
    # Start MQTT collector background daemon
    t = threading.Thread(target=mqtt_collector_thread, daemon=True)
    t.start()

    server = ThreadedHTTPServer(("0.0.0.0", PORT), SSEHandler)
    print(f"\n=======================================================")
    print(f"  EdgeML Jetson Nano — Interactive Web Dashboard")
    print(f"  URL: http://localhost:{PORT}")
    print(f"  MQTT Source: {BROKER_HOST}:{BROKER_PORT} [{TOPIC}]")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web dashboard server...")
        server.server_close()

if __name__ == "__main__":
    main()
