# GPT-OSS 20B heterogeneous benchmark

**Host:** `slug.home.lan`  
**Date:** 2026-08-07  
**Purpose:** Measure the same GPT-OSS 20B workload on the host CPU, Radeon 840M iGPU, and XDNA2 NPU.

This is a measured reproduction on this host and runtime stack. It is not a universal performance claim.

## Host and runtime

- Hardware: AMD Krackan system
- CPU: host CPU, 12 llama.cpp threads
- GPU: AMD Radeon 840M integrated GPU, RADV KRACKAN1, Vulkan
- NPU: AMD XDNA2, `/dev/accel/accel0`, 8 columns
- FastFlowLM: `v0.9.46`
- llama.cpp: `10221` (`815a2a5915`)
- System memory: 30 GiB
- Test context: 4096 tokens
- Server slots: 1

## Model cells

The CPU and GPU cells used the same llama.cpp GGUF:

```text
/home/rahlquist/.cache/huggingface/hub/models--ggml-org--gpt-oss-20b-GGUF/snapshots/ef9b12f2ff56c69cf32153a02784e7a3c88bf524/gpt-oss-20b-MXFP4.gguf
```

The GGUF resolved to a 12,109,566,624-byte blob.

The NPU cell used the FLM-native `gpt-oss:20b` `model.q4nx` artifact. That is a different runtime format, so the NPU result is labelled separately rather than treated as a byte-identical model file comparison.

## Fixed workload

Prompt used for every cell:

> Explain in exactly three short sentences why measuring CPU, GPU, and NPU inference separately matters.

Parameters:

- Prompt: 86 tokens
- Maximum completion: 96 tokens
- Temperature: 0
- Streaming: disabled
- One request per cell

The model's reasoning output consumed the full 96-token completion cap. The response therefore measures loading, prompt processing, and decoding throughput; it is not a semantic-quality comparison.

## Results

| Backend | Runtime / configuration | Prompt processing | Generation | Wall time |
|---|---|---:|---:|---:|
| CPU | llama.cpp, `--n-gpu-layers 0`, 12 threads | 40.30 tok/s | 15.71 tok/s | 8.26 s |
| GPU | llama.cpp Vulkan, `--n-gpu-layers 99`, Radeon 840M | 38.26 tok/s | **22.97 tok/s** | **6.44 s** |
| NPU | FastFlowLM, performance mode | 23.43 tok/s | 19.50 tok/s | 8.66 s |

### Raw timing evidence

CPU llama.cpp reported:

```text
prompt_n: 86
prompt_per_second: 40.2961
predicted_n: 96
predicted_per_second: 15.7148
```

Clean GPU llama.cpp reported:

```text
prompt_n: 86
prompt_per_second: 38.2554
predicted_n: 96
predicted_per_second: 22.9724
```

NPU FastFlowLM reported:

```text
prompt_tokens: 86
prefill_speed_tps: 23.4255
completion_tokens: 96
decoding_speed_tps: 19.4984
```

## GPU test validity

The first GPU attempt was invalid: the NPU GPT-OSS server was still resident while the GPU server attempted to load. Host memory reached approximately 28 GiB of 30 GiB and swap reached approximately 2.1 GiB. That attempt is excluded from the table.

The GPU test reported here was rerun cleanly:

1. No GPT-OSS, llama.cpp, or test server processes were running.
2. The NPU model was not loaded.
3. Baseline memory was approximately 1.5 GiB used and 28 GiB available.
4. Normal Whisper/TTS services were stopped temporarily to isolate the cell.
5. The GPU-only llama.cpp server became healthy on port `18091`.
6. The request completed successfully.
7. The GPU server was stopped before restoration.

During the clean GPU run, the llama-server process settled at approximately 1.0 GiB RSS after loading, and total system memory was approximately 12 GiB used. These values are host-process observations, not a complete accounting of Vulkan device memory or all mapped allocations.

## Interpretation

For this workload:

- GPU generation was fastest at 22.97 tok/s.
- NPU generation reached 19.50 tok/s.
- CPU generation reached 15.71 tok/s.
- CPU prompt processing was fastest at 40.30 tok/s, narrowly ahead of GPU at 38.26 tok/s.

The GPU was approximately 46% faster than the CPU for generation in this single measured cell. The NPU was approximately 24% faster than the CPU for generation. These percentages should not be generalized beyond this prompt, context size, quantization, runtime version, and power state.

## Restoration verification

The normal services were restored after the benchmark and verified by process and listening-port inspection:

- FLM Whisper ASR: `127.0.0.1:8090`
- Qwen TTS: `0.0.0.0:8092`
- Whisper proxy: `0.0.0.0:8081`
- No benchmark `llama-server` remained running

No kernel, driver, fan-control, or persistent service configuration changes were made.

## Limitations

- Only one request was measured per backend.
- The NPU used FLM's native `q4nx` artifact, while CPU/GPU used the llama.cpp GGUF.
- No stable NPU utilization percentage was available from the tested sysfs interfaces.
- No GPU utilization percentage was recorded; GPU attribution is established by the llama.cpp Vulkan backend and device identification.
- The completion cap was reached because GPT-OSS reasoning tokens consumed the budget.
- Results are throughput measurements, not a full latency distribution or sustained-load benchmark.

**Evidence class:** measured on-host runtime results. The excluded first GPU attempt is retained here only as a validity note and is not reported as a performance result.
