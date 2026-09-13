# Results

**Zero published comparative quality or performance measurements for the macOS, iOS, or Jetson iterations.**

The September 12 [development status](../status.md) records a working Mac voice-to-text-answer slice, seven automated checks, real local answer and synthetic speech checks, and owner confirmation of live voice input and visible text responses. These are implementation checks; they do not establish model quality, tail latency, phone memory fitness, or Jetson performance.

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
