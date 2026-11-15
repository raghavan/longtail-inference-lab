#!/usr/bin/env bash
# Signed-in Linux desktop only; the headless service has a separate audio path.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
command -v pactl >/dev/null || { echo 'PulseAudio tools are required.' >&2; exit 1; }

# Select USB hardware explicitly: desktop defaults can change between sessions.
# Multiple devices require an explicit PULSE_SOURCE or PULSE_SINK selection.
sources=$(pactl list short sources)
sinks=$(pactl list short sinks)
if [[ -z ${PULSE_SOURCE:-} ]]; then
  mapfile -t candidates < <(awk '$2 ~ /^alsa_input\.usb-/ {print $2}' <<< "$sources")
  [[ ${#candidates[@]} == 1 ]] || { echo 'Select one USB microphone using PULSE_SOURCE.' >&2; exit 1; }
  export PULSE_SOURCE=${candidates[0]}
fi
if [[ -z ${PULSE_SINK:-} ]]; then
  mapfile -t candidates < <(awk '$2 ~ /^alsa_output\.usb-/ {print $2}' <<< "$sinks")
  [[ ${#candidates[@]} == 1 ]] || { echo 'Select one USB speaker using PULSE_SINK.' >&2; exit 1; }
  export PULSE_SINK=${candidates[0]}
fi
cd -- "$(dirname -- "$0")/.."
exec python3 -m local_voice --capture-device pulse --playback-device pulse device --keyboard
