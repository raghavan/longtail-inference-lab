#!/usr/bin/env bash
set -euo pipefail
# Run only inside the VM or on the target Jetson. Does not install/replace CUDA.
test "$(uname -s)" = Linux || { echo 'This script requires Linux.' >&2; exit 1; }
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  build-essential cmake git ca-certificates libcurl4-openssl-dev \
  python3 python3-venv python3-pip espeak-ng alsa-utils ffmpeg
