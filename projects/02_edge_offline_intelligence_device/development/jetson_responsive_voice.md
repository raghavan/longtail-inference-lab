# Responsive offline Jetson voice

Authorized continuation: reduce time from the button ending recording to useful
speech, targeting one second without claiming that threshold before measurement.
EGM artifact directory: this development directory. Reuse the Linux intake and
Gemma/Piper upgrade contract; the changes below explicitly extend their execution
and partial-output behavior. No hardware, answer model, quantization, voice,
network isolation, conversation history, or power-mode change is planned.

## Execution contract

- Device mode loads and warms owned Gemma, Whisper, and Piper processes before
  signaling ready. Startup is amber; recording presses during startup are ignored.
  CLI single-turn/export mode retains complete-answer validation and behavior.
- Whisper runs through a small C ABI adapter built against the pinned source and
  existing native library. English beam search retains five beams; timestamp token generation is disabled because the application consumes text only. Use context-free
  decoding; no past question text is supplied. Piper uses its installed Python
  API with CPU execution. Both workers use bounded private pipes, not new sockets.
- During capture, a single provisional recognition worker receives at most one
  pending whole-prefix snapshot every 750 ms. Its output is never answered early.
  An exactly matching final PCM buffer can reuse it; any added samples require a
  full final pass. No silence/VAD heuristic may drop quiet trailing corrections.
  This conservative version may provide little latency reduction beyond keeping
  recognition warm; report measured benefit honestly.
- Gemma reuses only the exact common token prefix through llama.cpp prompt caching. Each request still supplies exactly the system prompt and current utterance; no prior turn is appended and no cache is written to disk.
- Gemma SSE content is validated and split at sentence/clause boundaries.
  Synthesis overlaps later answer generation; playback overlaps later synthesis.
  Each queue holds at most two entries. Total text remains 4,000 characters and
  aggregate generated speech at most 120 seconds, within transient RAM limits.
- Device streaming deliberately replaces the earlier all-or-nothing output rule:
  complete phrases may have played before a later failure or output-limit event.
  Stop remaining output and signal an error; never claim those phrases were
  retracted. Hold an unfinished tail until a successful stop event. Reject tool
  calls, special markup, malformed/oversized streams and missing completion.
- Cancellation stops owned generation, speech and playback processes and removes
  transient audio. Workers that were stopped are reloaded before ready. Shutdown
  cancels startup and active work. No speech content appears in logs; only bounded
  state/error events and numeric durations do.

## Verification and release

Check real worker reuse, startup readiness, partial-stream failures, cancellation
at recognition/generation/synthesis/playback, recovery, final-input completeness,
queue bounds and temporary cleanup. Run existing regressions and additional tests.
Compare fixed authored short questions with the committed previous implementation
on the same board. Separately report startup, transcription, first phrase,
playback request and playback completion; software playback request is not acoustic
onset. Do not fabricate a one-second result or count an acknowledgement as speech.

Stage separately, retain the preceding application and service rollback, and
activate only after checks. Verify the actual service namespace, resource use,
startup/ready state and owner listening. New physical listening/reboot evidence is
separate from automated tests. Publish only authored examples and sanitized timing.
