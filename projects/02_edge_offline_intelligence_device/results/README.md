# Results

**Zero published comparative quality or performance measurements for the macOS, iOS, or Jetson iterations.**

The [September 15 Linux ARM64 VM development record](2026-09-15-linux-vm-development.md) documents implementation checks for the Jetson-oriented voice application. Its CPU timing, model smoke checks, service tests, and compiled button firmware do not establish physical Jetson behavior or comparative model quality.

The September 12 [development status](../status.md) records the working Mac voice-to-text-answer slice with manual English read-aloud, seventeen shared automated tests, and a native iPhone app running typed-answer and manual-speech checks in the simulator. Apple accepted and processed Local Voice Lab 0.3.0 (build 5) for the internal owner group. The owner subsequently confirmed basic operation on their iPhone. The device/OS and individual feature paths were not specified. These are implementation checks and an owner report; they do not establish model quality, tail latency, phone memory fitness, or Jetson performance.

Each platform's measured evaluation should publish:

1. A dated summary with the frozen question, workload, scoring rubric, thresholds, and decision.
2. Sanitized provenance: hardware class, OS/build, runtime, available model identity, open-model revision/hash/quantization where applicable, prompts, context/output controls, speech locale/assets, and workload revision.
3. Attempt accounting, including failures, cancellations, timeouts, exclusions, and reasons.
4. Answer usefulness and transcription errors, with approved examples of failure.
5. End-of-recording to first visible answer and final-answer latency distributions; separate cold starts and model-only timings; report sample counts with p50, p95, maximum, and p99 only with an explicit small-sample caveat when appropriate.
6. App footprint and peak memory, shared system asset requirements where observable, thermal/battery observations on iPhone, and instrumented device energy/thermals on Jetson.
7. The offline test method and its limits. Setup downloads, OS background traffic, and app inference traffic are distinct categories.
8. At least one stress or removal comparison and a clear continue, narrow, switch, or stop decision.

Do not pool platform results. A successful simulator run or Mac benchmark does not establish physical iPhone or Jetson behavior. Publish negative and inconclusive findings; never count missing runs as passes or omit slow failures from attempt accounting. Commit only synthetic or explicitly approved content and sanitized measurements.
