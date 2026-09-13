#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

case "${1:-simulator}" in
  simulator)
    xcodebuild -project iOS/LocalVoice.xcodeproj -scheme LocalVoice \
      -destination 'generic/platform=iOS Simulator' \
      -derivedDataPath build/ios CODE_SIGNING_ALLOWED=NO build
    ;;
  archive)
    xcodebuild -project iOS/LocalVoice.xcodeproj -scheme LocalVoice \
      -configuration Release -destination 'generic/platform=iOS' \
      -archivePath build/ios/LocalVoice.xcarchive \
      -derivedDataPath build/ios-device -allowProvisioningUpdates archive
    ;;
  *)
    printf 'Usage: %s [simulator|archive]\n' "$0" >&2
    exit 2
    ;;
esac
