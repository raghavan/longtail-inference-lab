#!/usr/bin/env bash
set -euo pipefail
# Linux only. Create a network namespace for this command tree, not the whole VM.
# Preserve the invoking user's identity; do not run inference as root.
test "$(uname -s)" = Linux || { echo 'Run inside Linux.' >&2; exit 1; }
task_user=$(id -un)
task_dir=$(cd -- "$(dirname -- "$0")/.." && pwd)
sudo unshare --net -- bash -c '
  set -euo pipefail
  ip link set lo up
  exec runuser -u "$1" -- sh -c '\''cd "$1"; shift; exec python3 scripts/smoke.py --require-isolated-network "$@"'\'' sh "$2" "${@:3}"
' bash "$task_user" "$task_dir" "$@"
