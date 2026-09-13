#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
swift build -c release --product LocalVoice
binary_dir="$(swift build -c release --show-bin-path)"
bundle_dir="$PWD/build/Local Voice.app"
mkdir -p "$bundle_dir/Contents/MacOS"
cp "$binary_dir/LocalVoice" "$bundle_dir/Contents/MacOS/LocalVoice"
cp macOS/Info.plist "$bundle_dir/Contents/Info.plist"
codesign --force --sign - --entitlements macOS/LocalVoice.entitlements "$bundle_dir"
printf '%s\n' "$bundle_dir"
