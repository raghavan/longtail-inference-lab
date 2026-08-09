# Laptop pilot for the local voice loop

**Status:** runnable. Dry run verified; the real-backend path has not been run against models or an audio device.

This is the complete conversation controller from the design direction — capture, speech recognition, answer generation, speech synthesis, playback — written to run on an ordinary laptop before any hardware is bought.

## What this is, and what it is not

It **is** a pilot: enough of the real system to learn whether the loop is worth building on dedicated hardware, and to develop the software that will later run on that hardware unchanged.

It **is not** Experiment 02.1, and its output is never pooled with device measurements. A laptop is a different hardware condition, so its numbers answer different questions. `analyze.py` prints a warning when a ledger contains dry-run data, and every ledger records `is_measurement` in its provenance line.

### What transfers to the device

| Carries over unchanged | Does not carry over |
| --- | --- |
| Controller state machine and residency policy | Absolute latency — a laptop CPU or GPU is not an Orin |
| Ledger schema and stage boundaries | Peak memory under an 8 GB ceiling |
| Analysis script and percentile reporting | Energy per interaction and idle power |
| Question set and strata | Thermals, throttling, and fan behaviour |
| Prompt and spoken-response style policy | Audio path characteristics |
| Sentence-streaming logic | Anything about battery life |

The point of running it here is that the left column is most of the software work, and it is free to do now.

## Install

Three runtimes, all of which work on macOS, Windows, and Linux.

```bash
# 1. Answer model, through Ollama
#    https://ollama.com/download
ollama pull qwen3:4b

# 2. Speech recognition and audio capture
pip install faster-whisper sounddevice

# 3. Speech synthesis
#    https://github.com/rhasspy/piper  (binary + one voice file)
#    Place the voice next to this README, e.g. software/voices/en_US-lessac-medium.onnx
```

Nothing is required for the dry run. It uses only the standard library.

### Choosing model sizes for your machine

| Machine | Speech recognition | Answer model |
| --- | --- | --- |
| Apple Silicon, 16 GB+ | `small.en` | `qwen3:4b` |
| NVIDIA GPU laptop, 8 GB+ VRAM | `small.en` | `qwen3:4b` |
| CPU only, 16 GB | `base.en` | `qwen3:4b`, expect slow generation |
| CPU only, 8 GB | `tiny.en` | a 1–2 B model; 4 B will thrash |

The device target is a four-bit 4 B model, so matching that on the laptop keeps the comparison meaningful even though absolute timings will not match.

## Run

Start with the dry run. It needs no models, no microphone, and no speaker, and it verifies the state machine and the ledger.

```bash
cd projects/02_edge_offline_intelligence_device/software
python3 controller/main.py --mode dry-run --limit 6 --out runs/dry.jsonl
python3 analyze.py runs/dry.jsonl
```

Then the real loop. Press Enter, speak, press Enter again, and listen.

```bash
python3 controller/main.py \
  --mode interactive \
  --residency resident \
  --synthesis streamed \
  --limit 10 \
  --llm-model qwen3:4b \
  --stt-model base.en \
  --piper-voice voices/en_US-lessac-medium.onnx \
  --out runs/pilot-resident-streamed.jsonl
```

Run all four conditions into one ledger to reproduce the 2×2, then analyze:

```bash
python3 analyze.py runs/pilot.jsonl --target-s 8.0 --offset-ms 0
```

## Testing the offline claim on a laptop

Turn off WiFi and unplug Ethernet before an interactive block. That is a weaker assertion than the device experiment's packet-counter check, and it is deliberately not automated here — a laptop has too many background processes for a zero-packet claim to mean anything. Treat "it still worked with the radio off" as the only offline claim the pilot supports.

## Known measurement limits

These are why the pilot informs the device build rather than substituting for it.

1. **Press-to-start and press-to-stop, not press-and-hold.** A terminal cannot observe a held key portably. This changes what `capture` means but not the primary metric, which begins when recording stops.
2. **Playback submission is approximated by process start.** `SubprocessPlayer` shells out to `afplay`, `aplay`, or PowerShell and returns once the process has launched. The gap between that and audible sound is unmeasured here.
3. **No acoustic offset calibration.** Pass `--offset-ms` to `analyze.py` if you measure it.
4. **Piper runs as a subprocess,** so it has no resident state. The residency arm therefore tests speech recognition and answer model residency only, and `tts_load` will read near zero in both conditions. On the device this is worth revisiting with a library binding.
5. **Ollama manages its own memory.** `load` and `unload` request residency rather than commanding it, so the sequential condition is a request the runtime may not honour exactly.
6. **A laptop is thermally and electrically unconstrained** compared with the target device, and it is doing other work at the same time.

Limits 4 and 5 are worth knowing before reading any result: they mean the pilot's residency arm is softer than the device experiment's, so a null result on residency here is weak evidence, while a large effect would be notable.

## Files

```text
software/
  controller/
    ledger.py      frozen stage schema, timing, JSONL writer
    backends.py    speech, language, synthesis behind one interface, plus stubs
    audio.py       capture and playback
    pipeline.py    the interaction, and the two policies under test
    main.py        command line
  evaluations/
    question_set.jsonl   40 questions in four strata
  analyze.py       distributions, per-stage breakdown, dominant stage at p95
```

## Publication rules

Ledgers from your own machine may contain host details, so they are not committed by default. If you want to publish a pilot result, put it under `results/` with a dated folder, strip host identifiers, and run `python3 areas/lab_operations/safety_scan.py` first. Label it a pilot, on general-purpose hardware, in the summary's first line.

## Interface prototype

`ui/index.html` is a front-end mockup of the finished object: a mid-century tabletop set in
pistachio and cream, with the frequency graphs living inside the tuning dial. Open it directly in a
browser, or serve it:

```bash
python3 -m http.server 8000 --directory ui
# then open http://localhost:8000
```

Hold the bar or the space key to speak; `M` cuts the microphone. The traces are generated, not
measured — there is no microphone, recognition, or model behind the page. It exists to test whether
listening, working, and speaking read at a glance without a screen full of text, which is the
interaction question the design direction raises and no amount of prose settles.

Two details are deliberate rather than decorative. The stage names in the telemetry strip are the
frozen ledger schema from the experiment spec, so the mock and a real ledger line describe the same
thing. And cutting the microphone overrides every other state, because that is the one behaviour the
finished device must guarantee in hardware rather than software.

Wiring it to the real controller is a later step: the controller already knows its state at every
moment, so a small local event stream could drive the panel instead of the random generator.
