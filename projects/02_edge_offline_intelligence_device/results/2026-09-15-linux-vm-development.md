# Linux ARM64 voice application development checks

**Date:** September 15, 2026
**Status:** Linux ARM64 development slice passed. Physical Jetson acceptance remains open.
**Question:** Does the portable voice application build and execute locally in Linux ARM64, with bounded failure behavior and no external network during the inference check?

This record answers the [development intake](../development/jetson_linux_intake.md). It does not complete the platform quality/performance experiment or establish a Jetson measurement. Zero published comparative quality or performance measurements remain for Mac, iPhone, and Jetson.

## Observed environment

| Item | Observed configuration |
| --- | --- |
| VM host class | Apple silicon M2 Pro, 16 GB host memory |
| Virtualization | Lima 2.2.0, Apple Virtualization framework, native aarch64 |
| Guest | Ubuntu 22.04 ARM64, Linux 5.15.0-185-generic |
| Allocation | 4 virtual CPUs, 6 GiB configured RAM, 24 GiB sparse disk; no host-directory mounts |
| Python | 3.10.12 |
| Build | GCC 11.4.0; CMake 3.22.1; CPU backend; GGML_NATIVE=OFF |
| Speech | eSpeak NG 1.50+dfsg-10ubuntu0.1, en-us, 165 words/minute |
| Test audio | eSpeak NG en-us at 145 words/minute, converted to mono 16 kHz PCM with FFmpeg 4.4.2 |
| Answer runtime | llama.cpp commit `930e2fa5995789efbf249a8bf61325bb626e417b` |
| Transcription runtime | whisper.cpp commit `da54572229bcf64ba367d96c7ef15770376c4280` |
| Model identities | Qwen2.5 1.5B Instruct Q4_K_M and Whisper tiny.en F16; exact revisions and hashes in [runtime lock](../software/jetson/runtime-lock.json) |
| Answer policy | Fixed prompt in `local_voice/core.py`; current utterance only, no history or retrieval; context 2,048 tokens, output 128 tokens, temperature 0, seed 42 |

The Ubuntu image and checksum are recorded in [vm.yaml](../software/jetson/vm.yaml). No hardware purchases or paid inference services were used.

## Checks and results

| Check | Observed outcome | Limit |
| --- | --- | --- |
| Native Linux builds | llama-server and whisper-cli built from pinned commits | CPU only; no Jetson CUDA compilation |
| Model integrity | Both exact SHA-256 checks passed | Artifact identity, not quality |
| Automated regressions | 38 tests passed in approximately five seconds | Controlled cases; not a long-duration reliability test |
| Real offline pipeline | One typed and two synthetic-audio trials completed | Simple authored inputs only |
| Network exclusion | Test process tree had only loopback in its network namespace | Whole VM/host remained online for setup and unrelated activity |
| Missing runtime, oversized input, silence, output exhaustion | Actual CLI returned explicit errors | Near-zero threshold is not a complete voice activity detector |
| Actual cancellation | CLI returned cancellation, printed no partial result, and reaped its model process | Real cancellation during observed server startup; fixtures separately cover in-flight HTTP and playback |
| Service startup | Generated system unit verified and ran as non-root | Virtual serial device only |
| Service isolation | Loopback only; real text/answer/speech-file inference completed in the sandbox | Hardware and GPU access untested |
| Device failure recovery | Two virtual presses each produced sanitized missing-microphone errors; service remained usable | Intentionally nonexistent capture device |
| Service shutdown | Main process stopped; temporary service removed | No persistent VM autostart service left installed |
| Audio retention | Normal, failed, and cancelled turns cleaned temporary files | Explicit export and standalone hard-kill limits documented |
| Python package | Built/installed in a clean VM venv; installed CLI verified models outside the source directory | Service deliberately runs source with system Python |
| AtomS3-Lite firmware | ESP32-S3 build succeeded in Linux | Not flashed or exercised on hardware |

Regression coverage includes malformed/truncated/oversized WAVs, text and settings limits, silence, exclusive input modes, output overwrite protection, private permissions, cleanup, repeated turns, recording/answer/playback cancellation, late-result suppression, process-group cleanup, missing ALSA devices, null playback, fragmented serial messages, debouncing, oversized frames, HTTP proxy bypass, redirects, malformed/partial model responses, timeout recovery, and service generation.

## Real inference observations

The first trial starts a new answer server. Audio trials reuse it with fresh single-turn messages; Whisper starts per audio trial. Wall-clock times exclude setup/downloads, physical recording, and speaker playback.

