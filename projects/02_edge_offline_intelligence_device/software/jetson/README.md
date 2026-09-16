# Local Voice for Linux and Jetson development

**Version:** 0.1.0 development slice. **Status:** tested in an Ubuntu 22.04 ARM64 VM using CPU inference. Physical Jetson, CUDA, USB audio, button hardware, and voice naturalness remain unqualified. See the [intake](../../development/jetson_linux_intake.md) and [Linux validation record](../../results/2026-09-15-linux-vm-development.md).

An offline, single-turn English voice application:

```text
USB button or keyboard → ALSA microphone → whisper.cpp → llama.cpp → eSpeak NG → ALSA speaker
                              ↓                ↓             ↓
                         transient WAV    local models   transient WAV
```

The program is designed for Orin Nano Super 8 GB and has a real Linux ARM64 CPU implementation. Its CUDA build profile targets Orin's architecture, but has not been built or run on Jetson. Apple frameworks and models are not used. There is no web access, retrieval, conversation memory, external action, or cloud fallback.

## What is included

- A command-line text/WAV mode for reproducible model checks.
- A device mode: press to start recording, press to finish and answer, press during processing/playback to cancel. Recording automatically ends at 30 seconds. The next press after cancellation starts a fresh turn.
- An AtomS3-Lite firmware project and bounded USB serial protocol, with status LED and connection heartbeat. Firmware compiles; flashing and electrical/USB behavior await the hardware.
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
| Answer model | Qwen2.5 1.5B Instruct, Q4_K_M, llama.cpp | Initial 1–3B-band candidate; general usefulness not evaluated |
| Speech output | eSpeak NG, en-us, 165 words/minute | Functional, robotic voice; not the final natural-speech choice |
| Controller | Python 3.10+, standard library | One active operation; no Python inference wheels needed |
| Audio | ALSA `arecord` and `aplay` | Actual device selection and permissions need on-board qualification |

Exact commits, model revisions, hashes, and licenses are in `runtime-lock.json`. Models and source builds live outside the repository by default. llama.cpp and whisper.cpp are MIT licensed; Qwen2.5 1.5B is Apache-2.0; eSpeak NG is GPL-3.0-or-later. Their upstream license requirements still apply if a packaged product is later distributed.

Input is at most 1,200 characters or 30 seconds of mono, 16 kHz, signed 16-bit PCM WAV. Near-zero audio is rejected before transcription; this is not a full voice activity detector. Context is 2,048 tokens. Output defaults to 128 model tokens, bounded to a maximum of 384, and 4,000 characters. A model response that exhausts its token allowance is discarded instead of speaking a partial answer. Sampling uses temperature 0 and seed 42. Each turn supplies only the fixed system prompt and the current utterance; there is no retrieval or saved conversation.

Deadlines are per stage: model-server startup 120 seconds, transcription 60 seconds, answer 120 seconds, synthesis 30 seconds, and playback 120 seconds. They are protective caps, not desired response times or measured Jetson performance. A model can still give incorrect answers.

The default system prompt is versioned in `local_voice/core.py`. To customize it, put a local UTF-8 prompt in a file outside the repository and use `--system-prompt-file` before `ask` or `device`; the service generator accepts the same option. Prompt files are limited to 1,200 characters. Changing the prompt creates a different evaluation condition and does not inherit the default prompt's smoke observations.

