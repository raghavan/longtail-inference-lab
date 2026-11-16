# Local Voice for Linux and Jetson development

**Status:** The physical Jetson runs Gemma 4 E2B Q4_K_M, CUDA Whisper recognition, and resident Piper neural speech. The [responsive voice record](../../results/2026-11-15-jetson-responsive-voice.md) reports 55 passing regressions and nine final authored trials at 0.795–0.970 seconds to a playback request (median 0.827 seconds; acoustic onset and live microphone excluded). It records intermediate conditions, failures, cancellation, deployment and remaining limits. The [model/voice upgrade](../../results/2026-11-15-jetson-gemma4-piper.md) retains asset provenance; its earlier sequential timing is not the current execution path.

An offline, single-turn English voice application:

```text
USB button or keyboard → ALSA microphone → whisper.cpp → llama.cpp → Piper → ALSA speaker
                              ↓                ↓             ↓
                         transient WAV    local models   transient WAV
```

The program is designed for Orin Nano Super 8 GB and has a real Linux ARM64 CPU implementation. Its CUDA profile has been built and run on the physical board, with GPU transcription and all answer-model layers offloaded. Apple frameworks and models are not used. There is no web access, retrieval, conversation memory, external action, or cloud fallback.

## Responsive device execution

Device mode keeps Whisper and Piper in owned pipe workers and warms Gemma before
signaling ready. The button is amber during startup (about 52 seconds in one
observed run); presses then are ignored. No new network listener is introduced.
Recognition runs provisionally during capture, but any additional audio forces a
final full pass so quiet trailing corrections are preserved. Answer generation,
phrase synthesis and playback overlap. Gemma reuses exact matching prompt prefixes in RAM; requests still contain only the system prompt and current question. CLI `ask` retains sequential export behavior.

For an existing native installation, build the small adapter without downloading
or rebuilding the model runtimes (use the source path for your installation):

```bash
python3 scripts/build_speech_worker.py --root "$HOME/.local/share/longtail-voice" --source "$HOME/.local/share/longtail-voice/sources/whisper_cpp" --backend cuda
python3 -m local_voice --backend cuda doctor --responsive --verify-hashes --audio
```

Fresh `setup_runtime.py` installations build the adapter automatically for the
selected backend. Recognition retains English beam search (five beams), disables
timestamp tokens, and passes no prior utterance context. All assets stay pinned.
`local_voice/responsive.py`, `speech_worker.py`, and `native/whisper_worker.cpp`
implement the [responsive contract](../../development/jetson_responsive_voice.md).

The service emits numeric latency events without words or audio. The metric
`finish_to_playback_request` ends immediately before ALSA playback, not at measured
acoustic onset. A software timestamp below one second is not proof that every live
question becomes audible within one second. The reproducible authored comparison is:

```bash
python3 scripts/responsive_check.py --root /path/to/runtime --output /path/to/new-report.json
```

Use only one resident answer deployment while checking on an 8 GB board. Keep the
previous application directory as rollback; restoring it and restarting the service
restores the sequential behavior. The service sandbox, audio routing and firmware
are unchanged by this application update.

## What is included

- A command-line text/WAV mode for reproducible model checks.
- A device mode: press to start recording, press to finish and answer, press during processing/playback to cancel. Recording automatically ends at 30 seconds. After cancellation, stopped workers reload before green/ready; the next press starts a fresh turn.
- An AtomS3-Lite firmware project and bounded USB serial protocol, with status LED and connection heartbeat. Firmware was flashed and basic button/LED/voice interaction passed on the physical device; extended reconnect/cancellation reliability remains open.
- Local runtime readiness and SHA-256 checks, pinned source/model identities, and a separate explicit online setup script.
- Linux regressions, real-model smoke/failure checks, a VM lifecycle helper, and a startup-service generator.

## Start here

Get the source on your development computer, then run the commands in this guide from the application directory unless a step says otherwise:

```bash
git clone https://github.com/raghavan/longtail-inference-lab.git
cd longtail-inference-lab/projects/02_edge_offline_intelligence_device/software/jetson
```

