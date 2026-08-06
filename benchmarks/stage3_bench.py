#!/usr/bin/env python3
"""Stage 3: concurrency + latency harness for the slug voice service.
STT = FLM ASR on NPU behind proxy :8081 ; TTS = qwentts.cpp on iGPU :8092
Logs every sample to ~/tts-test/stage3-latency.log
"""
import json, subprocess, statistics, time, sys, threading, urllib.request

STT_URL = "http://127.0.0.1:8081/v1/audio/transcriptions"
TTS_URL = "http://127.0.0.1:8092/v1/audio/speech"
AUDIO   = "/home/rahlquist/tts-test/short.wav"      # 2.5 s utterance
TEXT    = "The voice service is running on slug."
LOG     = "/home/rahlquist/tts-test/stage3-latency.log"

def log(msg):
    line = "%s  %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def stt_once():
    t0 = time.time()
    out = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
                          "-X","POST",STT_URL,"-F","file=@"+AUDIO,"-F","model=whisper-1"],
                         capture_output=True, text=True, timeout=120)
    return time.time()-t0, out.stdout.strip()

def tts_once(stream=False):
    body = {"model":"qwen3-tts-1.7b","input":TEXT}
    if not stream:
        body["response_format"] = "wav"
    data = json.dumps(body).encode()
    req = urllib.request.Request(TTS_URL, data=data,
                                 headers={"Content-Type":"application/json"}, method="POST")
    t0 = time.time(); ttfa = None; total = 0
    with urllib.request.urlopen(req, timeout=180) as r:
        while True:
            chunk = r.read(4096)
            if not chunk: break
            if ttfa is None: ttfa = time.time()-t0   # first audio byte
            total += len(chunk)
    return time.time()-t0, ttfa, total

def bench(fn, n, label):
    lat = []
    for _ in range(n):
        r = fn()
        lat.append(r[0] if isinstance(r, tuple) else r)
    log("%-34s n=%d  mean=%.3fs  min=%.3fs  max=%.3fs" %
        (label, n, statistics.mean(lat), min(lat), max(lat)))
    return statistics.mean(lat)

def parallel(fn, n, label, results):
    lat = []
    lock = threading.Lock()
    def worker():
        r = fn()
        v = r[0] if isinstance(r, tuple) else r
        with lock: lat.append(v)
    ts = [threading.Thread(target=worker) for _ in range(n)]
    t0 = time.time()
    for t in ts: t.start()
    for t in ts: t.join()
    wall = time.time()-t0
    log("%-34s n=%d  wall=%.3fs  mean=%.3fs  max=%.3fs" %
        (label, n, wall, statistics.mean(lat), max(lat)))
    results[label] = (statistics.mean(lat), wall)
    return statistics.mean(lat), wall

if __name__ == "__main__":
    log("="*72)
    log("STAGE 3 — concurrency + liveness measurement")
    log("="*72)

    log("--- IDLE BASELINES (sequential) ---")
    stt_base = bench(stt_once, 5, "STT idle (2.5s audio, NPU)")
    tts_base = bench(lambda: tts_once(False), 5, "TTS idle (wav, iGPU)")

    # TTFA / streaming
    ttfas, totals = [], []
    for _ in range(5):
        tot, ttfa, _ = tts_once(stream=True)
        ttfas.append(ttfa); totals.append(tot)
    log("%-34s n=5  TTFA_mean=%.3fs  TTFA_min=%.3fs  total_mean=%.3fs" %
        ("TTS streaming (pcm)", statistics.mean(ttfas), min(ttfas), statistics.mean(totals)))

    log("--- TEST 1: SIMULTANEOUS TTS + STT (cross-contention) ---")
    res = {}
    stt_lat, tts_lat = [], []
    def s_w():
        stt_lat.append(stt_once()[0])
    def t_w():
        tts_lat.append(tts_once(False)[0])
    ths = [threading.Thread(target=s_w) for _ in range(3)] + \
          [threading.Thread(target=t_w) for _ in range(3)]
    t0 = time.time()
    for t in ths: t.start()
    for t in ths: t.join()
    log("simultaneous wall=%.3fs" % (time.time()-t0))
    log("  STT concurrent mean=%.3fs (idle %.3fs, delta %+.1f%%)" %
        (statistics.mean(stt_lat), stt_base, 100*(statistics.mean(stt_lat)-stt_base)/stt_base))
    log("  TTS concurrent mean=%.3fs (idle %.3fs, delta %+.1f%%)" %
        (statistics.mean(tts_lat), tts_base, 100*(statistics.mean(tts_lat)-tts_base)/tts_base))

    log("--- TEST 2: TTS FLOOD x5 (max-batch=1 -> expect serialize) ---")
    parallel(lambda: tts_once(False), 5, "TTS flood x5", res)
    log("  STT during TTS flood:")
    bench(stt_once, 3, "  STT while TTS flooded")

    log("--- TEST 3: STT FLOOD x5 (NPU q-len 10) ---")
    parallel(stt_once, 5, "STT flood x5", res)
    log("  TTS during STT flood:")
    bench(lambda: tts_once(False), 3, "  TTS while STT flooded")

    log("STAGE 3 harness complete.")
