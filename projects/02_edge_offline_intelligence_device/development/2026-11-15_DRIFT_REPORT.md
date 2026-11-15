## Desktop audio launcher contract (software/jetson/README.md)

No drift detected in the scoped desktop-launcher change. The launcher delegates to the existing single-turn keyboard controller, selects USB audio through inherited process-local PulseAudio settings, and adds no inference, retention, or service behavior. Checked against the Linux intake, CLI, capture/playback implementation, and on-device ready-state result. This is a scoped implementation consistency check, not a fresh-context design review or completion of physical acceptance.
