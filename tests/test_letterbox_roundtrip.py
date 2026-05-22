import numpy as np
from src.letterbox import LetterboxMeta, bbox_src_to_letterbox, bbox_letterbox_to_src

def test_roundtrip_error_under_one_px():
    for w,h in [(1920,1080),(1280,720),(640,480),(720,1280),(853,480)]:
        s=min(640/w,640/h); px=(640-int(round(w*s)))//2; py=(640-int(round(h*s)))//2
        meta=LetterboxMeta(w,h,640,s,px,py)
        boxes=np.array([[0,0,w,h],[10,20,w-30,h-40],[w*.25,h*.2,w*.75,h*.8]],dtype=np.float32)
        for b in boxes:
            lb=bbox_src_to_letterbox(b,meta)
            back=bbox_letterbox_to_src(lb,meta)
            assert np.max(np.abs(back-b)) < 1.0
