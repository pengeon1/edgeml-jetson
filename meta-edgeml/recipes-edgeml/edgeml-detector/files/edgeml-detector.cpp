// edgeml-detector: webcam (V4L2, YUYV) -> YOLOv5 TensorRT engine -> MQTT (JSON).
//
// Features:
//   - Pipelined multithreaded double/triple buffering (overlaps CPU preprocessing with GPU inference)
//   - Zero-copy V4L2 mmap capture with frame drop avoidance
//   - Standalone minimal MQTT 3.1.1 publisher (no extra libraries required)
//   - Configurable via environment variables (/etc/edgeml/detector.conf)
//
// Configuration comes from environment variables (see /etc/edgeml/detector.conf):
//   EDGEML_ENGINE   serialized TensorRT engine   (default /var/lib/edgeml/yolov5n_fp16.engine)
//   EDGEML_CAMERA   V4L2 device                  (default /dev/video0)
//   EDGEML_BROKER   MQTT broker host or IPv4     (default 192.168.55.100)
//   EDGEML_PORT     MQTT broker port             (default 1883)
//   EDGEML_TOPIC    MQTT topic                   (default edgeml/detections)
//   EDGEML_CONF     confidence threshold         (default 0.35)
//   EDGEML_NMS      NMS IoU threshold            (default 0.45)
// Options: --frames N (stop after N frames), --no-mqtt, --sync (sequential mode), --help
//
// The engine must have one FP32 input [1,3,S,S] and one FP32 output [1,N,5+classes]
// (the standard YOLOv5 ONNX export, built with trtexec --fp16).
#include <NvInfer.h>
#include <cuda_runtime_api.h>

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/videodev2.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#include <algorithm>
#include <cmath>
#include <condition_variable>
#include <fstream>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

static volatile sig_atomic_t g_stop = 0;
static void on_signal(int) { g_stop = 1; }