## Use the existing local VM

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
python3 -m local_voice doctor --verify-hashes
python3 -m unittest discover -s tests -v
bash scripts/offline_check.sh
python3 scripts/runtime_check.py
python3 scripts/service_check.py
```

The regression runner should end with `Ran 38 tests` and `OK`. The smoke and runtime/service scripts must exit with status 0 and report `"status": "passed"`. The smoke report must list only `lo` under `network_interfaces`. A passing `doctor` checks assets/executables, not real microphone, speaker, or GPU operation. Firmware compilation is a separate command in the button section.

`vm.yaml` pins the Ubuntu image and checksum used for the observed run. If Ubuntu retires that snapshot URL, deliberately select and record a replacement image/digest; do not silently call it the same environment. Apt security updates can change package versions; the observed versions are recorded with results.

Online setup downloads two source trees and approximately 1.2 GB of model files. It builds CPU runtimes on ARM64 and verifies the weights before installing them. Setup uses the network; application inference does not invoke the setup code. Re-running setup reuses verified model files and the pinned source/build trees.

`offline_check.sh` creates a new network namespace for the test process tree, brings up only loopback, and runs inference as the invoking non-root user. It does not disable the whole VM's network. `service_check.py` uses `sudo` to create one temporary system service, checks it, and removes it; it deliberately uses a nonexistent capture device and a pseudo terminal, so no person is recorded.

## Deploy to the actual Jetson

**Prerequisite:** complete board/firmware/storage setup using the official installation instructions for the chosen JetPack release. This application does not flash the board or prepare the SD card. The Linux VM baseline is Ubuntu 22.04; JetPack 6.2.1 is a corresponding candidate, not a confirmed installation on the future device. Record the actual release before building.

For that candidate, follow [NVIDIA's JetPack 6.2.1 installation guide](https://docs.nvidia.com/jetson/jetpack/6.2.1/install-setup/index.html), including its firmware check before a JetPack 6.x SD-card boot. Its SDK Manager route requires a supported Ubuntu x64 host; this ARM64 application-test VM is not that flashing host. Resolve the board's installation method first, then use the steps below to install the application onto its running Linux system.

1. Put the Jetson and Mac on the local network, enable SSH during device setup, and copy this directory using `scp`/`rsync`. Do not copy the Mac's Python environment or the VM's build symlinks. The placeholder destination below must be replaced with your Jetson account and address; keep real connection details out of Git.

   ```bash
   scp -r ./jetson USERNAME@JETSON_ADDRESS:~/voice-app
   ```

   Run that transfer from the parent `software/` directory, then open an SSH session using your device's account and address. The following commands run **on Jetson**.

2. Build and test a CPU baseline directly on the target:

   ```bash
   cd ~/voice-app
   bash scripts/install_linux_deps.sh
   python3 scripts/setup_runtime.py --backend cpu
   python3 -m local_voice doctor --verify-hashes --audio
   python3 -m local_voice ask --text 'Name a primary color.' --show-text
   ```

3. Build the optional GPU profile only after the JetPack CUDA toolkit is installed and `nvcc` is available:

   ```bash
   python3 scripts/setup_runtime.py --backend cuda --jobs 4
   python3 -m local_voice --backend cuda doctor --verify-hashes --audio
   python3 -m local_voice --backend cuda ask --text 'Name a primary color.' --show-text
   ```

   The CUDA profile builds separately with architecture 87 and explicitly selects `CUDA0` for the answer server. A missing CUDA device must fail instead of silently presenting a CPU run as a GPU result. CUDA compilation, library compatibility, offload, and memory remain untested; inspect actual runtime/device evidence on the board before treating this profile as accepted.

4. Identify the USB audio devices using `arecord -l` and `aplay -l`. Qualify capture/playback separately, then run the keyboard-controlled loop:

   ```bash
   python3 -m local_voice device --keyboard
   ```

   Enter starts recording; Enter again ends it and speaks the answer. Enter while busy cancels. `c` cancels explicitly; `q` quits. To select hardware, put `--capture-device` and `--playback-device` **before** `device`, using the ALSA names observed on your board. A `plughw:` device can perform sample-format conversion when the USB microphone's native rate differs. Missing/denied devices produce a visible error and allow retry.

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

   Replace `DEVICE` with the observed serial identifier. Add `--backend cuda` and the tested audio-device options to the generator only after those paths pass manual checks. Run the generator as the normal application user; it records that user and the local application/runtime locations in the generated machine-local file. Do not commit that generated file.

   The system service grants the `audio` and `dialout` supplementary groups, runs inference as the selected non-root user, isolates external networking, mounts a private 16 MiB tmpfs for transient audio, and terminates the whole process group when stopping. Journal entries contain states and sanitized errors, not utterances. Disable it with `sudo systemctl disable --now longtail-voice.service`. Leave boot autostart disabled until physical testing passes.

Application updates are another source transfer and service restart; routine code changes do not require reflashing the SanDisk card. Preserve a known-working local copy before an update and rerun the on-device checks.

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

Flash later from a machine with the physical board attached using PlatformIO's `run --target upload --upload-port` and the observed device path. The Lima VM has no USB passthrough configured; the firmware was compiled there, not flashed. Native Mac PlatformIO or the Jetson can perform the later upload. Never flash an unidentified serial device.

Protocol is 115200 baud, newline-terminated ASCII. Button sends `PRESS`; application accepts `CANCEL` for integration tools too. Application sends `STATE ready|recording|finishing|transcribing|answering|synthesizing|speaking|cancelling|error` and repeats its current state once per second. Duplicate presses within 200 ms are ignored by the host. LED: green ready, red recording, amber processing/cancelling, cyan speaking, magenta error, dim white waiting/disconnected. A five-second missing heartbeat resets the LED to waiting.

## Retention and measurement boundaries

Normal completion, ordinary errors, and cancellation delete temporary recording/transcript/speech files. The service's private tmpfs also disappears when the service exits. Standalone CLI files in `/dev/shm` can survive an uncatchable process kill until cleanup or reboot; no forensic-erasure guarantee is made. The selected OS controls swap and crash behavior. Explicitly exported WAVs and `--show-text` output are intentionally retained/displayed by the caller.

VM tests establish native ARM64 Linux integration, local inference, bounded failure handling, and service behavior. They do not establish Jetson bootability, CUDA compatibility, acoustic quality, latency, power draw, thermals, long-session stability, or final model usefulness. Run the physical-device acceptance checklist in the validation record before deployment is called complete.
