from dataclasses import dataclass
import cv2, numpy as np

@dataclass
class QualityThresholds:
    blur_min:float=100.0
    luma_min:float=35.0
    luma_max:float=220.0
    clip_max:float=0.05
    phash_min_dist:int=3

def phash(img):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    small=cv2.resize(g,(32,32),interpolation=cv2.INTER_AREA).astype(np.float32)
    dct=cv2.dct(small)[:8,:8]
    med=np.median(dct[1:,:])
    bits=dct>med
    return np.packbits(bits.reshape(-1)).tobytes()

def hamming(a,b):
    if a is None or b is None: return 64
    x=np.frombuffer(a,dtype=np.uint8)^np.frombuffer(b,dtype=np.uint8)
    return int(np.unpackbits(x).sum())

def assess(img, prev_hash, th:QualityThresholds):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur=float(cv2.Laplacian(g,cv2.CV_64F).var())
    y=cv2.cvtColor(img,cv2.COLOR_BGR2YCrCb)[:,:,0]
    luma=float(y.mean())
    clipped=float(((y<=2)|(y>=253)).mean())
    reasons=[]
    if blur<th.blur_min: reasons.append('blur')
    if luma<th.luma_min or luma>th.luma_max or clipped>th.clip_max: reasons.append('exposure')
    h=phash(img); dist=hamming(prev_hash,h)
    if prev_hash is not None and dist<=th.phash_min_dist: reasons.append('stuck')
    return len(reasons)==0, reasons, h, {'blur':blur,'luma':luma,'clipped':clipped,'phash_dist':dist}
