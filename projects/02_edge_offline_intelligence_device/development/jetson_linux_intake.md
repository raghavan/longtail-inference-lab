# Jetson voice application: Linux ARM64 development intake

**Status:** Linux ARM64 development validation passed; physical Jetson validation remains open.
**Track:** Offline edge application engineering
**Difficulty:** Intermediate
**Owner:** Laboratory maintainer
**Date:** September 15, 2026

This bounded development slice uses the [experiment template](../../../resources/experiment_template/README.md) and the existing [device architecture](../design_direction.md). It does not start a comparative quality experiment. It covers portable Linux application development, reproducible VM validation, and the subsequent on-board acceptance gates.

## One minute summary

**Question:** Can a portable Linux ARM64 application execute a bounded English audio-to-transcript-to-answer-to-speech pipeline entirely locally and recover from cancellation and unavailable assets?

**Decision:** Use the Linux application as the starting point for physical Jetson integration if its development checks pass. If native dependencies or resource use prevent a working pipeline, simplify before adding hardware features.

**Workload:** One English question at a time, no history, retrieval, external actions, or cloud inference. Deliberately authored synthetic audio is the VM integration input. A terminal control substitutes for the physical button; a serial event adapter provides the hardware integration boundary.

**Success boundary:** A real ARM64 Linux VM builds pinned runtimes, passes meaningful controller/failure tests, and produces a transcript, real model answer, and valid speech WAV with external networking unavailable. Reproduction and target deployment instructions accompany the result.

**Stop boundary:** Silent remote inference, uncontrolled generation, persistent recording after cancellation, private audio retained by default, or inability to recover cleanly from failed processing. Do not claim hardware readiness from VM tests.

## Practical context and scope

The target is Orin Nano Super 8 GB, mains powered, with USB microphone, speaker, and a programmed USB button. The existing Apple-only backends cannot be reused. Hardware acceptance, CUDA, real USB devices, thermal behavior, natural voice quality, and usefulness scoring remain separate gates. No additional hardware or paid service is required for this slice.

## Hypothesis and decision boundary

A Python standard-library controller around pinned native inference runtimes can provide a portable, inspectable implementation. CPU inference in an Ubuntu ARM64 VM establishes integration only. A positive result justifies testing the same application on Jetson; it cannot select a final answer model, establish acceptable device latency, or validate CUDA.

## Variables and controls

Use Ubuntu 22.04 ARM64 as the development baseline corresponding to the JetPack 6 family. Pin exact source commits, model revisions and SHA-256 hashes. Start with Qwen2.5 1.5B Instruct Q4_K_M through llama.cpp, Whisper tiny.en through whisper.cpp, and eSpeak NG as a functional speech baseline. The small established model and simple synthesizer reduce installation and debugging variables; neither is a final quality selection. Capture the actual versions and VM resource allocation with results.

Each answer receives a fresh single-turn prompt, capped input, fixed context/output limits, deterministic sampling where supported, and a deadline. Audio is mono 16 kHz signed 16-bit PCM, at most 30 seconds. Keep inference CPU-only in the VM; offer an explicit CUDA build profile for subsequent Jetson testing.

## Workload and evidence

Use authored questions about ordinary low-stakes topics and synthesize their audio locally. Such recordings are a development control, not representative human speech. Do not record the owner's microphone or ingest private prompts. Mock backends test failures; only actual model inference counts as an integration result. Test assertions and expected outputs remain outside model prompts.

## Failure tails, privacy, and path dependence

Exercise empty and oversized inputs, malformed WAVs, missing assets, runtime failure, timeouts, repeated turns, and cancellation. Only one operation may be active. New recording stops playback. Cancellation terminates subprocess groups and discards incomplete output. Do not persist audio, prompts, transcripts, or answers by default; explicit WAV export is opt-in. Runtime logs must not leak utterances into service logs. Temporary audio belongs in a private runtime directory and is removed when the operation ends.

Setup downloads are separate from inference. The inference client may talk only to its own loopback model server, with proxy environment variables bypassed. Missing models fail closed. Run the complete smoke check inside a Linux network namespace without external interfaces; record this exact boundary rather than claiming all host activity was offline.

## Experiment sequence

1. Inspect existing platform contracts and establish a bounded controller.
2. Provision an isolated local VM, build runtimes, and verify asset hashes.
3. Run automated controller, input, subprocess, and cancellation regressions on Linux.
4. Run real text and synthetic-audio integration tests, including network-isolated execution.
5. Test a simpler direct text path to separate transcription failures from answer failures.
6. Record the observed results, failed attempts, limitations, and Jetson acceptance checklist locally.

## Metrics and interpretation

Record pass/fail, stage wall times in seconds, actual model/runtime identities, generated WAV duration, and relevant process memory where available. Timing is VM development evidence only; do not extrapolate to Jetson or pool with Apple measurements. A few smoke trials do not support percentiles or general conversation-quality claims. A nonempty model answer is functional evidence, not a correctness score.

## Completion condition

Runnable source, a reproducible VM, pinned setup, passing Linux regression checks, real offline pipeline evidence, an explicit deployment path, and a sanitized result record with remaining hardware checks. Publish source and technical evidence under the laboratory public memory policy; exclude runtime artifacts and private machine data.

## Next smallest question

Does the same program work on the physical Jetson with the selected JetPack release, real USB audio/button, and sufficient measured memory and latency headroom?
