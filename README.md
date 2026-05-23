# Video Pipeline Task

CPU-only real-time video pipeline for `demo.mp4`.

## Overview

This project opens `demo.mp4` twice as two independent simulated camera streams:

- `cam_a`
- `cam_b`

Each stream runs in its own capture thread using `cv2.VideoCapture(path, cv2.CAP_FFMPEG)`.

Frames are decoded with real-time pacing using frame timestamps, not `time.sleep(1/fps)`. The video loops on EOF, latest-frame-wins buffering is used, one consumer thread processes both streams, accepted frames are quality checked and preprocessed to letterboxed `640x640` NCHW `float32`, and JSON metrics are emitted every 5 seconds per stream.

## Project Structure

```text
video_pipeline_project/
├── src/
│   ├── __init__.py
│   ├── capture.py
│   ├── consumer.py
│   ├── letterbox.py
│   ├── metrics.py
│   ├── quality.py
│   └── slot.py
├── scripts/
│   └── pick_thresholds.py
├── tests/
│   ├── conftest.py
│   └── test_letterbox_roundtrip.py
├── run.py
├── REPORT.md
├── README.md
└── requirements.txt
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Place `demo.mp4` in the project root:

```text
video_pipeline_project/demo.mp4
```

## Run

Default run:

```bash
python run.py --input demo.mp4
```

Short 30-second check:

```bash
python run.py --input demo.mp4 --duration 30
```

Required 10-minute soak test:

```bash
python run.py --input demo.mp4 --duration 600
```

The 10-minute soak should take about 10 real minutes. It should not complete in 30 seconds.

## Threshold Experiment

Run the threshold experiment:

```bash
python -m scripts.pick_thresholds --input demo.mp4 --out threshold_plots
```

This generates plots in:

```text
threshold_plots/
```

Example threshold output from my run:

```text
recommended thresholds:
blur_min=50.00
luma_min=82.91, luma_max=136.14, clip_max=0.0356
phash_min_dist=3
plots saved in threshold_plots/
```

The quality gate checks:

- blur using variance of Laplacian
- exposure using mean luma and clipped-pixel ratio
- stuck frames using perceptual hash distance against the previous accepted frame

## Tests

Run:

```bash
pytest -q
```

Expected output:

```text
1 passed in 2.72s and 0.9s
```

The test checks that bounding-box conversion has less than 1 pixel round-trip error:

```text
source coords -> letterbox coords -> source coords
```

## Example Metrics

The pipeline emits JSON metrics every 5 seconds per stream.

Example:


```json
{
  "stream": "cam_a",
  "fps_capture": 29.81,
  "fps_preprocess": 7.8,
  "frame_age_ms_p50": 22.34,
  "frame_age_ms_p99": 42.09,
  "frames_dropped": 78,
  "recovery_count": 0,
  "quality_counters": {
    "blur": 0,
    "exposure": 0,
    "stuck": 31
  },
  "rss_mb": 261.25
}{
  "stream": "cam_b",
  "fps_capture": 29.61,
  "fps_preprocess": 7.0,
  "frame_age_ms_p50": 21.02,
  "frame_age_ms_p99": 41.9,
  "frames_dropped": 77,
  "recovery_count": 0,
  "quality_counters": {
    "blur": 0,
    "exposure": 0,
    "stuck": 34
  },
  "rss_mb": 264.62
}
```

## Preprocessing Benchmark

Accepted frames are converted to letterboxed `640x640` NCHW `float32`.

Two preprocessing implementations are included:

1. `cv2.dnn.blobFromImage`
2. hand-written NumPy preprocessing

The preprocessing benchmark was tested on two systems: a laptop with 4 GB RAM and a desktop with 32 GB RAM.

### Laptop, 4 GB RAM

```text
cam_a preprocess_bench_ms cv2=11.030 numpy=12.205
cam_b preprocess_bench_ms cv2=10.712 numpy=12.180
```

### Desktop, 32 GB RAM

```text
cam_a preprocess_bench_ms cv2=4.552 numpy=5.223
cam_b preprocess_bench_ms cv2=4.482 numpy=5.224

## Shutdown

Press `Ctrl+C` to stop the pipeline.

The program uses a shared stop event and joins worker threads cleanly. It does not use `sys.exit()` as a SIGINT handler.

## Notes

- No GPU is required.
- No cloud service is used.
- No LLM is used.
- No unbounded `queue.Queue()` is used.
- Real-time pacing uses frame timestamps.
- The video loops on EOF to support the 10-minute soak test.
- JSON metrics include p50 and p99 frame age, not only average FPS.
