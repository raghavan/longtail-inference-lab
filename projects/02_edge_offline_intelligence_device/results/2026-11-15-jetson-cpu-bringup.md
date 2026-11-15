# Physical Jetson CPU bring-up

**Date:** November 15, 2026 (operator date; the device clock was incorrect).
**Status:** Existing CPU installation passes readiness, regression, authored inference, and owner-confirmed USB speaker checks. The owner confirmed a live microphone-to-spoken-answer turn after explicit USB selection.

## Environment and provenance

- Orin Nano Super developer kit; Ubuntu 22.04.5 LTS, aarch64, NVIDIA L4T R36.4.4.
- Approximately 7.4 GiB reported RAM and 91 GiB free on the root microSD filesystem at inspection.
- Existing application and user-local runtime installation reused; no new runtime build or model download performed. A checksum-based transfer comparison matched the existing Python source to the repository. A desktop audio-selection launcher was subsequently added and deployed.
- Qwen2.5 1.5B Instruct Q4_K_M and Whisper tiny.en model SHA-256 checks match the versioned runtime lock.
- llama-server reports pinned commit `930e2fa`; full binary/build provenance of the pre-existing runtime installation was not independently reconstructed.
- USB PnP Sound Device capture and UACDemoV1.0 playback devices enumerated. The AtomS3-Lite was subsequently connected, identified, flashed, and tested as described below.

## Observed checks

| Check | Result | Boundary |
| --- | --- | --- |
| Readiness with both model hashes and audio tools | Passed | User-local executable directory must be in PATH |
| Regression suite | 38 tests passed | Controlled cases, not long-session reliability |
| Authored typed question | Returned a primary-color answer and synthesized speech | CPU smoke check, no comparative quality claim |
| Authored synthetic audio | Transcribed the France-capital question exactly; answered Paris and synthesized speech | eSpeak source converted to mono 16 kHz PCM using Python audioop; not human microphone input |
| USB speaker playback | Application completed playback; owner confirmed hearing the test sentence | One short listening check |
| Live microphone-to-answer loop | Owner confirmed an answer was spoken after using the explicit USB launcher | One turn, no private audio or transcript collected in this record |
| Temporary synthetic fixtures | Removed at completion | No personal microphone recording collected for these checks |

The synthetic-audio trial reported 1.640 s transcription, 9.279 s answer, and 0.032 s synthesis. These are a single physical-device CPU smoke observation, not latency distributions, total interaction time, or VM-comparable benchmark results.

## Configuration findings

The desktop sound server and direct ALSA device access conflicted: direct speaker playback returned device-busy. Selecting the USB microphone/speaker as PulseAudio defaults and using `--capture-device pulse --playback-device pulse` allowed application playback. However, the defaults later reverted to the onboard interface, and the owner's first live test returned the explicit silence rejection. The new `scripts/desktop_device.sh` selects the single USB source/sink through process-local PulseAudio environment variables, fails on ambiguous selection, and reached the ready state on-device. The owner then confirmed a spoken answer from a live microphone turn. This is a signed-in desktop-session path, not proof that the headless system service can access PulseAudio.

The existing eSpeak wrapper is user-local and was absent from the noninteractive SSH PATH. Adding the user-local executable directory to that session's PATH resolved readiness. The model and speech wrappers already existed; this session did not install or rebuild them.

## Remaining acceptance

- Qualify repeated live turns and cancellation beyond the one owner-confirmed microphone-to-spoken-answer turn.
- Reproduce runtime builds on the board and validate CUDA separately; installed toolkit files alone do not establish GPU execution.
- Correct device time and establish target internet access before online setup. The USB link to a Mac is not automatically internet sharing.
- Extend button reconnect, repeated boot-cycle, and headless stability testing beyond the successful initial smoke checks.
- Extend offline reliability testing beyond the observed Jetson service namespace containing only loopback. This physical evidence is distinct from the prior VM isolation check.
- Evaluate human speech accuracy, voice quality, thermal/power behavior, and simultaneous memory headroom. Zero published comparative quality or performance measurements remain.

After the successful live turn, the owner reported low speaker volume. The USB speaker output was raised from 30% to 70% and the configured level was read back; listening comfort at the new level remains user-assessed.

## Physical-button standalone continuation

The identified AtomS3-Lite ESP32-S3 was flashed with the existing firmware after privately backing up the application region that would be overwritten. All flashed-region hashes verified. The owner observed LED changes, and the application received start/finish events. Firmware source was unchanged. Firmware image SHA-256: `770da8ffac4bb28c991418566c4f4d7f429466d893309442f0ff6a6b19bbf85e`.

Direct ALSA capture exposed a real stop-path defect: on SIGINT the USB driver returned EINTR and arecord left a 30-second WAV header over a shorter recording. A controlled two-second check showed 480,000 frames declared but only 60,000 audio bytes present. The application correctly rejected the truncated file. Capture now writes bounded raw PCM and constructs its own WAV after the subprocess stops; cancellation still discards temporary data. The paced subprocess regression now reproduces the nonzero EINTR-style stop exit and checks PCM cleanup. All 38 tests passed on the Jetson after the change. The owner confirmed the manual button-to-spoken-answer retest passed; the owner also confirmed a spoken answer from the installed system service.

The generated system service was installed and reached ready with zero restarts. Both USB sound cards report `PULSE_IGNORE=1`, reserving them for direct ALSA access. The service runs as the application user with audio/dialout groups, read-only home/system mounts, transient audio storage, and a network namespace observed to contain only loopback. Its machine-local PATH includes the pre-existing user-local speech wrapper. Boot startup was then enabled. A changed boot identity confirmed an actual reboot; the service was enabled, active, and ready with zero restarts, preserved 70% mixer volume, and only loopback in its network namespace. Laptop-disconnected listening confirmation remains pending.