static std::string env_str(const char* k, const char* d) {
  const char* v = getenv(k);
  return (v && *v) ? v : d;
}
static double env_num(const char* k, double d) {
  const char* v = getenv(k);
  return (v && *v) ? atof(v) : d;
}
static double now_ms() {
  timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec * 1e3 + ts.tv_nsec / 1e6;
}
static long long wall_ms() {
  timeval tv;
  gettimeofday(&tv, nullptr);
  return (long long)tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

static const char* kNames[80] = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush"};

// ---------------------------------------------------------------- camera
struct Camera {
  struct Buf { void* p; size_t len; };
  int fd = -1, w = 0, h = 0, stride = 0;
  std::vector<Buf> bufs;
  double last_ts_ms = -1;  // capture time of the last frame (CLOCK_MONOTONIC), or -1

  bool open_dev(const std::string& dev, int rw, int rh, int fps) {
    fd = ::open(dev.c_str(), O_RDWR | O_NONBLOCK);
    if (fd < 0) { perror("open camera"); return false; }
    v4l2_capability cap;
    if (ioctl(fd, VIDIOC_QUERYCAP, &cap) < 0 || !(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE) ||
        !(cap.capabilities & V4L2_CAP_STREAMING)) {
      fprintf(stderr, "%s is not a streaming capture device\n", dev.c_str());
      return false;
    }
    v4l2_format f;
    memset(&f, 0, sizeof f);
    f.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    f.fmt.pix.width = rw;
    f.fmt.pix.height = rh;
    f.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
    f.fmt.pix.field = V4L2_FIELD_ANY;
    if (ioctl(fd, VIDIOC_S_FMT, &f) < 0) { perror("VIDIOC_S_FMT"); return false; }
    if (f.fmt.pix.pixelformat != V4L2_PIX_FMT_YUYV) {
      fprintf(stderr, "camera does not offer YUYV\n");
      return false;
    }
    w = f.fmt.pix.width;
    h = f.fmt.pix.height;
    stride = f.fmt.pix.bytesperline ? f.fmt.pix.bytesperline : w * 2;

    v4l2_streamparm p;
    memset(&p, 0, sizeof p);
    p.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    p.parm.capture.timeperframe.numerator = 1;
    p.parm.capture.timeperframe.denominator = fps;
    ioctl(fd, VIDIOC_S_PARM, &p);  // best effort

    v4l2_control c;  // do not let auto exposure halve the frame rate in dim light
    memset(&c, 0, sizeof c);
    c.id = V4L2_CID_EXPOSURE_AUTO_PRIORITY;
    c.value = 0;
    ioctl(fd, VIDIOC_S_CTRL, &c);  // best effort

    v4l2_requestbuffers rb;
    memset(&rb, 0, sizeof rb);
    rb.count = 4;
    rb.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    rb.memory = V4L2_MEMORY_MMAP;
    if (ioctl(fd, VIDIOC_REQBUFS, &rb) < 0) { perror("VIDIOC_REQBUFS"); return false; }
    for (unsigned i = 0; i < rb.count; i++) {
      v4l2_buffer b;
      memset(&b, 0, sizeof b);
      b.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
      b.memory = V4L2_MEMORY_MMAP;
      b.index = i;
      if (ioctl(fd, VIDIOC_QUERYBUF, &b) < 0) { perror("VIDIOC_QUERYBUF"); return false; }
      void* m = mmap(nullptr, b.length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, b.m.offset);
      if (m == MAP_FAILED) { perror("mmap"); return false; }
      bufs.push_back({m, b.length});
      if (ioctl(fd, VIDIOC_QBUF, &b) < 0) { perror("VIDIOC_QBUF"); return false; }
    }
    int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (ioctl(fd, VIDIOC_STREAMON, &type) < 0) { perror("VIDIOC_STREAMON"); return false; }
    return true;
  }

  // Waits for a frame and returns the NEWEST one, giving older queued frames back.
  int grab(int timeout_ms) {
    pollfd pf;
    pf.fd = fd;
    pf.events = POLLIN;
    pf.revents = 0;
    if (poll(&pf, 1, timeout_ms) <= 0) return -1;
    if (pf.revents & (POLLERR | POLLHUP | POLLNVAL)) return -1;
    int last = -1;
    for (;;) {
      v4l2_buffer b;
      memset(&b, 0, sizeof b);
      b.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
      b.memory = V4L2_MEMORY_MMAP;
      if (ioctl(fd, VIDIOC_DQBUF, &b) < 0) break;
      if (last >= 0) release(last);
      last = b.index;
      last_ts_ms = (b.flags & V4L2_BUF_FLAG_TIMESTAMP_MONOTONIC)
                       ? b.timestamp.tv_sec * 1e3 + b.timestamp.tv_usec / 1e3
                       : -1;
    }
    return last;
  }
  void release(int i) {
    v4l2_buffer b;
    memset(&b, 0, sizeof b);
    b.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    b.memory = V4L2_MEMORY_MMAP;
    b.index = i;
    ioctl(fd, VIDIOC_QBUF, &b);
  }
};

// ------------------------------------------------- pre- and post-processing
struct Letterbox {
  float scale = 1;
  int dx = 0, dy = 0, nw = 0, nh = 0;
  std::vector<int> xmap, ymap;
};
static Letterbox make_letterbox(int w, int h, int in) {
  Letterbox l;
  l.scale = std::min((float)in / w, (float)in / h);
  l.nw = (int)std::lround(w * l.scale);
  l.nh = (int)std::lround(h * l.scale);
  l.dx = (in - l.nw) / 2;
  l.dy = (in - l.nh) / 2;
  for (int x = 0; x < l.nw; x++) l.xmap.push_back(std::min(w - 1, (int)(x / l.scale)));
  for (int y = 0; y < l.nh; y++) l.ymap.push_back(std::min(h - 1, (int)(y / l.scale)));
  return l;
}
static inline float clamp255(float v) { return v < 0 ? 0 : (v > 255 ? 255 : v); }

// YUYV frame -> planar RGB float in [0,1], letterboxed to in x in with grey padding.
static void preprocess(const uint8_t* yuyv, int stride, int in, const Letterbox& lb, float* dst) {
  const size_t plane = (size_t)in * in;
  std::fill(dst, dst + 3 * plane, 114.f / 255.f);
  for (int y = 0; y < lb.nh; y++) {
    const uint8_t* row = yuyv + (size_t)lb.ymap[y] * stride;
    float* r = dst + (size_t)(y + lb.dy) * in + lb.dx;
    float* g = r + plane;
    float* b = r + 2 * plane;
    for (int x = 0; x < lb.nw; x++) {
      int sx = lb.xmap[x];
      const uint8_t* px = row + (size_t)(sx & ~1) * 2;  // bytes: Y0 U Y1 V
      float Y = (sx & 1) ? px[2] : px[0];
      float U = px[1] - 128.f, V = px[3] - 128.f;
      r[x] = clamp255(Y + 1.402f * V) * (1.f / 255.f);
      g[x] = clamp255(Y - 0.344136f * U - 0.714136f * V) * (1.f / 255.f);
      b[x] = clamp255(Y + 1.772f * U) * (1.f / 255.f);
    }
  }
}

struct Det { float x1, y1, x2, y2, score; int cls; };
static float iou(const Det& a, const Det& b) {
  float ix = std::max(0.f, std::min(a.x2, b.x2) - std::max(a.x1, b.x1));
  float iy = std::max(0.f, std::min(a.y2, b.y2) - std::max(a.y1, b.y1));
  float inter = ix * iy;
  float u = (a.x2 - a.x1) * (a.y2 - a.y1) + (b.x2 - b.x1) * (b.y2 - b.y1) - inter;
  return u > 0 ? inter / u : 0;
}
// out: n rows of (cx, cy, w, h, objectness, class scores...), in network input pixels.
static std::vector<Det> decode(const float* out, int n, int row_len, const Letterbox& lb,
                               int fw, int fh, float conf, float nms_thr) {
  const int nc = row_len - 5;
  std::vector<Det> cand;
  for (int i = 0; i < n; i++) {
    const float* r = out + (size_t)i * row_len;
    if (r[4] < conf) continue;
    int bc = 0;
    float bs = r[5];
    for (int c = 1; c < nc; c++)
      if (r[5 + c] > bs) { bs = r[5 + c]; bc = c; }
    float s = r[4] * bs;
    if (s < conf) continue;
    Det d;
    d.x1 = std::min(std::max((r[0] - r[2] / 2 - lb.dx) / lb.scale, 0.f), (float)(fw - 1));
    d.y1 = std::min(std::max((r[1] - r[3] / 2 - lb.dy) / lb.scale, 0.f), (float)(fh - 1));
    d.x2 = std::min(std::max((r[0] + r[2] / 2 - lb.dx) / lb.scale, 0.f), (float)(fw - 1));
    d.y2 = std::min(std::max((r[1] + r[3] / 2 - lb.dy) / lb.scale, 0.f), (float)(fh - 1));
    d.score = s;
    d.cls = bc;
    cand.push_back(d);
  }
  std::sort(cand.begin(), cand.end(), [](const Det& a, const Det& b) { return a.score > b.score; });
  if (cand.size() > 300) cand.resize(300);
  std::vector<Det> keep;
  for (const Det& d : cand) {
    bool ok = true;
    for (const Det& k : keep)
      if (k.cls == d.cls && iou(k, d) > nms_thr) { ok = false; break; }
    if (ok) keep.push_back(d);
  }
  return keep;
}

// ------------------------------------------------------------------ MQTT
// Minimal MQTT 3.1.1 publisher: CONNECT, then QoS 0 PUBLISH. Keep-alive is disabled.
struct Mqtt {
  std::string host, client, topic;
  int port = 1883, fd = -1;
  double next_try = 0;

  static void put_str(std::vector<uint8_t>& v, const std::string& s) {
    v.push_back((uint8_t)(s.size() >> 8));
    v.push_back((uint8_t)(s.size() & 255));
    v.insert(v.end(), s.begin(), s.end());
  }
  static void put_len(std::vector<uint8_t>& v, size_t n) {
    do {
      uint8_t b = n % 128;
      n /= 128;
      if (n) b |= 0x80;
      v.push_back(b);
    } while (n);
  }
  bool send_all(const std::vector<uint8_t>& v) {
    size_t off = 0;
    while (off < v.size()) {
      ssize_t r = send(fd, v.data() + off, v.size() - off, MSG_NOSIGNAL);
      if (r <= 0) return false;
      off += (size_t)r;
    }
    return true;
  }
  void drop() {
    if (fd >= 0) close(fd);
    fd = -1;
  }
  int connect_tcp() {
    addrinfo hints, *res = nullptr;
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(host.c_str(), std::to_string(port).c_str(), &hints, &res) != 0 || !res) return -1;
    int s = socket(res->ai_family, res->ai_socktype, 0);
    if (s < 0) { freeaddrinfo(res); return -1; }
    fcntl(s, F_SETFL, fcntl(s, F_GETFL, 0) | O_NONBLOCK);
    int rc = connect(s, res->ai_addr, res->ai_addrlen);
    freeaddrinfo(res);
    if (rc < 0 && errno != EINPROGRESS) { close(s); return -1; }
    pollfd pf;
    pf.fd = s;
    pf.events = POLLOUT;
    pf.revents = 0;
    int err = 0;
    socklen_t el = sizeof err;
    if (poll(&pf, 1, 1000) <= 0 || getsockopt(s, SOL_SOCKET, SO_ERROR, &err, &el) < 0 || err) {
      close(s);
      return -1;
    }
    fcntl(s, F_SETFL, fcntl(s, F_GETFL, 0) & ~O_NONBLOCK);
    timeval tv = {1, 0};
    setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof tv);
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
    int one = 1;
    setsockopt(s, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
    return s;
  }
  bool ensure() {
    if (fd >= 0) return true;
    double t = now_ms();
    if (t < next_try) return false;
    next_try = t + 3000;
    fd = connect_tcp();
    if (fd < 0) return false;
    std::vector<uint8_t> body;
    put_str(body, "MQTT");
    body.push_back(4);     // protocol level 3.1.1
    body.push_back(0x02);  // clean session
    body.push_back(0);     // keep-alive 0 = disabled
    body.push_back(0);
    put_str(body, client);
    std::vector<uint8_t> pkt;
    pkt.push_back(0x10);
    put_len(pkt, body.size());
    pkt.insert(pkt.end(), body.begin(), body.end());
    uint8_t ack[4];
    if (!send_all(pkt) || recv(fd, ack, 4, MSG_WAITALL) != 4 || ack[0] != 0x20 || ack[3] != 0) {
      drop();
      return false;
    }
    fprintf(stderr, "mqtt: connected to %s:%d\n", host.c_str(), port);
    return true;
  }
  bool publish(const std::string& payload) {
    if (!ensure()) return false;
    std::vector<uint8_t> body;
    put_str(body, topic);
    body.insert(body.end(), payload.begin(), payload.end());
    std::vector<uint8_t> pkt;
    pkt.push_back(0x30);
    put_len(pkt, body.size());
    pkt.insert(pkt.end(), body.begin(), body.end());
    if (!send_all(pkt)) {
      fprintf(stderr, "mqtt: connection lost\n");
      drop();
      return false;
    }
    return true;
  }
};

