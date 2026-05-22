import time
from .quality import assess
from .letterbox import blob_cv2, blob_numpy

class ConsumerThread:
    def __init__(self, slots, stop_event, metrics, thresholds):
        self.slots=slots; self.stop=stop_event; self.metrics=metrics; self.th=thresholds; self.prev_hash={k:None for k in slots}
    def run(self):
        names=list(self.slots)
        while not self.stop.is_set():
            got=False
            for n in names:
                pkt=self.slots[n].get_latest(timeout=0.02)
                if pkt is None: continue
                got=True; m=self.metrics[n]
                m['ages'].append((time.monotonic()-pkt.captured_mono)*1000.0)
                ok,reasons,h,_=assess(pkt.frame,self.prev_hash[n],self.th)
                if not ok:
                    for r in reasons: m['quality_counters'][r]+=1
                    continue
                self.prev_hash[n]=h
                t0=time.perf_counter(); blob_cv2(pkt.frame); t1=time.perf_counter(); blob_numpy(pkt.frame); t2=time.perf_counter()
                m.setdefault('bench_cv2_ms',[]).append((t1-t0)*1000); m.setdefault('bench_numpy_ms',[]).append((t2-t1)*1000)
                m['preprocess_count']+=1
            if not got: self.stop.wait(0.005)
