# Local Voice for macOS

**Status:** Native development app, version 0.1.1 (build 2). Real local answer and synthetic speech checks passed; the owner confirmed live voice input and visible text answers. Zero published comparative quality or performance measurements for Mac, iPhone, or Jetson.

Speak one question, see its transcript, and read a locally generated text answer. The app also accepts typed input so recognition errors can be corrected. The current prototype uses Apple's on-device `SystemLanguageModel.default` and `SpeechTranscriber`; it has no web, document, or vector retrieval, conversation history, voice playback, or app-owned recording/transcript persistence.

## Requirements and setup

- Apple silicon Mac running macOS 26 or later, with a compatible Xcode installation and Swift 6.
- Apple Intelligence enabled and its on-device model available. The app shows readiness and unavailable states.
- English (United States) speech assets. **Prepare local speech** downloads them if needed; initial setup may require internet.
- Microphone permission for Local Voice when recording.

From the repository root:

```bash
cd projects/02_edge_offline_intelligence_device/software/apple
./build-macos.sh
open "build/Local Voice.app"
```

The script creates an ad hoc signed local app bundle. This is a development build, not a notarized distribution or TestFlight upload. Build products and caches are ignored by Git. No external package dependencies or separately bundled model weights are required for this Apple backend.

Use **Record**, then **Stop and answer**. **Cancel** stops the active operation; **Clear** resets the visible text. Recording ends automatically after 30 seconds. Input is limited to 1,200 characters and generated output to 384 model tokens. Typed generation has a 60-second cancellation deadline; the complete recording workflow has a 90-second deadline. Framework cancellation is cooperative. Each question creates a fresh answer session.

## Development checks

From the `software/apple` directory:

```bash
swift test
swift run LocalVoiceCheck --readiness
swift run LocalVoiceCheck --check-answer
```

If speech assets need setup, use the app's preparation button or:

```bash
swift run LocalVoiceCheck --prepare-speech
```

To exercise an authored synthetic audio file without microphone capture:

```bash
say -v Samantha -r 155 -o /tmp/longtail-synthetic-voice.aiff \
  'Explain why leaves change color in autumn.'
swift run LocalVoiceCheck --check-voice /tmp/longtail-synthetic-voice.aiff
```

The command prints the fixture's transcript and answer. Use deliberately authored test material for shared logs. `--transcribe AUDIO_FILE` also exists for local debugging; its output may be private and must not be published without permission.

The seven automated tests cover input bounds, unavailable models, streamed state, stale results after cancellation, final-transcript handoff, recoverable errors, and the actual audio callback on a background executor. The callback test also checks conversion and buffer ownership. Fake-backend tests do not measure model quality. An audio-file smoke check bypasses microphone capture; it cannot establish recording usability.

App inference and speech services need normal local framework access. A restricted development-tool sandbox may deny that access even when the desktop app works. Report such a failure separately from a model failure; do not add a cloud fallback to work around it.

## Code and next platform gate

[`apple/Package.swift`](apple/Package.swift) defines the reusable `LocalVoiceCore`, SwiftUI app, command-line checks, and tests. The answer and speech interfaces keep providers replaceable. The nonisolated, sendable audio callback converts hardware buffers before the asynchronous analyzer consumes them; UI state stays on the main actor.

The [development record](../development/README.md) scopes this Mac slice, and [current status](../status.md) records its checks and known limits. The target iPhone/OS and requested languages are still needed before phone-specific model selection. Shared Swift source and declared iOS availability are not a signed iOS application or proof of physical-device compatibility.

If an embedded open model is needed, freeze the same model artifact, quantization, prompt policy, and context budget for Mac and iPhone, then measure the actual phone. Jetson needs a separate local backend. Follow the [architecture](../design_direction.md), [model-selection intake](../../../resources/project_proposals/apple_local_voice_intake.md), and [results policy](../results/README.md) before expanding scope or claiming performance.
