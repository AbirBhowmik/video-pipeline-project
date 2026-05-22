from dataclasses import dataclass
import cv2, numpy as np

@dataclass(frozen=True)
class LetterboxMeta:
    src_w:int; src_h:int; dst:int; scale:float; pad_x:float; pad_y:float

def letterbox_image(img, dst=640, color=(114,114,114)):
    h,w=img.shape[:2]; s=min(dst/w,dst/h)
    nw,nh=int(round(w*s)),int(round(h*s))
    resized=cv2.resize(img,(nw,nh),interpolation=cv2.INTER_LINEAR)
    out=np.full((dst,dst,3),color,dtype=img.dtype)
    px=(dst-nw)//2; py=(dst-nh)//2
    out[py:py+nh,px:px+nw]=resized
    return out, LetterboxMeta(w,h,dst,s,px,py)

def blob_cv2(img, dst=640):
    lb,meta=letterbox_image(img,dst)
    blob=cv2.dnn.blobFromImage(lb, scalefactor=1/255.0, size=(dst,dst), swapRB=True, crop=False)
    return blob.astype(np.float32, copy=False), meta

def blob_numpy(img, dst=640):
    lb,meta=letterbox_image(img,dst)
    arr=lb[:,:,::-1].astype(np.float32)/255.0
    return arr.transpose(2,0,1)[None], meta

def bbox_src_to_letterbox(box, meta):
    b=np.asarray(box,dtype=np.float32).copy()
    b[[0,2]]=b[[0,2]]*meta.scale+meta.pad_x
    b[[1,3]]=b[[1,3]]*meta.scale+meta.pad_y
    return b

def bbox_letterbox_to_src(box, meta):
    b=np.asarray(box,dtype=np.float32).copy()
    b[[0,2]]=(b[[0,2]]-meta.pad_x)/meta.scale
    b[[1,3]]=(b[[1,3]]-meta.pad_y)/meta.scale
    b[[0,2]]=np.clip(b[[0,2]],0,meta.src_w)
    b[[1,3]]=np.clip(b[[1,3]],0,meta.src_h)
    return b