| Task | Entry point | What it establishes |
| --- | --- | --- |
| Test before owning a Jetson | [Fresh Ubuntu ARM64 VM](#reproduce-on-a-fresh-vm) on an Apple silicon Mac | Linux CPU integration and controlled failure handling |
| Repeat tests in an already-provisioned VM | [Existing VM commands](#use-the-existing-local-vm) | Rechecks the current source in that VM |
| Install the application on a bootable Jetson | [Jetson deployment](#deploy-to-the-actual-jetson) | CPU baseline first, followed by explicitly unvalidated CUDA and hardware gates |
| Program the physical control | [Button firmware](#atoms3-lite-button-firmware) | Firmware build, then a separate hardware upload/check |
| Review what actually passed | [Dated validation report](../../results/2026-09-15-linux-vm-development.md) | 38 regression tests and real offline model/service evidence, with limitations |

This repository supplies application source and installation tools. It is not a bootable Jetson image or a Jetson GPU emulator. Model weights are downloaded during explicit setup and are not bundled in Git.

## Runtime choices and limits

| Component | Development choice | Boundary |
| --- | --- | --- |
| Speech recognition | Whisper tiny.en, F16, whisper.cpp | Compact English baseline; human speech/noise accuracy not scored |
| Answer model | Gemma 4 E2B instruction model, Unsloth Q4_K_M GGUF, llama.cpp | Text answering with thinking disabled; usefulness not scored |
| Speech output | Piper 1.8.0, en_US-ljspeech-medium, CPU ONNX Runtime | Neural English voice; resident worker in device mode |
| Controller | Python standard library; separate Python 3.10 Piper environment | One active operation; pinned ARM64 voice wheels required |
| Audio | ALSA `arecord` and `aplay` | Actual device selection and permissions need on-board qualification |

Exact commits, model revisions, hashes, and licenses are in `runtime-lock.json`. Models and source builds live outside the repository by default. llama.cpp and whisper.cpp are MIT licensed; Gemma 4 is Apache-2.0; Piper is GPL-3.0-or-later. The voice card identifies a public-domain LJ Speech dataset. eSpeak remains a synthetic fixture generator, not answer synthesis. Their upstream license requirements still apply if a packaged product is later distributed.

Input is at most 1,200 characters or 30 seconds of mono, 16 kHz, signed 16-bit PCM WAV. Near-zero audio is rejected before transcription; this is not a full voice activity detector. Context is 2,048 tokens. Output defaults to 128 model tokens, bounded to a maximum of 384, and 4,000 characters. CLI mode discards a response that exhausts its token allowance. Device mode streams complete phrases: a later error stops remaining speech, but previously spoken phrases cannot be retracted. An unfinished final phrase is held until successful completion. Sampling uses temperature 0 and seed 42, with Gemma thinking disabled. Leaked model control tokens are rejected before synthesis. Each turn supplies only the fixed system prompt and the current utterance; there is no retrieval or saved conversation.

Deadlines are per stage: model-server startup 120 seconds, transcription 60 seconds, answer 120 seconds, synthesis 30 seconds, and playback 120 seconds. They are protective caps, not desired response times or measured Jetson performance. A model can still give incorrect answers.

The default system prompt is versioned in `local_voice/core.py`. To customize it, put a local UTF-8 prompt in a file outside the repository and use `--system-prompt-file` before `ask` or `device`; the service generator accepts the same option. Prompt files are limited to 1,200 characters. Changing the prompt creates a different evaluation condition and does not inherit the default prompt's smoke observations.

## Use the existing local VM

The recorded VM snapshot predates Gemma/Piper. Source sync alone does not install
this profile: run model setup and the neural-voice installation below before
current-source inference checks. The current upgrade was qualified on the physical
Jetson; the earlier VM evidence belongs to its recorded configuration.

From this directory on the Mac:

```bash
limactl start --tty=false longtail-jetson
bash scripts/vm.sh sync
bash scripts/vm.sh test
bash scripts/vm.sh smoke
```

The VM uses four virtual CPUs, 6 GiB configured memory, and a 24 GiB sparse disk. It has no shared host-directory mounts. `sync` copies only this source tree into `~/voice-app` inside the guest. It excludes model caches, local results, build products, and virtual environments. It does not commit or publish anything.

Open a guest shell with `bash scripts/vm.sh shell`, then:

```bash
cd ~/voice-app
python3 -m local_voice doctor --verify-hashes
python3 -m local_voice ask --text 'Name two things to pack for a short walk.' --show-text
```

Default output reports completion and stage times. `--show-text` explicitly prints the transcript and answer. For private typed input, prefer `--stdin` to avoid placing text in command arguments. `ask` synthesizes speech even when playback/export is not requested; the temporary audio is then deleted.

To retain a speech file explicitly:

```bash
python3 -m local_voice ask --text 'Say a short friendly greeting.' --output greeting.wav --show-text
```

An existing output file is never overwritten. WAV export is opt-in; exported files are the user's responsibility and ignored by this directory's Git rules. The VM has no physical microphone/speaker attached. Its file-based audio checks do not prove acoustic playback or capture.

Stop the VM when finished to release its memory:

```bash
bash scripts/vm.sh stop
```

## Reproduce on a fresh VM

Install Lima on the Apple silicon Mac if needed with `brew install lima`. These commands create the `longtail-jetson` VM; use the existing-VM section if that instance already exists. Then:

```bash
bash scripts/vm.sh create
bash scripts/vm.sh sync
bash scripts/vm.sh shell
```

Inside the guest:

```bash
cd ~/voice-app
bash scripts/install_linux_deps.sh
python3 scripts/setup_runtime.py --backend cpu
python3 scripts/setup_voice.py --wheel-dir /path/to/verified-voice-wheels
python3 -m local_voice doctor --verify-hashes
python3 -m unittest discover -s tests -v
bash scripts/offline_check.sh
python3 scripts/runtime_check.py
python3 scripts/service_check.py
```

The regression runner should end with `Ran 55 tests` and `OK`. The smoke and runtime/service scripts must exit with status 0 and report `"status": "passed"`. The smoke report must list only `lo` under `network_interfaces`. A passing `doctor` checks assets/executables, not real microphone, speaker, or GPU operation. Firmware compilation is a separate command in the button section.

`vm.yaml` pins the Ubuntu image and checksum used for the observed run. If Ubuntu retires that snapshot URL, deliberately select and record a replacement image/digest; do not silently call it the same environment. Apt security updates can change package versions; the observed versions are recorded with results.

Online setup downloads two source trees and approximately 3.25 GB of answer, recognition, and voice model/config files. It builds CPU runtimes on ARM64 and verifies the weights before installing them. Setup uses the network; application inference does not invoke the setup code. Re-running setup reuses verified model files and the pinned source/build trees.

`offline_check.sh` creates a new network namespace for the test process tree, brings up only loopback, and runs inference as the invoking non-root user. It does not disable the whole VM's network. `service_check.py` uses `sudo` to create one temporary system service, checks it, and removes it; it deliberately uses a nonexistent capture device and a pseudo terminal, so no person is recorded.

## Install the neural voice dependencies

The controller uses the system Python; Piper runs in a separate `tts-venv` under
the selected runtime root. This release locks Linux ARM64/Python 3.10 wheels.
Download them on an internet-connected setup host (the Mac can cross-download):

```bash
python3 -m pip download --only-binary=:all: \
  --platform manylinux_2_28_aarch64 --platform manylinux2014_aarch64 \
  --python-version 310 --implementation cp --abi cp310 --abi abi3 \
  --require-hashes -r piper-requirements.txt --dest /path/to/verified-voice-wheels
```

Copy that wheel directory to the target, then run `scripts/setup_voice.py` there
with `--wheel-dir` pointing at it. Pass the same `--root` used by model setup and
the application if using a separate deployment root. The installer checks every
required wheel and the pip bootstrap hash before execution, uses `--no-index`,
and checks installed dependencies. `setup_runtime.py` separately downloads and
verifies the voice ONNX/config alongside the answer and transcription models.
Inference never calls either installer. English phonemization assets are included
in Piper's wheel; no cloud voice endpoint is used.

## Deploy to the actual Jetson

**Prerequisite:** complete board/firmware/storage setup using the official installation instructions for the chosen JetPack release. This application does not flash the board or prepare the SD card. The observed board runs Ubuntu 22.04.5, L4T R36.4.4, and CUDA 12.6. Record the actual installed release before building on another board.

For a new board, follow [NVIDIA's JetPack 6.2.1 installation guide](https://docs.nvidia.com/jetson/jetpack/6.2.1/install-setup/index.html), including its firmware check before a JetPack 6.x SD-card boot. Its SDK Manager route requires a supported Ubuntu x64 host; this ARM64 application-test VM is not that flashing host. Resolve the board's installation method first, then use the steps below to install the application onto its running Linux system.

1. Put the Jetson and Mac on the local network, enable SSH during device setup, and copy this directory using `scp`/`rsync`. Do not copy the Mac's Python environment or the VM's build symlinks. The placeholder destination below must be replaced with your Jetson account and address; keep real connection details out of Git.

   ```bash
   scp -r ./jetson USERNAME@JETSON_ADDRESS:~/voice-app
   ```

   Run that transfer from the parent `software/` directory, then open an SSH session using your device's account and address. The following commands run **on Jetson**.

2. Build and test a CPU baseline directly on the target (install the verified voice wheels as described above):

   ```bash
   cd ~/voice-app
   bash scripts/install_linux_deps.sh
   python3 scripts/setup_runtime.py --backend cpu
python3 scripts/setup_voice.py --wheel-dir /path/to/verified-voice-wheels
   python3 -m local_voice doctor --verify-hashes --audio
   python3 -m local_voice ask --text 'Name a primary color.' --show-text
   ```

3. Build the optional GPU profile only after the JetPack CUDA toolkit is installed and `nvcc` is available:

   ```bash
   python3 scripts/setup_runtime.py --backend cuda --jobs 4
   python3 -m local_voice --backend cuda doctor --verify-hashes --audio
   python3 -m local_voice --backend cuda ask --text 'Name a primary color.' --show-text
   ```

   The CUDA profile builds separately with architecture 87 and explicitly selects `CUDA0` for the answer server. A missing CUDA device must fail instead of silently presenting a CPU run as a GPU result. The November 15 [CUDA check](../../results/2026-11-15-jetson-cuda-check.md) records successful compilation, library loading, full answer-model offload, GPU transcription, and limited timing/resource observations. Verify these on each installation; sustained memory/thermal limits remain unqualified.

4. Identify the USB audio devices using `arecord -l` and `aplay -l`. Qualify capture/playback separately, then run the keyboard-controlled loop:

   ```bash
   python3 -m local_voice device --keyboard
   ```

   Enter starts recording; Enter again ends it and speaks the answer. Enter while busy cancels. `c` cancels explicitly; `q` quits. To select hardware, put `--capture-device` and `--playback-device` **before** `device`, using the ALSA names observed on your board. A `plughw:` device can perform sample-format conversion when the USB microphone's native rate differs. Missing/denied devices produce a visible error and allow retry.

   On a signed-in Ubuntu desktop, PulseAudio may own the USB audio devices. If direct hardware access reports device-busy, use the desktop launcher. It selects the single USB microphone and speaker explicitly, because desktop defaults may change between sessions:

   ```bash
   bash scripts/desktop_device.sh
   ```

   The launcher includes user-local executables in PATH and requires a running desktop sound server. If multiple USB devices exist, set `PULSE_SOURCE` and `PULSE_SINK` to the desired names from `pactl list short sources` and `pactl list short sinks`. It refuses an ambiguous automatic selection. This desktop-session route does not establish headless system-service audio support.

5. Build and flash the button as described below, then run `device --serial` with its actual stable `/dev/serial/by-id/…` path. The keyboard and serial inputs are alternatives, not simultaneous listeners.

6. After the complete manual loop passes, generate and inspect a system service on the Jetson:

   ```bash
   python3 scripts/service_unit.py --serial /dev/serial/by-id/DEVICE > /tmp/longtail-voice.service
   sudo systemd-analyze verify /tmp/longtail-voice.service
   sudo install -m 644 /tmp/longtail-voice.service /etc/systemd/system/longtail-voice.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now longtail-voice.service
   journalctl -u longtail-voice.service -f
   ```

   For the validated standalone USB path, use stable ALSA card names (`plughw:CARD=Device,DEV=0` for the observed microphone and `plughw:CARD=UACDemoV10,DEV=0` for the observed speaker). Verify names on the actual board. The system service must own these devices; a desktop PulseAudio server can otherwise claim them. The November 15 deployment reserves the two observed USB devices with machine-local udev `PULSE_IGNORE=1` rules matched to their vendor/product IDs. This intentionally removes those devices from the desktop PulseAudio launcher while standalone mode is installed. Removing the rules, disabling the service, and reloading/reconnecting audio restores desktop use.

   If speech tools were installed in the user's local executable directory, include that directory in the generated unit's `Environment=PATH=...`; systemd does not read interactive shell profiles. The November 15 unit also sets `StartLimitIntervalSec=0` so a disconnected/reconnected button can recover through the existing five-second restart delay. Save the working mixer level with `sudo alsactl store`. These are machine-local service settings; keep generated units and device identifiers outside Git.

   Replace `DEVICE` with the observed serial identifier. Add `--backend cuda` and the tested audio-device options to the generator only after those paths pass manual checks. Run the generator as the normal application user; it records that user and the local application/runtime locations in the generated machine-local file. Do not commit that generated file.

   The system service grants the `audio` and `dialout` supplementary groups, runs inference as the selected non-root user, isolates external networking, mounts a private 16 MiB tmpfs for transient audio, and terminates the whole process group when stopping. Journal entries contain states and sanitized errors, not utterances. Disable it with `sudo systemctl disable --now longtail-voice.service`. Leave boot autostart disabled until physical testing passes.

Application updates are another source transfer and service restart; routine code changes do not require reflashing the SanDisk card. Preserve a known-working local copy before an update and rerun the on-device checks.

### Check the selected model and voice

Run `python3 scripts/profile_check.py --backend cuda --root /path/to/runtime` for
three fixed authored pipeline turns. Add `--output` to retain an explicit report.
Run `python3 scripts/runtime_check.py --backend cuda --root /path/to/runtime` for
real CLI failure/cancellation checks. The latter does not record the microphone.
The earlier CPU/CUDA result can be reproduced from its source commit `bf0f6a7`;
current-source timings describe Gemma/Piper and must not inherit its results.

### Compare installed CPU and CUDA profiles

After both profiles pass real inference, run the fixed authored development check
on the Jetson with no builds or interactive voice turns running:

```bash
mkdir -p .local-results
python3 scripts/backend_check.py --output .local-results/backend-check.json
```

The output file must not already exist. The check verifies model hashes, runs
CPU-CUDA-CUDA-CPU sessions, and closes each answer server between sessions. Each
session has a cold text turn, a warm text turn, and a warm synthetic-audio turn.
Cold means a new server, not a cold operating-system file cache. Inputs are
authored examples; the check never captures the microphone or plays speech.
It removes temporary synthetic audio and writes only the explicitly requested
report. Stage times exclude recording and playback; synthesis stays on CPU.
Two sessions per profile do not establish quality, tail latency, or performance
on other hardware. Check actual CUDA offload separately: asset readiness alone
does not prove GPU execution. Keep the working CPU profile for rollback.

For updates from the parent `software/` directory, use a trailing source slash to update the existing application directory rather than nesting another directory inside it. With `rsync` available on both machines:

```bash
rsync -a --exclude='.venv' --exclude='.local-results' --exclude='.pio' \
  --exclude='__pycache__' --exclude='build' --exclude='dist' \
  ./jetson/ USERNAME@JETSON_ADDRESS:~/voice-app/
```

On Jetson, restart the installed service only after the updated source passes its checks: `sudo systemctl restart longtail-voice.service`.

## AtomS3-Lite button firmware

`button/` uses PlatformIO, Espressif32 6.9.0, Arduino ESP32 2.0.17, and Adafruit NeoPixel 1.12.3. The firmware initializes USB, GPIO41's button, and GPIO35's RGB LED; it does not initialize Wi-Fi or Bluetooth. Pins and USB settings follow the [M5Stack device documentation](https://docs.m5stack.com/en/core/AtomS3%20Lite).

To reproduce the firmware build inside Linux:

```bash
python3 -m venv ~/.local/share/longtail-voice/firmware-tools
~/.local/share/longtail-voice/firmware-tools/bin/pip install platformio==6.1.18
cd button
~/.local/share/longtail-voice/firmware-tools/bin/pio run
```

Flash later from a machine with the physical board attached using PlatformIO's `run --target upload --upload-port` and the observed device path. The Lima VM has no USB passthrough configured; its firmware compilation does not establish hardware behavior. The subsequent physical bring-up flashed and tested the button from Jetson. Native Mac PlatformIO or the Jetson can perform an upload. Never flash an unidentified serial device.

Protocol is 115200 baud, newline-terminated ASCII. Button sends `PRESS`; application accepts `CANCEL` for integration tools too. Application sends `STATE ready|recording|finishing|transcribing|answering|synthesizing|speaking|cancelling|error` and repeats its current state once per second. Duplicate presses within 200 ms are ignored by the host. LED: green ready, red recording, amber processing/cancelling, cyan speaking, magenta error, dim white waiting/disconnected. A five-second missing heartbeat resets the LED to waiting.

## Retention and measurement boundaries

Normal completion, ordinary errors, and cancellation delete temporary recording/transcript/speech files. The service's private tmpfs also disappears when the service exits. Standalone CLI files in `/dev/shm` can survive an uncatchable process kill until cleanup or reboot; no forensic-erasure guarantee is made. The selected OS controls swap and crash behavior. Explicitly exported WAVs and `--show-text` output are intentionally retained/displayed by the caller.

VM tests establish native ARM64 Linux integration, local inference, bounded failure handling, and service behavior. They do not establish physical Jetson behavior. The linked physical CPU/CUDA records separately establish basic standalone operation and limited development timings, while acoustic quality, sustained power/thermals, long-session stability, and final model usefulness remain open. Run the physical-device acceptance checklist in the validation record before deployment is called complete.
