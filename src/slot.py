import threading, time
from dataclasses import dataclass

@dataclass
class FramePacket:
    stream:str; frame:object; src_ts_ms:float; captured_mono:float; seq:int

class LatestFrameSlot:
    def __init__(self):
        self._cv=threading.Condition(); self._pkt=None; self._seq=0; self._last_read=0; self.dropped=0
    def put(self, stream, frame, src_ts_ms):
        with self._cv:
            if self._pkt is not None and self._seq>self._last_read: self.dropped+=1
            self._seq+=1
            self._pkt=FramePacket(stream, frame, src_ts_ms, time.monotonic(), self._seq)
            self._cv.notify_all()
    def get_latest(self, timeout=0.2):
        with self._cv:
            if self._seq==self._last_read: self._cv.wait(timeout)
            if self._pkt is None or self._seq==self._last_read: return None
            self._last_read=self._seq
            return self._pkt
