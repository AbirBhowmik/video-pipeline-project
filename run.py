import argparse, signal, threading, time
from src.slot import LatestFrameSlot
from src.capture import CaptureThread
from src.consumer import ConsumerThread
from src.metrics import new_metrics, emit
from src.quality import QualityThresholds

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--duration', type=float, default=600)
    ap.add_argument('--metrics-interval', type=float, default=5)
    args=ap.parse_args()
    stop=threading.Event()
    def on_sigint(signum, frame): stop.set()
    signal.signal(signal.SIGINT,on_sigint)
    slots={n:LatestFrameSlot() for n in ('cam_a','cam_b')}
    metrics={n:new_metrics() for n in slots}
    th=QualityThresholds()
    caps=[CaptureThread(n,args.input,slots[n],stop,metrics[n]) for n in slots]
    consumer=threading.Thread(target=ConsumerThread(slots,stop,metrics,th).run, name='consumer', daemon=False)
    for t in caps: t.start()
    consumer.start()
    prev={n:{'t':time.monotonic(),'cap':0,'prep':0} for n in slots}; start=time.monotonic()
    try:
        while not stop.is_set() and time.monotonic()-start<args.duration:
            stop.wait(args.metrics_interval)
            _,prev=emit(metrics,slots,args.metrics_interval,prev)
    finally:
        stop.set(); deadline=time.monotonic()+2.0
        for t in caps+[consumer]: t.join(max(0,deadline-time.monotonic()))
        alive=[t.name for t in caps+[consumer] if t.is_alive()]
        if alive: raise SystemExit(f'threads still alive: {alive}')
        for n,m in metrics.items():
            if m.get('bench_cv2_ms'):
                import statistics as st
                print(f'{n} preprocess_bench_ms cv2={st.median(m["bench_cv2_ms"]):.3f} numpy={st.median(m["bench_numpy_ms"]):.3f}', flush=True)

if __name__=='__main__': main()