| Trial | Input | Observed answer | Transcription | Answer | Synthesis | Total |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Typed, server cold | Name two things to pack for a short walk. | Water and sunscreen. | N/A | 1.898 s | 0.032 s | 1.930 s |
| Synthetic speech, server warm | What is the capital of France? | The capital of France is Paris. | 0.546 s | 1.400 s | 0.033 s | 1.979 s |
| Same synthetic speech, repeat | What is the capital of France? | The capital of France is Paris. | 0.550 s | 1.400 s | 0.034 s | 1.984 s |

Both audio trials transcribed the authored question exactly. Input duration was 2.221 seconds; synthesized answer duration was 2.087 seconds. This deliberately easy synthetic case is not a human-speech accuracy estimate. Three trials support neither percentiles nor model rankings.

The largest reaped child peak RSS was **1,221,800 KiB**, about **1.17 GiB**. This is not simultaneous pipeline memory, total VM memory, CUDA memory, or Jetson RAM usage. The actual cancellation check recorded 0.009 seconds from signal to observed exit in that run; no cancellation-latency guarantee follows.

Evidence contains authored examples and sanitized technical values:

- [Offline smoke trials](linux_vm_2026-09-15/offline-smoke.json)
- [Actual CLI failure/cancellation checks](linux_vm_2026-09-15/runtime-check.json)
- [Service and virtual serial checks](linux_vm_2026-09-15/service-check.json)
- [Validated source hashes and test count](linux_vm_2026-09-15/source-validation.json)

Raw build logs and generated machine-specific units stay in the VM's ignored local results directory. Model weights, third-party source trees, virtual disks, and firmware build outputs are not repository content.

## Failures found and repaired

1. The first offline harness inspected `/sys/class/net`, which retained the parent namespace view and incorrectly rejected isolation. It now queries `socket.if_nameindex()` in the current namespace. Real loopback-only model checks subsequently passed; the failed harness attempt is not counted as a successful trial.
2. A cancellation test assumed ALSA null capture progressed at recording speed. It completed immediately, so cancellation was not exercised. A paced external capture fixture now verifies stop/finalization and cancellation; real ALSA missing-device/null-playback checks are separate. No physical capture conclusion follows.
3. Live `systemd-analyze verify` rejected quoted `WorkingDirectory=` syntax. The generator now uses the correct setting syntax and retains argument quoting for `ExecStart`. The corrected service was started and exercised with real inference.
4. A later service isolation check found the private audio tmpfs was not writable by the non-root service account. Explicit mode 1777 restores normal temporary-directory access while each operation retains its private 0700 directory; the service was retested after the correction.
5. The privacy scan flagged an illustrative SSH command despite placeholder values. The connection step is now explained in prose. No private connection value entered source.
6. Code review identified blocking stdin reads that could postpone signal cancellation until EOF. A selectable bounded reader replaced them; both pipe regressions and the actual CLI now verify cancellation while stdin remains open. Keyboard commands use the same non-blocking approach.

## Operational conclusion

**Supported:** Continue with this application for on-board integration. Its CPU stack works in ARM64 Linux, actual inference works without external networking, and the service/button protocol has executable development evidence.

**Not supported:** Calling Jetson deployed, CUDA compatible in practice, acoustically usable, natural sounding, or within an on-board resource envelope. The answer model is an implementation candidate, not a comparative winner. eSpeak is a robotic development voice; listening checks and a better local voice may be needed.

## Physical acceptance still required

1. Record actual board, firmware, JetPack, storage, runtime build, and power mode; verify boot/shutdown from the SanDisk card.
2. Rebuild the CPU profile on-board, verify hashes, and repeat authored text/audio checks.
3. Build CUDA against the matching JetPack toolkit, verify GPU execution and libraries, and measure simultaneous memory headroom.
4. Flash the identified AtomS3-Lite; verify USB reconnect, press/debounce, heartbeat, and LED states.
5. Select USB microphone/speaker ALSA devices; verify capture and audible playback, then the complete button-to-spoken-answer loop.
6. Agree on human-speech, usefulness, voice-quality, and waiting-time gates. Test noise, cancellations, device removal, long sessions, memory pressure, thermals, and external-network disconnection.
7. Enable boot autostart only after manual checks pass; reboot and repeat. Screen, battery, enclosure, and additional languages remain deferred.

Commands are in the [Linux application guide](../software/jetson/README.md).
