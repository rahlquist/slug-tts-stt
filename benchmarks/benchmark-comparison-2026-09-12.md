# Stage 3 latency — 2026-08-06 vs 2026-09-12 side by side

All tests on `slug.home.lan`, same `short.wav` (2.5 s), same services. Drivers below.

## Driver stack

| Component | 2026-08-06 | 2026-09-12 |
|---|---|---|
| Kernel | (unknown) | Linux 7.2.4-1-cachyos |
| Mesa / RADV | (unknown) | 26.2.2-arch3.2 |
| ROCm | (unknown) | 7.2.4 (Runtime 1.18) |
| FLM | v0.9.46 | **v1.0.5** |
| qwentts.cpp | (unknown) | same build |
| NPU device | /dev/accel/accel0 | /dev/accel0 |
| GPU device | RADV KRACKAN1 | RADV KRACKAN1 |

> 2026-08-06 driver stack was not captured at the time — kernel/Mesa/ROCm
> versions for the original run are lost. New runs from here on log them.

---

## Stage 3 — concurrency + liveness

### Idle baselines (sequential)

| Metric | 2026-08-06 | 2026-09-12 | Δ |
|---|---:|---:|---:|
| STT idle (2.5 s audio) | 2.395 s | **2.344 s** | −2.1 % |
| TTS idle (WAV) | 1.234 s | 1.693 s | +37.2 % |
| TTS streaming TTFA | 0.237 s | **0.203 s** | −14.3 % |
| TTS streaming total | 1.318 s | 1.374 s | +4.2 % |

### Test 1: simultaneous TTS + STT (cross-contention)

| Metric | 2026-08-06 | 2026-09-12 | Δ |
|---|---:|---:|---:|
| STT concurrent | 5.453 s | **5.414 s** | −0.7 % |
| STT delta vs idle | +127.6 % | +131.0 % | — |
| TTS concurrent | 3.041 s | 3.704 s | +21.8 % |
| TTS delta vs idle | +146.4 % | +118.8 % | — |

### Test 2: TTS flood x5

| Metric | 2026-08-06 | 2026-09-12 | Δ |
|---|---:|---:|---:|
| TTS flood wall | 7.748 s | **6.840 s** | −11.7 % |
| STT during TTS flood | 2.417 s | **2.287 s** | −5.4 % |

### Test 3: STT flood x5

| Metric | 2026-08-06 | 2026-09-12 | Δ |
|---|---:|---:|---:|
| STT flood wall | 13.009 s | **12.718 s** | −2.2 % |
| TTS during STT flood | 1.305 s | 1.349 s | +3.4 % |

---

## Stage 3b — strict 1:1 cross-contention + end-to-end loop

### Idle baselines

| Metric | 2026-08-06 | 2026-09-12 | Δ |
|---|---:|---:|---:|
| STT idle | 2.379 s | **2.286 s** | −3.9 % |
| TTS idle total | 1.404 s | 1.502 s | +7.0 % |
| TTS idle TTFA | 0.202 s | 0.203 s | +0.5 % |

### 1 STT + 1 TTS strictly simultaneous

| Metric | 2026-08-06 | 2026-09-12 | Δ |
|---|---:|---:|---:|
| STT concurrent | 2.422 s (+1.8 %) | 3.380 s (+47.8 %) | **regression** |
| TTS concurrent | 1.450 s (+3.3 %) | 1.612 s (+7.3 %) | +11.2 % |
| TTS TTFA concur | 0.203 s (+0.8 %) | 0.206 s (+1.3 %) | +1.5 % |

### End-to-end conversational loop

| Metric | 2026-08-06 | 2026-09-12 | Δ |
|---|---:|---:|---:|
| E2E mean | 3.729 s | 4.117 s | +10.4 % |
| E2E min | 3.647 s | 3.437 s | −5.8 % |
| E2E round 1 | 3.752 s | 5.836 s | outlier (likely first-req JIT) |

---

## Notes

- **STT idle improved** from 2.395 → 2.344 s (−2.1 %) — FLM v1.0.5 on NPU is
  slightly faster for the single-request path.
- **TTS idle WAV regressed** from 1.234 → 1.693 s (+37 %) — non-streaming encode
  path is slower; unclear if driver or model-load interaction.
- **TTFA is rock-solid** — 0.203 s unchanged, the conversational stream path
  unaffected.
- **STT concurrent 1:1 regressed** — 2.422 → 3.380 s (+48 %) under simultaneous
  load. This is the headline change. NPU scheduling may have shifted between
  FLM versions when both devices are active.
- **E2E loop got worse on average** (3.729 → 4.117 s) but the round 1 outlier
  (5.836 s) likely dominates; rounds 2–5 are 3.4–3.8 s, overlapping the old
  range.
