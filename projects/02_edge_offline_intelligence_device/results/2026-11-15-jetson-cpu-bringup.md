# Physical Jetson CPU bring-up

**Date:** November 15, 2026 (operator date; the device clock was incorrect).
**Status:** Existing CPU installation passes readiness, regression, authored inference, and owner-confirmed USB speaker checks. Live microphone interaction remains pending.

## Environment and provenance

- Orin Nano Super developer kit; Ubuntu 22.04.5 LTS, aarch64, NVIDIA L4T R36.4.4.
- Approximately 7.4 GiB reported RAM and 91 GiB free on the root microSD filesystem at inspection.
- Existing application and user-local runtime installation reused; no new runtime build or model download performed. A checksum-based transfer comparison matched the existing Python source to the repository. A desktop audio-selection launcher was subsequently added and deployed.
- Qwen2.5 1.5B Instruct Q4_K_M and Whisper tiny.en model SHA-256 checks match the versioned runtime lock.
- llama-server reports pinned commit `930e2fa`; full binary/build provenance of the pre-existing runtime installation was not independently reconstructed.
- USB PnP Sound Device capture and UACDemoV1.0 playback devices enumerated. No physical button was enumerated in the inspected USB inventory.

## Observed checks

| Check | Result | Boundary |
| --- | --- | --- |
| Readiness with both model hashes and audio tools | Passed | User-local executable directory must be in PATH |
| Regression suite | 38 tests passed | Controlled cases, not long-session reliability |
| Authored typed question | Returned a primary-color answer and synthesized speech | CPU smoke check, no comparative quality claim |
| Authored synthetic audio | Transcribed the France-capital question exactly; answered Paris and synthesized speech | eSpeak source converted to mono 16 kHz PCM using Python audioop; not human microphone input |
| USB speaker playback | Application completed playback; owner confirmed hearing the test sentence | One short listening check |
| Temporary synthetic fixtures | Removed at completion | No personal microphone recording collected for these checks |

The synthetic-audio trial reported 1.640 s transcription, 9.279 s answer, and 0.032 s synthesis. These are a single physical-device CPU smoke observation, not latency distributions, total interaction time, or VM-comparable benchmark results.

## Configuration findings

The desktop sound server and direct ALSA device access conflicted: direct speaker playback returned device-busy. Selecting the USB microphone/speaker as PulseAudio defaults and using `--capture-device pulse --playback-device pulse` allowed application playback. However, the defaults later reverted to the onboard interface, and the owner's first live test returned the explicit silence rejection. The new `scripts/desktop_device.sh` selects the single USB source/sink through process-local PulseAudio environment variables, fails on ambiguous selection, and reached the ready state on-device. Live retesting is pending. This is a signed-in desktop-session path, not proof that the headless system service can access PulseAudio.

The existing eSpeak wrapper is user-local and was absent from the noninteractive SSH PATH. Adding the user-local executable directory to that session's PATH resolved readiness. The model and speech wrappers already existed; this session did not install or rebuild them.

## Remaining acceptance

- Complete and confirm the live microphone-to-spoken-answer loop, repeated turns, and cancellation.
- Reproduce runtime builds on the board and validate CUDA separately; installed toolkit files alone do not establish GPU execution.
- Correct device time and establish target internet access before online setup. The USB link to a Mac is not automatically internet sharing.
- Qualify physical button firmware, headless audio/service operation, reboot behavior, and then autostart.
- Run a defined network-isolation check on the Jetson. The prior VM isolation result does not transfer to this device.
- Evaluate human speech accuracy, voice quality, thermal/power behavior, and simultaneous memory headroom. Zero published comparative quality or performance measurements remain.
