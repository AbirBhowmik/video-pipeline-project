# Video Pipeline Report

## Summary

This project implements a CPU-only real-time video pipeline for `demo.mp4`. The same recorded video is opened twice as two independent simulated cameras, `cam_a` and `cam_b`, with each stream running in its own `cv2.VideoCapture(path, cv2.CAP_FFMPEG)` capture thread. A single consumer thread reads the newest available frame from each stream, applies quality checks, preprocesses accepted frames to letterboxed `640x640` NCHW `float32`, and emits JSON metrics every 5 seconds.

## Threshold Experiment

Thresholds were selected using `scripts/pick_thresholds.py` on `demo.mp4`, not chosen randomly. The experiment measured blur using variance of Laplacian, exposure using mean luma and clipped-pixel ratio, and frame similarity using perceptual hash distance. The resulting thresholds were:

```text
blur_min = 1400.98
luma_min = 118.62
luma_max = 154.26
clip_max = 0.0221
phash_min_dist = 3
```

Histogram plots were generated in `threshold_plots/` to justify these values.

## Test and Benchmark Results

The letterbox inverse-transform unit test passed:

```text
pytest -q -> 1 passed
```

The preprocessing benchmark from the run was:

```text
cam_a preprocess_bench_ms cv2=4.839 numpy=5.329
cam_b preprocess_bench_ms cv2=4.775 numpy=5.269
```

During the observed run, capture FPS stayed close to 12 FPS per stream, which indicates that real-time pacing was respected for this source video.

## 1. Real-Time Throttling

Each capture thread reads the frame timestamp with `cv2.CAP_PROP_POS_MSEC` and maps that video timestamp to a target wall-clock time. The thread waits using `stop_event.wait(...)`, so it does not busy-wait and can also wake quickly on shutdown. This works for variable-FPS input because the delay is computed from each frame's own timestamp rather than assuming a fixed `1/fps` interval. If timestamp data is missing, the code uses FPS only as a fallback.

## 2. Latest-Frame-Wins Mechanism

Each stream has one bounded latest-frame slot instead of an unbounded queue. The capture thread overwrites an unread frame with the newest frame and increments the dropped-frame counter, so old frames cannot build up and increase latency. The producer only holds the slot lock briefly and never waits for the consumer to finish processing; the consumer waits only with a timeout. If the consumer is faster it waits briefly, if it is slower frames are overwritten, and if both run at similar speed frames are read normally, so neither side can wait forever.

## 3. `cv2.dnn.blobFromImage` vs NumPy

`cv2.dnn.blobFromImage` is fast because OpenCV performs resize-related image operations, scaling, channel conversion, and NCHW layout conversion in optimized native code. The NumPy version loses time because it creates intermediate arrays for BGR-to-RGB conversion, `float32` conversion, normalization, and transpose. In the measured run, OpenCV took about 4.8 to 4.9 ms per frame while NumPy took about 5.3 ms per frame. NumPy was therefore about 0.5 ms slower per frame, roughly 10% slower in this run.

## 4. `VideoCapture.read()` Failure Handling

In this pipeline, `VideoCapture.read()` is treated as recoverable when it returns `ok=False` or `frame is None`. That condition is used for EOF and possible read/decode failure, so the code increments `recovery_count`, seeks to frame 0, resets timing state, and continues. I did not try to classify arbitrary returned image content as a decode glitch because OpenCV can still return `ok=True` with an image-like frame. A true hang is not represented as a returned `(ok, frame)` result, so the practical recoverable case handled here is `(False, None)` or any failed/empty frame result.

## 5. Least Confident Measurement

The measurement I am least confident about is RSS stability. The observed RSS range was roughly 155 MB to 181 MB, but a single local 10-minute run can be affected by operating-system caching, Python allocation behavior, and short-term measurement noise. I would strengthen this result by logging RSS to CSV over several longer runs, plotting memory over time, and checking that the trend line does not steadily increase. I would also include that plot with the final evidence artifacts.

## Soak and Shutdown Notes

The required soak command is:

```bash
python run.py --input demo.mp4 --duration 600
```

This should run for about 10 real minutes because pacing is based on frame timestamps. `Ctrl+C` shutdown uses a shared stop event and thread joins rather than calling `sys.exit()` directly, so worker threads are given a clean path to exit. The video loops on EOF by seeking back to frame 0, allowing a short `demo.mp4` to cover the full soak duration.
