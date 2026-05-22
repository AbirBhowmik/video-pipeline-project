import cv2, threading, time, sys

class CaptureThread(threading.Thread):
    def __init__(self, name, path, slot, stop_event, metrics):
        super().__init__(name=name, daemon=False)
        self.path=path; self.slot=slot; self.stop=stop_event; self.metrics=metrics
    def open_cap(self):
        cap=cv2.VideoCapture(self.path, cv2.CAP_FFMPEG)
        if not cap.isOpened(): raise RuntimeError(f'cannot open {self.path}')
        return cap
    def run(self):
        cap=None; wall0=None; pts0=None; last_pts=None
        try:
            cap=self.open_cap()
            while not self.stop.is_set():
                ok,frame=cap.read()
                if not ok or frame is None:
                    self.metrics['recovery_count']+=1
                    cap.set(cv2.CAP_PROP_POS_FRAMES,0); wall0=None; pts0=None; last_pts=None
                    continue
                pts=cap.get(cv2.CAP_PROP_POS_MSEC)
                if pts<=0 and last_pts is not None:
                    fps=cap.get(cv2.CAP_PROP_FPS) or 30.0; pts=last_pts+1000.0/fps
                if wall0 is None:
                    wall0=time.monotonic(); pts0=pts
                target=wall0+(pts-pts0)/1000.0
                while not self.stop.is_set():
                    remain=target-time.monotonic()
                    if remain<=0: break
                    self.stop.wait(min(remain,0.05))
                if self.stop.is_set(): break
                self.slot.put(self.name,frame,pts)
                self.metrics['capture_count']+=1
                last_pts=pts
        except Exception as e:
            print(f'{self.name} fatal: {e}', file=sys.stderr)
            self.stop.set()
        finally:
            if cap is not None: cap.release()
