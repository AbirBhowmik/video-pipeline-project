import json, os, psutil, statistics, time

def new_metrics():
    return {'capture_count':0,'preprocess_count':0,'recovery_count':0,'quality_counters':{'blur':0,'exposure':0,'stuck':0},'ages':[]}

def pctl(vals,p):
    if not vals: return 0.0
    s=sorted(vals); i=min(len(s)-1, int(round((p/100)*(len(s)-1))))
    return float(s[i])

def emit(streams, slots, interval, prev):
    now=time.monotonic(); proc=psutil.Process(os.getpid()); out=[]
    for name,m in streams.items():
        dt=max(now-prev[name]['t'],1e-6)
        c=m['capture_count']-prev[name]['cap']; pr=m['preprocess_count']-prev[name]['prep']
        ages=m['ages']; m['ages']=[]
        rec={'stream':name,'fps_capture':round(c/dt,2),'fps_preprocess':round(pr/dt,2),
             'frame_age_ms_p50':round(pctl(ages,50),2),'frame_age_ms_p99':round(pctl(ages,99),2),
             'frames_dropped':slots[name].dropped,'recovery_count':m['recovery_count'],
             'quality_counters':dict(m['quality_counters']),'rss_mb':round(proc.memory_info().rss/1024/1024,2)}
        print(json.dumps(rec), flush=True); out.append(rec)
        prev[name]={'t':now,'cap':m['capture_count'],'prep':m['preprocess_count']}
    return out, prev
