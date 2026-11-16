# Jetson live reply latency profile

**Date:** November 15, 2026

**Configuration:** Deployed Gemma 4 E2B Q4_K_M, CUDA Whisper tiny.en, Piper 1.8.0 / LJ Speech medium CPU voice. See the [deployment record](2026-11-15-jetson-gemma4-piper.md). This profile is diagnostic, not a scored performance study.

## Two observed physical button turns

Intervals were computed from the service's existing journal state timestamps. No words, transcripts, or microphone audio were retrieved or retained. The origin is the controller's `finishing` state following the second button press; the button's electrical/USB latency is not separately measured.

| Stage or interval | First turn, seconds | Second turn, seconds |
| --- | --- | --- |
| Capture finalization | 0.045 | 0.048 |
| Recognition | 3.619 | 4.248 |
| Answer, including first server load | 30.572 | 0.742 |
| Speech synthesis | 4.963 | 3.618 |
| Playback call through completion | 2.205 | 2.503 |
| Recording finish to playback request | **39.198** | **8.657** |
| Recording finish to playback completion | **41.402** | **11.160** |

The recording intervals themselves were 6.345 and 2.243 seconds and are excluded
from those response-delay totals. `speaking` is emitted immediately before the
ALSA playback call, so this measures a software request rather than acoustic
first-sound onset. Journal buffering and scheduling can affect timestamps. These
are different live questions, with no retained content and no matched quality
claim. Two turns cannot establish latency percentiles.

For the warm turn, recognition accounts for about 49% of the wait before playback,
synthesis 42%, and answering 9%. Further answer-token acceleration alone would
have little effect on that observed warm delay.

## Authored component probes

The current Gemma service remained resident while these probes ran separately.
Only fixed authored speech/text was used; temporary speech fixtures were deleted.
The [sanitized diagnostic artifact](2026-11-15-jetson-latency-profile.json) records
all reported intervals.

**Piper:** In one process, imports took 0.256 seconds and loading the deployed voice
took 2.679 seconds. Two syntheses of the same short authored sentence then took
0.267 and 0.232 seconds, producing about 2.1 seconds of audio each. This directly
shows repeated voice initialization is avoidable work. It does not establish the
latency or memory behavior of an implemented persistent worker.

**Whisper:** A single authored clip took 1.205 seconds wall time, with 407 ms of
reported model loading and 243 ms encoding. Processing two copies in one process
took 1.266 seconds total, with 266 ms of reported loading and 286 ms total encoding.
The inputs were synthetic and the sequential probes had different cache state.
Their faster times do not explain all of the 4.248-second live recognition stage;
acoustics, decoder work, initialization, and cache effects need separation in a
subsequent instrumented check. No private live speech was replayed.

## Preferred optimization order

1. **Keep Piper loaded in an owned worker.** The measured 2.679-second voice load is
   the clearest recurring cost. Preserve bounded stdin/IPC, no content logging,
   cancellation by terminating/restarting the worker, transient output cleanup,
   and CPU execution. Verify memory with Gemma and recognition resident.
2. **Reuse Whisper's loaded runtime and collect safe internal stage metrics.**
   Test matched live-duration authored audio and representative opt-in spoken
   turns; do not promise removal of the whole live recognition stage from the
   synthetic reuse result. Keep each request context-free and retain cancellation.
3. **Load Gemma during service startup, before signaling ready.** This moves the
   first model-load delay out of the first question; it does not eliminate boot
   work. The button should indicate startup and accept recording only when ready.
4. Defer streaming speech and model/power tuning until the recurring startup costs
   are addressed. Current warm answer generation is already below one second for
   the observed short reply; speech should not be sped up merely to shorten its
   natural playback duration.

These are measured priorities, not deployed optimizations or a promised speedup.
The deployed profile still creates a Whisper process and a Piper process per turn
and starts the answer model on first use. A follow-up change should measure the
same bounded workloads, first and warm turns, cleanup/recovery, loopback-only
isolation, and physical listening before claiming an improved end-to-end result.
