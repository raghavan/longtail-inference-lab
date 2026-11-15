## Desktop audio launcher contract (software/jetson/README.md)

No drift detected in the scoped desktop-launcher change. The launcher delegates to the existing single-turn keyboard controller, selects USB audio through inherited process-local PulseAudio settings, and adds no inference, retention, or service behavior. Checked against the Linux intake, CLI, capture/playback implementation, and on-device ready-state result. This is a scoped implementation consistency check, not a fresh-context design review or completion of physical acceptance.

## Linux intake and capture contract — direct ALSA stop fix

No drift detected in the scoped raw-PCM framing fix. Mono 16 kHz signed 16-bit capture, the 30-second cap, silence rejection, cancellation, and transient-file cleanup remain enforced. Direct driver interruption is reproduced by the updated subprocess regression. Hardware and headless acceptance remain separately recorded.

## Standalone system-service deployment

No drift detected in the scoped service deployment: the existing generator's non-root identity, audio/dialout groups, private network, read-only mounts, and transient-audio storage are retained. Machine-local configuration adds the user-local speech executable path, reserves USB audio from PulseAudio, and permits five-second restart retries without a burst lockout when the button is absent. The deployment guide records these settings. System-service inference and post-reboot readiness were observed; broader reliability remains unqualified.
