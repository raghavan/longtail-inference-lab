# Physical Jetson CUDA development check

**Date:** November 15, 2026

**Scope:** Same-device CPU/CUDA development timings and basic GPU integration. This is not a scored quality study, cross-platform comparison, or reliability qualification.

## Configuration

- Orin Nano Super 8 GB, Ubuntu 22.04.5 LTS, L4T R36.4.4, existing 25 W power mode. No power-mode or clock-frequency tuning.
- CUDA toolkit 12.6.68, cuBLAS 12.6 (package build 1.4), GCC 11.4.0, CMake 3.22.1. Native Release builds target CUDA architecture 87, with `GGML_NATIVE=OFF`, `GGML_METAL=OFF`, and `GGML_CUDA=ON`.
- llama.cpp `930e2fa5995789efbf249a8bf61325bb626e417b`; whisper.cpp `da54572229bcf64ba367d96c7ef15770376c4280`. Both source trees matched the lock and were clean. The server build disables unused UI downloads, CURL, and upstream tests.
- Qwen2.5 1.5B Instruct Q4_K_M and Whisper tiny.en F16, with exact revisions and verified SHA-256 values in the [runtime lock](../software/jetson/runtime-lock.json). eSpeak NG 1.50, `en-us`, 165 words/minute generates answers on CPU.
- Four CPU threads, 2,048-token context, 128-token output cap, temperature zero, seed 42. Fresh single-turn prompts, no retrieval or conversation history, prompt caching disabled. The application system-prompt hash is included in the timing artifact.
- The pre-existing CPU installation was retained. Both answer binaries report version 0.4.1-dev, build 1, commit 930e2fa, GNU 11.4.0/aarch64. The complete original CPU build provenance was not reconstructed; this comparison measures the installed working CPU profile against the newly built CUDA profile.

## GPU execution evidence

The answer runtime detected `CUDA0: Orin`, loaded all 29/29 model layers onto the GPU, and completed an authored text question. Final runtime allocation logs showed 934.70 MiB of CUDA model buffers, 56.00 MiB of CUDA KV cache, and 63.51 MiB of CUDA compute buffers. These buffer figures are not peak process or total system memory measurements.

Whisper detected the Orin at compute capability 8.7, reported `using CUDA0 backend`, loaded 77.11 MB of model data on CUDA, and correctly transcribed the authored synthetic question. Both builds exited successfully. CUDA asset/executable/audio readiness and both model hashes passed. All 38 application regression tests passed on the physical Jetson.

## Paired timings

All twelve turns completed with no failed, cancelled, timed-out, or excluded
comparison attempts. The full [authored trial artifact](2026-11-15-jetson-cuda-check.json)
records each answer and stage duration. Builds were finished before measurement;
the installed CPU button service remained idle throughout all four sessions.

| Case / stage | CPU seconds, two trials | CUDA seconds, two trials |
| --- | --- | --- |
| Cold text answer, includes server startup | 9.109, 8.767 | 3.493, 3.178 |
| Warm text answer | 7.860, 7.859 | 0.495, 0.479 |
| Warm synthetic voice: transcription | 1.640, 1.647 | 0.795, 0.795 |
| Warm synthetic voice: answer | 6.837, 6.816 | 0.365, 0.406 |
| Warm synthetic voice: synthesis | 0.032, 0.032 | 0.032, 0.032 |
| Warm synthetic voice: sum of processing stages | 8.509, 8.495 | 1.192, 1.233 |

For this voice fixture, the mean summed processing time was **8.502 seconds on CPU
versus 1.213 seconds on CUDA**, approximately **7.0 times faster**. This is not
recording-to-audible-answer latency or a general speedup claim. The warm text and
voice answers matched exactly across profiles. The cold text answer differed:
CPU returned “Water and sunscreen.”; CUDA returned “Water and sunscreen are two
essentials to pack for a short walk.” Cold timings therefore include different
output lengths as well as initialization.

During the complete comparison, 629 system telemetry samples at a requested
100 ms interval observed GPU activity up to 99%, total system RAM between 1,868
and 3,030 MB, zero swap use, and junction temperature between 46.5 and 49.937 °C.
These are sampled system-wide observations, including background services, not
per-process peaks, sustained thermal limits, or energy measurements. Kernel was
5.15.148-tegra and Python was 3.10.12.

## Deployment

The system service was switched to the CUDA backend and restarted. It is active,
enabled for boot, and reports ready with zero restart attempts. Its process
network namespace still contains only loopback. The switch changed only the
backend selection; button firmware, USB audio routing, and speaker volume were
retained. The owner confirmed two physical-button questions answered aloud and
a noticeably faster second response. After that check, the service-owned answer
process explicitly selected CUDA0, had the CUDA runtime library loaded, and still
had only loopback networking. The service returned to ready with zero restarts.
Boot enablement is verified, but the earlier observed reboot used the CPU profile;
no new CUDA reboot test is claimed. CPU binaries and a machine-local rollback
script remain available.

## Method

The [backend check](../software/jetson/scripts/backend_check.py) verifies model hashes and runs CPU-CUDA-CUDA-CPU sessions. Each session starts a new answer server and runs the same three authored inputs:

1. Cold text: “Name two things to pack for a short walk.”
2. Warm text: “In one short sentence, why do plants need sunlight?”
3. Warm synthetic audio: “What is the capital of France?”

The speech fixture is generated locally with eSpeak `en-us` at 145 words/minute and converted to mono 16 kHz signed 16-bit PCM. Its duration and SHA-256 are recorded. The check removes synthetic audio after use and never captures the microphone or plays speech. Only deliberately authored examples are published.

Cold means a new model-server process, not an empty OS file cache. Stage times exclude microphone capture and speaker playback. Two sessions per backend are too few for percentiles, general conversation latency, quality conclusions, or thermal/reliability claims. Report any output differences alongside timing because answer length can affect latency.

## Build failures and recovery

The initial source transfer carried AppleDouble metadata files that were mistakenly included by the CUDA source glob; removing those transfer artifacts resolved that configuration failure. The upstream server also attempted an unnecessary Web UI download; the setup script now explicitly disables it. Finally, the device's incorrect 2025 clock made already-built objects older than system headers, causing repeated recompilation after build restarts. Correcting system/hardware time and retimestamping generated build artifacts allowed valid objects to be reused. Source contents were unchanged.

The CUDA profiles occupy separate build/binary directories. The existing CPU binaries, models, service configuration, audio routing, and button firmware were preserved during compilation. A machine-local service switch and CPU rollback were prepared; no connection or device identifiers are published here.
