# Stage 3 latency — 2026-08-06 / 09-12 / 09-29 / 09-30 / 10-01 side by side

All tests on `slug.home.lan`, same `short.wav` (2.5 s), same services. Drivers below.

## Driver stack

| Component | 2026-08-06 | 2026-09-12 | 2026-09-29 | 2026-09-30 | 2026-10-01 |
|---|---|---|---|---|---|
| Kernel | (unknown) | 7.2.4-1-cachyos | 7.2.8-1-cachyos | 7.2.8-1-cachyos | **7.3.0-rc4-1-cachyos-rc** |
| Mesa / RADV | (unknown) | 26.2.2-arch3.2 | 26.2.3-arch3.1 | 26.2.3-arch3.1 | **26.2.4-1** |
| ROCm | (unknown) | 7.2.4 (Runtime 1.18) | 7.8.0 | 7.2.4 | (unchanged, not queried) |
| FLM | v0.9.46 | v1.0.5 | v1.0.6 | v1.0.6 | **v1.0.7** |
| qwentts.cpp | (unknown) | same build | same build | master (6fae929) | **same build** |
| NPU device | /dev/accel/accel0 | /dev/accel/accel0 | /dev/accel/accel0 | /dev/accel/accel0 | /dev/accel/accel0 |
| GPU device | RADV KRACKAN1 | RADV KRACKAN1 | RADV KRACKAN1 | RADV KRACKAN1 | RADV KRACKAN1 |

> 2026-10-01 also carries a config change: `flm-asr.service` ExecStart dropped the
> `whisper-v3:turbo` model tag (standalone ASR mode, `flm serve --asr 1`), so no
> LLM is co-loaded on the NPU anymore. flm-asr RSS: 8.3 G → 935 M.

---

## Stage 3 — concurrency + liveness

### Idle baselines (sequential)

| Metric | 08-06 | 09-12 | 09-29 | 09-30 | **10-01** | Δ (8/6→10/01) |
|---|---:|---:|---:|---:|---:|---:|
| STT idle (2.5 s audio) | 2.395 | 2.344 | 2.326 | 2.296 | **2.139** | **−10.7 %** |
| TTS idle (WAV) | 1.234 | 1.693 | 1.399 | 1.389 | 1.556 | +26.1 % |
| TTS streaming TTFA | 0.237 | 0.203 | 0.202 | 0.201 | 0.214 | −9.7 % |
| TTS streaming total | 1.318 | 1.374 | 1.338 | 1.392 | 1.426 | +8.2 % |

### Test 1: simultaneous TTS + STT (cross-contention)

| Metric | 08-06 | 09-12 | 09-29 | 09-30 | **10-01** |
|---|---:|---:|---:|---:|---:|
| STT concurrent | 5.453 | 5.414 | 5.322 | 5.307 | 5.364 |
| STT delta vs idle | +127.6 % | +131.0 % | +128.8 % | +131.2 % | **+150.8 %** |
| TTS concurrent | 3.041 | 3.704 | 3.287 | 2.417 | 3.449 |
| TTS delta vs idle | +146.4 % | +118.8 % | +135.0 % | +74.0 % | **+121.7 %** |

### Test 2: TTS flood x5

| Metric | 08-06 | 09-12 | 09-29 | 09-30 | **10-01** |
|---|---:|---:|---:|---:|---:|
| TTS flood wall | 7.748 | 6.840 | 6.785 | 6.363 | 7.120 |
| STT during TTS flood | 2.417 | 2.287 | 2.332 | 2.314 | **2.164** |

### Test 3: STT flood x5

| Metric | 08-06 | 09-12 | 09-29 | 09-30 | **10-01** |
|---|---:|---:|---:|---:|---:|
| STT flood wall | 13.009 | 12.718 | 13.002 | 12.764 | **12.156** |
| TTS during STT flood | 1.305 | 1.349 | 1.355 | 1.703 | **1.511** |

---