// ------------------------------------------------------------- TensorRT
class Logger : public nvinfer1::ILogger {
 public:
  void log(Severity s, const char* msg) noexcept override {
    if (s <= Severity::kWARNING) fprintf(stderr, "[trt] %s\n", msg);
  }
};
static size_t volume(const nvinfer1::Dims& d) {
  size_t v = 1;
  for (int i = 0; i < d.nbDims; i++) v *= (size_t)d.d[i];
  return v;
}
#define CUDA_OK(call)                                                           \
  do {                                                                          \
    cudaError_t e_ = (call);                                                    \
    if (e_ != cudaSuccess) {                                                    \
      fprintf(stderr, "CUDA error %d at %s:%d\n", (int)e_, __FILE__, __LINE__); \
      return 1;                                                                 \
    }                                                                           \
  } while (0)

struct PipelinedSlot {
  float* h_in = nullptr;
  double capture_ts = -1;
  double prep_ms = 0;
  long seq = 0;
};

int main(int argc, char** argv) {
  long max_frames = -1;
  bool use_mqtt = true;
  bool pipelined = true;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--frames") && i + 1 < argc) max_frames = atol(argv[++i]);
    else if (!strcmp(argv[i], "--no-mqtt")) use_mqtt = false;
    else if (!strcmp(argv[i], "--sync")) pipelined = false;
    else {
      printf("usage: edgeml-detector [--frames N] [--no-mqtt] [--sync]\nsettings: environment variables, see /etc/edgeml/detector.conf\n");
      return !strcmp(argv[i], "--help") ? 0 : 2;
    }
  }

  const std::string engine_path = env_str("EDGEML_ENGINE", "/var/lib/edgeml/yolov5n_fp16.engine");
  const std::string cam_dev = env_str("EDGEML_CAMERA", "/dev/video0");
  const float conf = (float)env_num("EDGEML_CONF", 0.35);
  const float nms_thr = (float)env_num("EDGEML_NMS", 0.45);
  const double target_fps = env_num("EDGEML_FPS_LIMIT", 0.0);
  Mqtt mqtt;
  mqtt.host = env_str("EDGEML_BROKER", "192.168.55.100");
  mqtt.port = (int)env_num("EDGEML_PORT", 1883);
  mqtt.topic = env_str("EDGEML_TOPIC", "edgeml/detections");
  mqtt.client = "edgeml-detector-" + std::to_string((int)getpid());

  signal(SIGINT, on_signal);
  signal(SIGTERM, on_signal);

  std::ifstream ef(engine_path, std::ios::binary);
  if (!ef) { fprintf(stderr, "cannot open engine %s\n", engine_path.c_str()); return 1; }
  std::vector<char> blob((std::istreambuf_iterator<char>(ef)), std::istreambuf_iterator<char>());
  static Logger logger;
  nvinfer1::IRuntime* runtime = nvinfer1::createInferRuntime(logger);
  nvinfer1::ICudaEngine* engine = runtime ? runtime->deserializeCudaEngine(blob.data(), blob.size(), nullptr) : nullptr;
  if (!engine) { fprintf(stderr, "cannot deserialize %s (built with another TensorRT?)\n", engine_path.c_str()); return 1; }
  nvinfer1::IExecutionContext* ctx = engine->createExecutionContext();
  if (!ctx) { fprintf(stderr, "cannot create execution context\n"); return 1; }

  int in_idx = -1, out_idx = -1;
  for (int i = 0; i < engine->getNbBindings(); i++) {
    if (engine->bindingIsInput(i)) { if (in_idx < 0) in_idx = i; }
    else if (out_idx < 0) out_idx = i;
  }
  if (in_idx < 0 || out_idx < 0) { fprintf(stderr, "engine needs one input and one output\n"); return 1; }
  nvinfer1::Dims in_d = engine->getBindingDimensions(in_idx);
  nvinfer1::Dims out_d = engine->getBindingDimensions(out_idx);
  if (engine->getBindingDataType(in_idx) != nvinfer1::DataType::kFLOAT ||
      engine->getBindingDataType(out_idx) != nvinfer1::DataType::kFLOAT || in_d.nbDims != 4 ||
      in_d.d[1] != 3 || in_d.d[2] != in_d.d[3] || out_d.nbDims != 3 || out_d.d[0] != 1) {
    fprintf(stderr, "unexpected engine shapes or data types (need FP32 [1,3,S,S] -> [1,N,5+C])\n");
    return 1;
  }
  const int S = in_d.d[2], rows = out_d.d[1], row_len = out_d.d[2];
  const size_t in_bytes = volume(in_d) * sizeof(float), out_bytes = volume(out_d) * sizeof(float);
  void *d_in = nullptr, *d_out = nullptr;
  float *h_out = nullptr;
  cudaStream_t stream;
  CUDA_OK(cudaMalloc(&d_in, in_bytes));
  CUDA_OK(cudaMalloc(&d_out, out_bytes));
  CUDA_OK(cudaMallocHost((void**)&h_out, out_bytes));
  CUDA_OK(cudaStreamCreate(&stream));
  std::vector<void*> bindings(engine->getNbBindings(), nullptr);
  bindings[in_idx] = d_in;
  bindings[out_idx] = d_out;

  // Allocate 3 host pinned buffers for non-blocking double/triple-buffering
  constexpr int kNumSlots = 3;
  PipelinedSlot slots[kNumSlots];
  for (int i = 0; i < kNumSlots; i++) {
    CUDA_OK(cudaMallocHost((void**)&slots[i].h_in, in_bytes));
  }

  Camera cam;
  if (!cam.open_dev(cam_dev, 640, 480, 30)) return 1;
  Letterbox lb = make_letterbox(cam.w, cam.h, S);
  fprintf(stderr, "ready: camera %dx%d, network %dx%d, %d candidates, topic %s on %s:%d, mode: %s\n",
          cam.w, cam.h, S, S, rows, mqtt.topic.c_str(), mqtt.host.c_str(), mqtt.port,
          pipelined ? "pipelined (triple-buffered)" : "sync (sequential)");

  long cons_seq = 0, win_frames = 0, win_dets = 0;
  double win_start = now_ms(), s_pre = 0, s_inf = 0, s_post = 0, s_e2e = 0;
  long e2e_n = 0;
  bool mqtt_ok = false;

  if (pipelined) {
    std::mutex mtx;
    std::condition_variable cv_ready;
    std::vector<int> free_slots = {0, 1, 2};
    int ready_slot = -1;
    bool has_ready = false;
    long prod_seq = 0;

    // Stage 1 Producer thread: continuous camera grab + CPU letterbox preprocessing
    std::thread prod_thread([&]() {
      while (!g_stop && (max_frames < 0 || prod_seq < max_frames)) {
        int idx = cam.grab(2000);
        if (idx < 0) {
          std::this_thread::sleep_for(std::chrono::milliseconds(50));
          continue;
        }
        double frame_ts = cam.last_ts_ms;

        int slot = -1;
        {
          std::unique_lock<std::mutex> lk(mtx);
          if (!free_slots.empty()) {
            slot = free_slots.back();
            free_slots.pop_back();
          } else if (has_ready) {
            // Drop unconsumed ready slot to always supply freshest frame
            slot = ready_slot;
            has_ready = false;
          }
        }

        if (slot < 0) {
          cam.release(idx);
          continue;
        }

        double t0 = now_ms();
        preprocess((const uint8_t*)cam.bufs[idx].p, cam.stride, S, lb, slots[slot].h_in);
        cam.release(idx);
        double t1 = now_ms();

        slots[slot].capture_ts = frame_ts;
        slots[slot].prep_ms = t1 - t0;
        slots[slot].seq = prod_seq++;

        {
          std::unique_lock<std::mutex> lk(mtx);
          if (has_ready) {
            free_slots.push_back(ready_slot);
          }
          ready_slot = slot;
          has_ready = true;
          cv_ready.notify_one();
        }
      }
      {
        std::unique_lock<std::mutex> lk(mtx);
        cv_ready.notify_all();
      }
    });

    // Stage 2 Consumer: GPU inference + decode + MQTT publish
    while (!g_stop && (max_frames < 0 || cons_seq < max_frames)) {
      int cur = -1;
      {
        std::unique_lock<std::mutex> lk(mtx);
        cv_ready.wait(lk, [&] { return has_ready || g_stop; });
        if (g_stop && !has_ready) break;
        cur = ready_slot;
        has_ready = false;
      }

      double t1 = now_ms();
      CUDA_OK(cudaMemcpyAsync(d_in, slots[cur].h_in, in_bytes, cudaMemcpyHostToDevice, stream));
      if (!ctx->enqueueV2(bindings.data(), stream, nullptr)) {
        fprintf(stderr, "enqueue failed\n");
        g_stop = 1;
        break;
      }
      CUDA_OK(cudaMemcpyAsync(h_out, d_out, out_bytes, cudaMemcpyDeviceToHost, stream));
      CUDA_OK(cudaStreamSynchronize(stream));
      double t2 = now_ms();

      double prep_ms = slots[cur].prep_ms;
      double frame_ts = slots[cur].capture_ts;
      long cur_seq = slots[cur].seq;

      // Recycle host buffer back to free queue immediately after GPU work
      {
        std::unique_lock<std::mutex> lk(mtx);
        free_slots.push_back(cur);
      }

      std::vector<Det> dets = decode(h_out, rows, row_len, lb, cam.w, cam.h, conf, nms_thr);

      char head[256];
      snprintf(head, sizeof head,
               "{\"ts\":%lld,\"seq\":%ld,\"frame\":{\"w\":%d,\"h\":%d},\"inference_ms\":%.1f,\"detections\":[",
               wall_ms(), cur_seq, cam.w, cam.h, t2 - t1);
      std::string js = head;
      for (size_t i = 0; i < dets.size(); i++) {
        char one[200];
        snprintf(one, sizeof one,
                 "%s{\"label\":\"%s\",\"class\":%d,\"conf\":%.3f,\"box\":[%.0f,%.0f,%.0f,%.0f]}",
                 i ? "," : "", dets[i].cls < 80 ? kNames[dets[i].cls] : "unknown", dets[i].cls,
                 dets[i].score, dets[i].x1, dets[i].y1, dets[i].x2, dets[i].y2);
        js += one;
      }
      js += "]}";
      if (use_mqtt) mqtt_ok = mqtt.publish(js);
      double t3 = now_ms();
      if (frame_ts >= 0) { s_e2e += (now_ms() - frame_ts); e2e_n++; }

      if (target_fps > 0.0) {
        double frame_elapsed = now_ms() - t1;
        double frame_target = 1000.0 / target_fps;
        if (frame_elapsed < frame_target) {
          std::this_thread::sleep_for(std::chrono::milliseconds((long)(frame_target - frame_elapsed)));
        }
      }

      cons_seq++;
      win_frames++;
      win_dets += (long)dets.size();
      s_pre += prep_ms;
      s_inf += t2 - t1;
      s_post += t3 - t2;
      if (t3 - win_start >= 2000) {
        double sec = (t3 - win_start) / 1e3;
        printf("fps=%.1f pre=%.1fms infer=%.1fms post+mqtt=%.1fms capture_to_publish=%.1fms dets/frame=%.2f mqtt=%s (pipelined)\n",
               win_frames / sec, s_pre / win_frames, s_inf / win_frames, s_post / win_frames,
               e2e_n ? s_e2e / e2e_n : -1.0, (double)win_dets / win_frames,
               !use_mqtt ? "off" : (mqtt_ok ? "ok" : "down"));
        fflush(stdout);
        win_start = t3;
        win_frames = win_dets = e2e_n = 0;
        s_pre = s_inf = s_post = s_e2e = 0;
      }
    }

    g_stop = 1;
    cv_ready.notify_all();
    if (prod_thread.joinable()) prod_thread.join();

  } else {
    // Synchronous sequential fallback mode
    while (!g_stop && (max_frames < 0 || cons_seq < max_frames)) {
      int idx = cam.grab(2000);
      if (idx < 0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        continue;
      }
      double t0 = now_ms();
      double frame_ts = cam.last_ts_ms;
      preprocess((const uint8_t*)cam.bufs[idx].p, cam.stride, S, lb, slots[0].h_in);
      cam.release(idx);
      double t1 = now_ms();
      CUDA_OK(cudaMemcpyAsync(d_in, slots[0].h_in, in_bytes, cudaMemcpyHostToDevice, stream));
      if (!ctx->enqueueV2(bindings.data(), stream, nullptr)) { fprintf(stderr, "enqueue failed\n"); return 1; }
      CUDA_OK(cudaMemcpyAsync(h_out, d_out, out_bytes, cudaMemcpyDeviceToHost, stream));
      CUDA_OK(cudaStreamSynchronize(stream));
      double t2 = now_ms();
      std::vector<Det> dets = decode(h_out, rows, row_len, lb, cam.w, cam.h, conf, nms_thr);

      char head[256];
      snprintf(head, sizeof head, "{\"ts\":%lld,\"seq\":%ld,\"frame\":{\"w\":%d,\"h\":%d},\"inference_ms\":%.1f,\"detections\":[",
               wall_ms(), cons_seq, cam.w, cam.h, t2 - t1);
      std::string js = head;
      for (size_t i = 0; i < dets.size(); i++) {
        char one[200];
        snprintf(one, sizeof one, "%s{\"label\":\"%s\",\"class\":%d,\"conf\":%.3f,\"box\":[%.0f,%.0f,%.0f,%.0f]}",
                 i ? "," : "", dets[i].cls < 80 ? kNames[dets[i].cls] : "unknown", dets[i].cls,
                 dets[i].score, dets[i].x1, dets[i].y1, dets[i].x2, dets[i].y2);
        js += one;
      }
      js += "]}";
      if (use_mqtt) mqtt_ok = mqtt.publish(js);
      double t3 = now_ms();
      if (frame_ts >= 0) { s_e2e += (now_ms() - frame_ts); e2e_n++; }

      if (target_fps > 0.0) {
        double frame_elapsed = now_ms() - t1;
        double frame_target = 1000.0 / target_fps;
        if (frame_elapsed < frame_target) {
          std::this_thread::sleep_for(std::chrono::milliseconds((long)(frame_target - frame_elapsed)));
        }
      }

      cons_seq++;
      win_frames++;
      win_dets += (long)dets.size();
      s_pre += t1 - t0;
      s_inf += t2 - t1;
      s_post += t3 - t2;
      if (t3 - win_start >= 2000) {
        double sec = (t3 - win_start) / 1e3;
        printf("fps=%.1f pre=%.1fms infer=%.1fms post+mqtt=%.1fms capture_to_publish=%.1fms dets/frame=%.2f mqtt=%s\n",
               win_frames / sec, s_pre / win_frames, s_inf / win_frames, s_post / win_frames,
               e2e_n ? s_e2e / e2e_n : -1.0, (double)win_dets / win_frames,
               !use_mqtt ? "off" : (mqtt_ok ? "ok" : "down"));
        fflush(stdout);
        win_start = t3;
        win_frames = win_dets = e2e_n = 0;
        s_pre = s_inf = s_post = s_e2e = 0;
      }
    }
  }

  fprintf(stderr, "stopping after %ld frames\n", cons_seq);
  return 0;
}
