#!/usr/bin/env python3
"""Clean cross-contention test: exactly ONE STT and ONE TTS in flight together,
so any slowdown is cross-device, not self-queuing. Also measures the real
end-to-end conversational loop (STT -> TTS first audio)."""
import json, subprocess, statistics, time, threading, urllib.request

STT_URL="http://127.0.0.1:8081/v1/audio/transcriptions"
TTS_URL="http://127.0.0.1:8092/v1/audio/speech"
AUDIO="/home/rahlquist/tts-test/short.wav"
TEXT="The voice service is running on slug."
LOG="/home/rahlquist/tts-test/stage3-latency.log"

def log(m):
    line="%s  %s"%(time.strftime("%Y-%m-%d %H:%M:%S"),m)
    print(line,flush=True)
    open(LOG,"a").write(line+"\n")

def stt():
    t0=time.time()
    subprocess.run(["curl","-s","-o","/dev/null","-X","POST",STT_URL,
                    "-F","file=@"+AUDIO,"-F","model=whisper-1"],
                   capture_output=True,timeout=120)
    return time.time()-t0

def tts(stream=True):
    b={"model":"qwen3-tts-1.7b","input":TEXT}
    if not stream: b["response_format"]="wav"
    req=urllib.request.Request(TTS_URL,data=json.dumps(b).encode(),
        headers={"Content-Type":"application/json"},method="POST")
    t0=time.time(); ttfa=None
    with urllib.request.urlopen(req,timeout=180) as r:
        while True:
            c=r.read(4096)
            if not c: break
            if ttfa is None: ttfa=time.time()-t0
    return time.time()-t0, ttfa

log("="*72)
log("STAGE 3b — STRICT 1:1 cross-contention + end-to-end loop")
log("="*72)

s_idle=[stt() for _ in range(5)]
t_idle=[tts(True) for _ in range(5)]
log("STT idle          mean=%.3fs"%statistics.mean(s_idle))
log("TTS idle  total   mean=%.3fs   TTFA mean=%.3fs"%(
    statistics.mean([x[0] for x in t_idle]),
    statistics.mean([x[1] for x in t_idle])))

log("--- 1 STT + 1 TTS strictly simultaneous, 5 rounds ---")
sc,tc,tf=[],[],[]
for i in range(5):
    barrier=threading.Barrier(2)
    out={}
    def sw():
        barrier.wait(); out['s']=stt()
    def tw():
        barrier.wait(); out['t']=tts(True)
    a=threading.Thread(target=sw); b=threading.Thread(target=tw)
    a.start(); b.start(); a.join(); b.join()
    sc.append(out['s']); tc.append(out['t'][0]); tf.append(out['t'][1])
    time.sleep(0.5)

si=statistics.mean(s_idle); ti=statistics.mean([x[0] for x in t_idle])
fi=statistics.mean([x[1] for x in t_idle])
log("STT concurrent    mean=%.3fs  (idle %.3fs) delta %+.1f%%"%(
    statistics.mean(sc),si,100*(statistics.mean(sc)-si)/si))
log("TTS concurrent    mean=%.3fs  (idle %.3fs) delta %+.1f%%"%(
    statistics.mean(tc),ti,100*(statistics.mean(tc)-ti)/ti))
log("TTS TTFA concur   mean=%.3fs  (idle %.3fs) delta %+.1f%%"%(
    statistics.mean(tf),fi,100*(statistics.mean(tf)-fi)/fi))

log("--- END-TO-END conversational loop (slug audio portion) ---")
e2e=[]
for i in range(5):
    t0=time.time()
    stt()                      # user speaks -> text
    _,ttfa=tts(True)           # Hermes replies -> first audio out
    e2e.append(time.time()-t0)
    log("  round %d: %.3fs (STT complete -> TTS first audio)"%(i+1,e2e[-1]))
log("E2E slug audio    mean=%.3fs  min=%.3fs   [target <1.000s]"%(
    statistics.mean(e2e),min(e2e)))
log("STAGE 3b complete.")
