# Gemma 4 E2B and local neural voice on Jetson

**Date:** November 15, 2026 (trial timestamps use UTC)

**Scope:** Requested model/voice upgrade and basic deployment checks on one Orin Nano Super 8 GB. This is not a quality benchmark or a cross-platform comparison.

## Installed configuration

- Answer model: Google's instruction-tuned Gemma 4 E2B, Unsloth GGUF Q4_K_M, repository revision `0314792d7f1f7e229411f620751375812bb9faf2`, 3,106,738,272 bytes, SHA-256 `740185b21d22ceb83a11c3aa62ad5842ef32c70f6096d756bbee85a1e4ec34b8`.
- Recognition: the existing Whisper tiny.en F16 CUDA profile.
- Speech: Piper 1.8.0, ONNX Runtime 1.23.2 CPU provider, `en_US-ljspeech-medium`, mono 22,050 Hz. The voice card identifies a public-domain LJ Speech dataset. Voice weights/config and all twelve target Python wheels are hash-locked; no weights or wheels are committed here.
- Existing CUDA runtime commits, Ubuntu 22.04.5 / L4T R36.4.4, CUDA 12.6, and 25 W mode retained. Full artifact provenance is in the [runtime lock](../software/jetson/runtime-lock.json) and [ARM64 wheel requirements](../software/jetson/piper-requirements.txt).
- Context 2,048 tokens, answer cap 128 tokens, four answer/recognition CPU threads, temperature zero, seed 42, no history/retrieval/tools. Thinking explicitly disabled in chat-template parameters. The brief English prompt now requests one sentence for simple facts, at most two otherwise, and the requested item count. Its hash is in the trial artifact.

## Observed checks

Both model hashes and both voice/config hashes passed. Gemma returned an authored answer with all 36/36 transformer layers assigned to CUDA. Final allocation diagnostics reported 1,407.73 MiB CUDA model buffers, 1,756.00 MiB host model buffers, 24.00 MiB CUDA KV cache, and 116.52 MiB CUDA compute buffers. Layer offload does not mean every model buffer resides on the GPU; these are allocation figures, not peak system memory.

All **42 application regressions passed**, including neural WAV output, stdin delivery, missing voice configuration, synthesis failure/cancellation, thinking disabled, and rejection of leaked model control tokens. Real CLI checks passed missing assets, oversized input, output-limit rejection, silence rejection, stdin cancellation, and model-server cancellation. The observed server cancellation took 0.042 seconds. Separately, cancelling the actual Piper subprocess passed in 0.312 seconds, reaped the owned process, and removed transient audio.

Three final authored pipeline turns completed without a failure, cancellation, timeout, or exclusion in that final check. The [complete authored artifact](2026-11-15-jetson-gemma4-piper.json) records outputs and exact stage times. It ran outside the service network namespace; the service isolation check below is separate.

| Final configuration case | Answer seconds | Transcription seconds | Synthesis seconds |
| --- | --- | --- | --- |
| First text turn, including new server load | 21.394 | — | 4.224 |
| Warm plant/sunlight question | 0.744 | — | 3.559 |
| Warm synthetic France question | 0.687 | 3.346 | 3.379 |

The last case summed to **7.412 seconds of processing**, excluding microphone capture and speaker playback. This new model/voice/prompt combination is slower than the earlier small-model/formant-voice configuration; its earlier 1.21-second figure does not describe this deployment. Cold loading is substantially slower than warm answering. There is one final sample per case, no percentile claim, and no scored proof of better answer quality. One packing answer still named three items when two were requested; instruction following remains imperfect.

During this final check, 303 telemetry samples at a requested 200 ms interval observed total-system RAM between 1,293 and 4,960 MB of 7,620 MB, GPU activity up to 99%, junction temperature between 45.562 and 47.781 °C, and swap use between 163 and 234 MB. These include background processes and are not a sustained operating envelope or per-process peak. The prior answer model was unloaded before final checks to avoid keeping two deployments resident.

## Failures and voice selection

- An early voice probe was attempted before package installation finished and failed because the executable was absent. Installation subsequently completed from local hash-verified wheels; dependency checks passed.
- Another voice probe timed out during concurrent model loading and setup/readiness work. An isolated high-voice retry passed in 6.552 seconds. The initial Gemma offload probe completed but took roughly 78 seconds with that contention. These preliminary attempts are not omitted from the record or included as successful final timing samples.
- The high neural voice generated valid audio but synthesis took 6.351–11.532 seconds across three initial pipeline turns. A two-thread high-voice experiment was slower and was not adopted.
- The medium voice synthesized the same authored France response in 3.846 seconds in an isolated selection check. The final deployment uses medium, default CPU runtime threading, and the more concise prompt. Different output lengths and cache/system conditions prevent a general voice speedup claim.

## Deployment and offline boundary

Downloads occurred on the development host, then transferred to the Jetson. The voice Python environment was installed with `--no-index` and required hashes. Application inference never invokes setup or model download tools. Speech text is passed through stdin; generated audio stays transient unless explicitly exported.

A separate application/runtime directory was staged alongside the prior working installation. The system service now points at that directory, is active/enabled/ready with zero restarts, and has only loopback in its actual process network namespace. The non-root identity, private network, read-only home/system mounts, ALSA selections, button firmware, and boot enablement were preserved. The old application, models, CUDA binaries, and a machine-local service rollback remain available.

The owner confirmed that the new service answers aloud. Two complete physical button turns reached speaking and returned to ready. The service-owned answer process was verified to select the Gemma GGUF and CUDA and to retain only loopback networking. The owner did not separately rate voice naturalness; preference remains open. A new reboot or laptop-disconnected test of this profile has not been performed. Earlier hardware tests do not substitute for that profile-specific evidence.

See the [upgrade contract](../development/jetson_gemma4_voice_upgrade.md) and [deployment guide](../software/jetson/README.md). Extended voice preference, transcription accuracy, quality, repeated boot/reconnect behavior, and long-session resource limits remain open.

## Follow-up latency profile

The owner requested end-to-end profiling after the listening check. The [separate live-stage/component profile](2026-11-15-jetson-latency-profile.md) records timestamps without retaining utterances or audio and identifies repeated voice initialization as the clearest next optimization. No persistent speech/recognition workers or startup preloading have been deployed in this change.