## Stage 3b — strict 1:1 cross-contention + end-to-end loop

### Idle baselines

| Metric | 08-06 | 09-12 | 09-29 | 09-30 | **10-01** | Δ (8/6→10/01) |
|---|---:|---:|---:|---:|---:|---:|
| STT idle | 2.379 | 2.286 | 2.333 | 2.289 | **2.157** | −9.3 % |
| TTS idle total | 1.404 | 1.502 | 1.388 | 1.282 | 1.478 | +5.3 % |
| TTS idle TTFA | 0.202 | 0.203 | 0.203 | 0.202 | 0.215 | +6.4 % |

### 1 STT + 1 TTS strictly simultaneous

| Metric | 08-06 | 09-12 | 09-29 | 09-30 | **10-01** |
|---|---:|---:|---:|---:|---:|
| STT concurrent | 2.422 (+1.8 %) | 3.380 (+47.8 %) | 2.399 (+2.9 %) | 2.385 (+4.2 %) | 2.465 (**+14.3 %**) |
| TTS concurrent | 1.450 (+3.3 %) | 1.612 (+7.3 %) | 1.558 (+12.2 %) | 1.452 (+13.3 %) | 1.814 (**+22.7 %**) |
| TTS TTFA concur | 0.203 (+0.8 %) | 0.206 (+1.3 %) | 0.205 (+1.2 %) | 0.205 (+1.1 %) | 0.221 (+3.0 %) |

### End-to-end conversational loop

| Metric | 08-06 | 09-12 | 09-29 | 09-30 | **10-01** | Δ (8/6→10/01) |
|---|---:|---:|---:|---:|---:|---:|
| E2E mean | 3.729 | 4.117 | 3.599 | 3.623 | **3.585** | −3.9 % |
| E2E min | 3.647 | 3.437 | 3.516 | 3.595 | 3.349 | −8.2 % |
| E2E round 1 | 3.752 | 5.836 | 3.516 | 3.606 | 3.507 | — |

---

## Notes

- **STT idle is the best ever recorded** — 2.296 → 2.139 s (−6.8 % vs 09-30,
  −10.7 % vs the 08-06 baseline). Dropping the co-loaded `llama3.2:1b` from the NPU
  frees ~1.3 GB and removes a co-tenant from the NPU queue; this is the most
  plausible cause. Cumulative STT improvement across all runs is now ~11 %.
- **STT flood wall also improved** — 12.764 → 12.156 s (−4.8 %), consistent with
  the same cause.
- **flm v1.0.7 caused no STT regression.** Idle, flood, and STT-under-TTS-load are
  all at or better than 09-30. The "Unsupported model family" startup error was
  cosmetic, as suspected.
- **STT-under-TTS-flood is the best yet** — 2.314 → 2.164 s.
- **TTS regressed this run, and it is the open problem.** TTS idle WAV 1.389 →
  1.556 s (+12 %), concurrent TTS 2.417 → 3.449 s (+43 %), 1:1 concurrent
  +13.3 % → +22.7 %. qwentts.cpp build is unchanged, so this is not the TTS binary.
  Prime suspect is the newer Mesa (26.2.3 → 26.2.4) regressing Vulkan
  throughput on the Radeon 840M, possibly on the rc kernel. Worth a controlled
  test: pin mesa 26.2.3-arch3.1 and re-run.
- **STT concurrent delta (+150.8 %) looks worse but isn't.** Absolute STT
  concurrent time barely moved (5.307 → 5.364 s, +1.1 %); the percentage is
  inflated because the idle baseline got faster.
- **TTFA remains stable** — 0.201 → 0.214 s, still far below the 0.237 s of the
  original baseline. Conversational responsiveness is unaffected.
- **E2E loop is the best mean on record** (3.585 s) and no outlier round recurred.
- The 09-30 "TTS during STT flood" regression (1.703 s) partially recovers at
  1.511 s but is still above the 1.305 s baseline.
