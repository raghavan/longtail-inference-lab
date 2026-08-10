# End-to-end local voice loop

**Status:** verified in stub mode — health check, page load, and a full audio round trip through
the pipeline into a returned WAV. The real-model path has not yet been run against models or a
microphone.

A browser page that looks like the device, backed by a local server that runs the same pipeline the
device experiment tests: local speech recognition, the same four-bit compact instruct model planned
for the Jetson, and a local voice. One **Ask** button. Nothing leaves your machine.

This is the rehearsal for the Jetson build. The same `server.py` and the same page run on the
device; only the model sizes and the host change.

## Run it

### First, without any models

```bash
cd projects/02_edge_offline_intelligence_device/software
python3 app/server.py --stub
```

Open <http://127.0.0.1:8080>. Press **Ask**, say anything, pause. Stub mode ignores what you said
and returns a canned answer, but it exercises every step: microphone capture, WAV encoding, upload,
the pipeline, audio synthesis, and playback. If this works, everything after it is an install
problem rather than a code problem.

Requires nothing beyond the standard library.

### Then, for real

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install faster-whisper
ollama pull qwen3:4b            # install from ollama.com/download first
```

One Piper voice, both files — the `.onnx` and its `.json` sidecar, or synthesis fails:

```bash
mkdir -p voices && cd voices
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ..
pip install piper-tts
```

Then:

```bash
python3 app/server.py --stt-model small.en --llm-model qwen3:4b
```

The first start downloads the speech model, so give it a minute. `sounddevice` is not needed here —
the browser does the capture.

## What happens when you press Ask

1. The page captures from the microphone, watching level. It stops on about 1.4 s of silence, or
   when you press **Stop**, or at 30 s.
2. Audio is resampled to 16 kHz mono and encoded as WAV in the browser. No codec is involved, so
   the server never has to guess at a container format.
3. `POST /api/ask` runs the same `run_interaction` the command-line pilot uses, writing the same
   ledger.
4. The answer comes back as text plus a WAV, and the page plays it.

The dial shows the real signal at each step. While listening it draws your microphone; while
speaking it draws the answer audio. Only the thinking symbol — a sweeping arc with a pulsing core —
is generated, because there is no signal to show while the model works.

## Options

| Flag | Default | Note |
| --- | --- | --- |
| `--stub` | off | No models. Verifies the whole path. |
| `--stt-model` | `small.en` | `base.en` or `tiny.en` on a smaller machine |
| `--llm-model` | `qwen3:4b` | The model planned for the device |
| `--piper-voice` | `voices/en_US-lessac-medium.onnx` | Relative paths resolve from `software/` |
| `--residency` | `resident` | `sequential` loads and unloads around each turn |
| `--port` | `8080` | |
| `--out` | `runs/app.jsonl` | Ledger location |

## Which numbers here mean anything

The page shows recognition, first token, generation, and voice timings. Those are real and are
measured on the server around the same stages the experiment defines.

**The total is not a first-word latency measurement.** Capture, upload, decoding, and playback all
happen outside it, and the server synthesises the whole answer before sending any of it, so the
sentence-streaming behaviour the experiment tests is invisible here. `synthesis` is pinned to
`whole` for that reason, and every ledger line this app writes carries `is_measurement: false`.

For latency figures that mean something, use the command-line pilot. For figures that mean
something *about the device*, wait for the hardware.

## Enclosure scale

The cabinet is drawn at the proportions the real parts require:

| Component | W × D × H (mm) |
| --- | --- |
| Jetson Orin Nano Super Developer Kit | 100 × 79 × 21 |
| M5Stack Atom VoiceS3R | 24 × 24 × 17 |
| NVMe M.2 2280, inside the devkit envelope | 80 × 22 × 3.5 |
| USB-C PD battery pack, **assumed** | 105 × 52 × 26 |
| Airflow gap above the thermal solution | 8 |
| Wall thickness per face | 3 |
| **Cabinet** | **112 × 86 × 62** |

The devkit lies flat with the battery beneath it. **Show actual size** on the page renders the face
at roughly 1 mm to 1 mm so you can judge whether it is an object worth picking up. Only the battery
line is assumed; the rest come from published dimensions.

The ReSpeaker in the bill of materials is deliberately absent — it is bench instrumentation for the
latency experiment, not a part of the finished object.

## Moving this to the Jetson

Unchanged: the page, `server.py`, the pipeline, and the ledger schema.

Changes: `--stt-model` probably drops to `base.en` under the 8 GB ceiling, the answer model becomes
a four-bit build, `--host 0.0.0.0` if you want to reach it from another machine on the bench, and
the service starts at boot instead of from a shell.

Two things this app does not yet do, both of which the device needs: it has no physical control, and
it has no microphone cut. Both are hardware, and both are why this is a rehearsal rather than the
device.

## Privacy

Audio stays on the machine. The browser talks to localhost, and the server talks to Ollama on
localhost. Recordings are written to a scratch directory while a turn is in flight — that is a
development convenience and contradicts the design direction's default of retaining no raw audio,
so it must be removed before anything resembling daily use. Ledgers land in `runs/`, which is
ignored by git.
