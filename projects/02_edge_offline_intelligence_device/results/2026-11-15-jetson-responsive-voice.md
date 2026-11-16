# Resident and streaming Jetson voice

**Date:** November 15, 2026. **Scope:** Authorized latency optimization on one
Orin Nano Super 8 GB, retaining Gemma 4 E2B Q4_K_M, Whisper tiny.en, and Piper
LJ Speech medium. This is a development check, not a general sub-second guarantee.

## Measured result

Three fixed authored spoken questions were synthesized once and used for three
repetitions per configuration. All measurements below begin with the completed
input WAV and end immediately before the first ALSA playback call. They include
recognition, answer generation to the first complete phrase, and speech synthesis.
Microphone capture, physical button event delivery and acoustic onset are excluded.

| Configuration | Trials | Median seconds | Range seconds | Below one second |
| --- | --- | --- | --- | --- |
| Previous sequential implementation | 9 | 5.428 | 4.775–8.762 | 0/9 |
| Resident speech workers and phrase streaming | 9 | 0.945 | 0.825–1.166 | 8/9 |
| Final profile, also reusing exact prompt prefixes | 9 | **0.827** | **0.795–0.970** | **9/9** |

The final sample median is about 6.6 times faster than the sequential sample
median. This is a comparison of these authored runs, not a predicted speedup for
arbitrary questions. The three cases are a short factual question, a plant/sunlight
question, and a request for two walking supplies. All nine final transcripts and
answers exactly matched the sequential outputs. Both profiles mistranscribed the
synthetic plant question as “Why do plant seed sunlight?”; the packing answer still
named a third item despite a request for two. Matching output is not scored quality.

The first comparison ran sequential first, resident second; a regression-test
process ran during portions of that comparison. The final prefix-cache run was
separate, with no concurrent regression tests. Cache/order effects and a small
workload prevent causal attribution of every millisecond. The [complete authored
artifact](2026-11-15-jetson-responsive-voice.json) includes all 27 comparison turns,
provenance, intermediate timings and the final configuration. A preliminary
resident-only probe also completed three France turns at 0.933, 0.882 and 0.855
seconds; those selection probes are not pooled into the table.

## Implementation and provenance

- `ResponsiveBackend` loads and warms the answer server and two owned speech
  workers before ready. Measured resident-profile startup took 52.329 seconds in
  one run. Startup is amber, and recording presses during startup are ignored.
- Piper's installed Python API keeps the voice in memory. Whisper uses a small
  C ABI adapter linked against the existing pinned CUDA library, retaining English
  five-beam decoding and four CPU threads. Timestamp-token generation is disabled;
  each recognition request has no previous utterance context.
- Recognition runs provisionally during recording. Only an exact final PCM match
  can reuse a provisional transcript; any new audio requires a full final pass.
  No quiet trailing correction is removed to meet a latency target. The final
  nine-trial file benchmark did not use provisional capture work.
- Gemma SSE replies feed complete sentence/clause phrases into a two-item bounded
  synthesis queue; playback overlaps later synthesis/generation. Context remains
  2,048 tokens, output cap 128 tokens, temperature zero, seed 42, and the prompt is
  unchanged. Exact common prompt tokens are reused in RAM by llama.cpp; every
  request still contains just the system prompt and current question. No disk cache,
  conversation history, downloads, or cloud inference path was added.
- Device mode can play complete phrases before a later stream error. It stops
  remaining speech on failure; already spoken phrases cannot be retracted. CLI
  `ask` retains complete-answer validation and export behavior.
- Models, voice, native runtime commits, CUDA 12.6, operating system and 25 W mode
  are unchanged from the [Gemma/Piper upgrade](2026-11-15-jetson-gemma4-piper.md).
  Model/voice locks and the prompt hash are included in the artifact. No platform
  comparison or higher-power tuning is claimed.

## Failure, cancellation and physical-output checks

All **55 regressions passed** on the target, covering worker reuse and recovery,
stream truncation/disconnection/control output, bounded responses, numeric-text
phrase boundaries, overlap, startup controls, quiet trailing input preservation,
content-free metrics, cancellation and transient cleanup. An early run exposed
unclosed pipe handles; explicit closure fixed it and the final run passed with
ResourceWarning checks enabled. Cancelling playback after generation has already
finished now retains the answer server; active generation cancellation still reaps
it and reloads before ready.

Real-model checks passed recognition cancellation (0.140 seconds), speech worker
cancellation (0.073 seconds), and active answer generation cancellation (1.569
seconds), with owned processes reaped. Actual ALSA playback cancellation and
recovery passed, and transient workspace cleanup passed. These timings were
measured before the final exact-prefix-cache switch; ownership/cancellation code
is shared, with an additional regression for preserving a finished answer server.

Two authored capture replays exercised the recording observer, resident recognition,
streaming and actual USB speaker. They reached playback requests 1.029 and 1.006
seconds after the simulated finish event, and completed playback after 3.265 and
3.174 seconds. They preceded prefix caching and did not open a microphone. This
is a physical output-path check, not human listening acceptance or acoustic-onset
measurement. The reusable `scripts/responsive_runtime_check.py` supplies only
fixed authored input and never opens the microphone.

## Deployment and remaining limits

The optimized application is deployed through the existing enabled system service.
It completed startup and reached ready with three owned model/voice processes;
the service and all three children have only loopback in their actual network
namespaces. The previous application is retained as a machine-local rollback. The
service unit, audio routing, button firmware and filesystem isolation are unchanged.
One deliberate application restart activated the update; subsequent stability is
checked separately from that requested restart.

The owner subsequently confirmed that two physical-button answers were fast and
complete. Their recorded times from the button ending capture to the first playback
request were **1.113 and 1.061 seconds**, with playback completing after 3.283 and
3.472 seconds. Both returned to ready, with no additional service restart. No live
utterances or audio were retained in this record. These live results support an
approximately one-second experience, but neither met a strict sub-second threshold;
the nine synthetic sub-second results must not be substituted for them. Acoustic
onset was not instrumented.

No new
profile-specific reboot test, long-session resource qualification, noise/accent
accuracy study or representative latency distribution is claimed. One second
remains a target for useful audible response, not a universal guarantee established
by the short synthetic workload.

See the [responsive contract](../development/jetson_responsive_voice.md),
[application guide](../software/jetson/README.md), and reproducible
`scripts/responsive_check.py` (`--no-prefix-cache` reproduces the intermediate
resident-only condition).
