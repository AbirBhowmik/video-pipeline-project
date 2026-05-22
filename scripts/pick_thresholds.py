import argparse, os, cv2, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
from src.quality import phash, hamming

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--out',default='threshold_plots')
    args=ap.parse_args(); Path(args.out).mkdir(exist_ok=True)
    cap=cv2.VideoCapture(args.input, cv2.CAP_FFMPEG)
    if not cap.isOpened(): raise SystemExit('cannot open input')
    blur=[]; luma=[]; clipped=[]; hd=[]; prev=None
    while True:
        ok,frame=cap.read()
        if not ok or frame is None: break
        g=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        blur.append(cv2.Laplacian(g,cv2.CV_64F).var())
        y=cv2.cvtColor(frame,cv2.COLOR_BGR2YCrCb)[:,:,0]
        luma.append(y.mean()); clipped.append(((y<=2)|(y>=253)).mean())
        h=phash(frame); hd.append(hamming(prev,h) if prev else 64); prev=h
    cap.release()
    if not blur: raise SystemExit('no frames decoded')
    vals={'blur_laplacian_var':blur,'mean_luma':luma,'clipped_ratio':clipped,'phash_distance':hd[1:]}
    for name,v in vals.items():
        plt.figure(); plt.hist(v,bins=50); plt.title(name); plt.xlabel(name); plt.ylabel('frames')
        plt.savefig(os.path.join(args.out,f'{name}.png'),bbox_inches='tight'); plt.close()
    blur_min=max(50.0,float(np.percentile(blur,1))*0.7)
    luma_min=max(15.0,float(np.percentile(luma,1))-10); luma_max=min(245.0,float(np.percentile(luma,99))+10)
    clip_max=max(0.02,float(np.percentile(clipped,99))*1.5)
    phash_min=3
    print('recommended thresholds:')
    print(f'blur_min={blur_min:.2f}')
    print(f'luma_min={luma_min:.2f}, luma_max={luma_max:.2f}, clip_max={clip_max:.4f}')
    print(f'phash_min_dist={phash_min}')
    print(f'plots saved in {args.out}/')
if __name__=='__main__': main()
