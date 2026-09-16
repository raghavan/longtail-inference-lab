#!/usr/bin/env bash
set -euo pipefail
# Local-only VM lifecycle helper. No host filesystem is mounted in the guest.
task_dir=$(cd -- "$(dirname -- "$0")/.." && pwd)
instance=longtail-jetson
case "${1:-help}" in
  create)
    command -v limactl >/dev/null || { echo 'Install Lima: brew install lima'; exit 1; }
    limactl start --name="$instance" --tty=false "$task_dir/vm.yaml"
    ;;
  sync)
    limactl shell --workdir=/ "$instance" sh -c 'mkdir -p ~/voice-app'
    COPYFILE_DISABLE=1 tar --no-xattrs -C "$task_dir" --exclude=__pycache__ --exclude=.local-results \
      --exclude=.runtime --exclude=.venv --exclude=.pio --exclude=models \
      --exclude=build --exclude=dist --exclude='*.egg-info' -cf - . |
      limactl shell --workdir=/ "$instance" sh -c 'cd ~/voice-app && tar -xf -'
    ;;
  test)
    limactl shell --workdir=/ "$instance" sh -c 'cd ~/voice-app && python3 -m unittest discover -s tests -v'
    ;;
  smoke)
    limactl shell --workdir=/ "$instance" sh -c 'cd ~/voice-app && bash scripts/offline_check.sh'
    ;;
  shell) limactl shell --workdir=/ "$instance" ;;
  stop) limactl stop "$instance" ;;
  *) echo 'Usage: bash scripts/vm.sh create|sync|test|smoke|shell|stop' ;;
esac
