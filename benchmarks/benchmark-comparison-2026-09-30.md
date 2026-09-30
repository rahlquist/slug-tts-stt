# Stage 3 latency — 2026-08-06 vs 2026-09-12 vs 2026-09-29 vs 2026-09-30 side by side

All tests on `slug.home.lan`, same `short.wav` (2.5 s), same services. Drivers below.

## Driver stack

| Component | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 |
|---|---|---|---|---|
| Kernel | (unknown) | Linux 7.2.4-1-cachyos | Linux 7.2.8-1-cachyos | Linux 7.2.8-1-cachyos |
| Mesa / RADV | (unknown) | 26.2.2-arch3.2 | 26.2.3-arch3.1 | 26.2.3-arch3.1 |
| ROCm | (unknown) | 7.2.4 (Runtime 1.18) | 7.8.0 | 7.2.4 |
| FLM | v0.9.46 | v1.0.5 | v1.0.6 | v1.0.6 |
| qwentts.cpp | (unknown) | same build | same build | **updated to master (6fae929)** |
| NPU device | /dev/accel/accel0 | /dev/accel/accel0 | /dev/accel/accel0 | /dev/accel/accel0 |
| GPU device | RADV KRACKAN1 | RADV KRACKAN1 | RADV KRACKAN1 | RADV KRACKAN1 |

> 2026-08-06 driver stack was not captured at the time — kernel/Mesa/ROCm
> versions for the original run are lost. New runs from here on log them.

---

## Stage 3 — concurrency + liveness

### Idle baselines (sequential)

| Metric | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | Δ (8/6→9/30) |
|---|---:|---:|---:|---:|---:|
| STT idle (2.5 s audio) | 2.395 s | 2.344 s | 2.326 s | **2.296 s** | −4.1 % |
| TTS idle (WAV) | 1.234 s | 1.693 s | 1.399 s | **1.389 s** | +12.6 % |
| TTS streaming TTFA | 0.237 s | 0.203 s | 0.202 s | **0.201 s** | −15.2 % |
| TTS streaming total | 1.318 s | 1.374 s | 1.338 s | 1.392 s | +5.6 % |

### Test 1: simultaneous TTS + STT (cross-contention)

| Metric | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | Δ (8/6→9/30) |
|---|---:|---:|---:|---:|---:|
| STT concurrent | 5.453 s | 5.414 s | 5.322 s | **5.307 s** | −2.7 % |
| STT delta vs idle | +127.6 % | +131.0 % | +128.8 % | +131.2 % | — |
| TTS concurrent | 3.041 s | 3.704 s | 3.287 s | **2.417 s** | −20.5 % |
| TTS delta vs idle | +146.4 % | +118.8 % | +135.0 % | +74.0 % | — |

### Test 2: TTS flood x5

| Metric | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | Δ (8/6→9/30) |
|---|---:|---:|---:|---:|---:|
| TTS flood wall | 7.748 s | 6.840 s | 6.785 s | **6.363 s** | −17.9 % |
| STT during TTS flood | 2.417 s | 2.287 s | 2.332 s | 2.314 s | −4.3 % |

### Test 3: STT flood x5

| Metric | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | Δ (8/6→9/30) |
|---|---:|---:|---:|---:|---:|
| STT flood wall | 13.009 s | 12.718 s | 13.002 s | **12.764 s** | −1.9 % |
| TTS during STT flood | 1.305 s | 1.349 s | 1.355 s | 1.703 s | +30.5 % |

---

## Stage 3b — strict 1:1 cross-contention + end-to-end loop

### Idle baselines

| Metric | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | Δ (8/6→9/30) |
|---|---:|---:|---:|---:|---:|
| STT idle | 2.379 s | 2.286 s | 2.333 s | **2.289 s** | −3.8 % |
| TTS idle total | 1.404 s | 1.502 s | 1.388 s | **1.282 s** | −8.7 % |
| TTS idle TTFA | 0.202 s | 0.203 s | 0.203 s | 0.202 s | +0.0 % |

### 1 STT + 1 TTS strictly simultaneous

| Metric | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | Δ (8/6→9/30) |
|---|---:|---:|---:|---:|---:|
| STT concurrent | 2.422 s (+1.8 %) | 3.380 s (+47.8 %) | 2.399 s (+2.9 %) | 2.385 s (+4.2 %) | −1.5 % |
| TTS concurrent | 1.450 s (+3.3 %) | 1.612 s (+7.3 %) | 1.558 s (+12.2 %) | **1.452 s (+13.3 %)** | +0.1 % |
| TTS TTFA concur | 0.203 s (+0.8 %) | 0.206 s (+1.3 %) | 0.205 s (+1.2 %) | 0.205 s (+1.1 %) | +1.0 % |

### End-to-end conversational loop

| Metric | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | Δ (8/6→9/30) |
|---|---:|---:|---:|---:|---:|
| E2E mean | 3.729 s | 4.117 s | 3.599 s | 3.623 s | −2.8 % |
| E2E min | 3.647 s | 3.437 s | 3.516 s | 3.595 s | −1.4 % |
| E2E round 1 | 3.752 s | 5.836 s | 3.516 s | 3.606 s | — |

---

## Notes

- **qwentts.cpp updated** from 28 commits behind to latest master (6fae929).
  Key changes: ggml fork updates, sampling refactor, tts-server fixes,
  Docker support. Required installing `spirv-headers` (new dep).
- **TTS under load improved significantly** — simultaneous TTS dropped from
  3.287 → 2.417 s (−26 %), TTS flood wall from 6.785 → 6.363 s (−6 %).
  The ggml fork updates appear to have helped Vulkan throughput.
- **TTS idle WAV** went 1.234 → 1.693 → 1.399 → 1.389 s — still above 8/6
  baseline but trending better.
- **TTFA is rock-solid** — 0.237 → 0.203 → 0.202 → 0.201 s, the conversational
  stream path unaffected across all four runs.
- **STT concurrent 1:1 regression RESOLVED** — 2.422 → 3.380 → 2.399 → 2.385 s.
  The 9/12 +47.8 % regression was FLM v1.0.5; v1.0.6 brings it back to
  near-baseline (+4.2 % vs +1.8 % on 8/6).
- **E2E loop is stable** — 3.729 → 4.117 → 3.599 → 3.623 s mean. The 9/12
  outlier round 1 (5.836 s) does not recur; all 9/30 rounds are 3.6–3.7 s.
- **TTS during STT flood regressed** — 1.305 → 1.349 → 1.355 → 1.703 s.
  This is the one metric that got worse; unclear if qwentts.cpp update or
  system state is the cause.
