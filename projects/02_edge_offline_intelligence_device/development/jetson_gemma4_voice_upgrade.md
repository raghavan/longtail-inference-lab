# Gemma 4 E2B and neural speech upgrade

**Authorized:** November 15, 2026. Upgrade the existing physical Jetson prototype to Gemma 4 E2B and a more natural local voice; keep inference offline and deploy it on the board.

This continues the [Linux intake](jetson_linux_intake.md) and existing single-turn button/audio/service contract. It is an implementation upgrade, not a new comparative quality experiment. EGM artifact directory: this development directory; scoped consistency findings belong in the dated drift report.

## Selected implementation

- Retain the validated CUDA llama.cpp/whisper.cpp commits and Whisper tiny.en recognition. Use Unsloth's GGUF conversion of Google's instruction-tuned Gemma 4 E2B, Q4_K_M. Pin revision, byte count, and SHA-256 in the runtime lock.
- Keep the existing 2,048-token context, 128-token answer limit, timeout/cancellation behavior, and brief English answers. Refine the prompt to one sentence for simple facts, at most two otherwise, and the requested item count. Explicitly disable thinking in chat-template parameters so speech receives the final answer within the existing output budget. No retrieval, tools, multimodal input, or conversation history is introduced.
- Replace eSpeak answer synthesis with Piper 1.8.0 and its `en_US-ljspeech-medium` single-speaker English voice. The voice card identifies a public-domain LJ Speech dataset. Pin the ONNX voice/config and target Python wheels with hashes; run synthesis on CPU in a bounded subprocess, passing text through stdin. eSpeak remains only a synthetic test-fixture generator.
- Keep one model-server process between turns. Piper loads per synthesis call initially; measure its startup/synthesis cost before considering a persistent worker. Keep the existing 120-second speech-duration bound and temporary audio cleanup.
- Stage a separate application/runtime installation beside the working Qwen/eSpeak deployment. Reuse immutable CUDA binaries and the existing transcription model; retain the old application, weights, and system unit as rollback. Download on the development host, transfer artifacts, and install packages without a package index on the Jetson.

## Acceptance and stop boundary

Before service activation: verify artifact hashes, real Gemma CUDA offload, neural WAV generation, all controller regressions plus missing-voice and synthesis-failure/cancellation coverage. Exercise three fixed authored inputs (short-walk packing, plant sunlight, capital of France), including synthetic audio. Record stage times and sampled total-system memory without quality/percentile claims. Exercise cancellation and output limits against the actual installed pipeline. Stop on memory exhaustion, silent fallback, external inference dependency, leaked reasoning, incomplete spoken output, or failed cleanup.

Activate only after these checks. Keep the service's non-root identity, private network, read-only mounts, transient audio, ALSA device selection, and button protocol. Verify the running service's actual model/runtime and loopback-only namespace, then obtain a physical listening check. A preferred-sounding voice is an owner report, not a scored naturalness result. Boot enablement and an observed reboot remain separate claims.

## Source references

- [Google Gemma 4 E2B instruction model](https://huggingface.co/google/gemma-4-E2B-it)
- [Unsloth GGUF conversion](https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF)
- [Google prompt/thinking format](https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4)
- [Piper local neural speech engine](https://github.com/OHF-Voice/piper1-gpl)
- [Voice model card](https://huggingface.co/rhasspy/piper-voices/blob/e9ab671f2a0e50a701b34361136ba3e6a3a9eb0c/en/en_US/ljspeech/medium/MODEL_CARD)

## Voice selection check

The high variant generated valid audio but took 6.351–11.532 seconds for the three initial authored responses. The medium variant synthesized the same authored France answer in 3.846 seconds in a separate isolated check (different system/cache conditions; no general speedup claim). Select medium for the first deployment and retain listening acceptance as a separate gate. The two-thread high-voice experiment was slower and is not deployed.
