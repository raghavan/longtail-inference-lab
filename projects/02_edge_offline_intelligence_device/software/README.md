# Local Voice for macOS and iPhone

**Status:** The Mac development app is version 0.2.0 (build 4). The native iPhone beta is **Local Voice Lab 0.3.0 (build 5)** in TestFlight, Ready to Test in the internal owner group, with the owner Invited. The installed app remains **Local Voice**. Simulator typed-answer and manual read-aloud checks passed; physical iPhone installation and evaluation remain unverified. The owner confirmed the Mac voice-input, text-answer, and read-aloud flow. Zero published comparative quality or performance measurements for Mac, iPhone, or Jetson.

Speak one question, see its transcript, and read a locally generated text answer, or press **Read aloud** to hear it. The app also accepts typed input so recognition errors can be corrected. The current prototype uses Apple's on-device `SystemLanguageModel.default`, `SpeechTranscriber`, and installed English `AVSpeechSynthesizer` voices. It has no web, document, or vector retrieval, conversation history, or app-owned recording/transcript persistence. English is the current scope; additional languages are deferred.

## Mac requirements and setup

- Apple silicon Mac running macOS 26 or later, with a compatible Xcode installation and Swift 6.
- Apple Intelligence enabled and its on-device model available. The app shows readiness and unavailable states.
- English (United States) speech assets. **Prepare local speech** downloads them if needed; initial setup may require internet.
- Microphone permission for Local Voice when recording.
- An installed Apple English speaking voice. Standard voices work; Enhanced or Premium voices require a one-time download in system settings. No paid speech subscription is needed.

From the repository root:

```bash
cd projects/02_edge_offline_intelligence_device/software/apple
./build-macos.sh
open "build/Local Voice.app"
```

The script creates an ad hoc signed local app bundle. This is a development build, not a notarized distribution or TestFlight upload. Build products and caches are ignored by Git. No external package dependencies or separately bundled model weights are required for this Apple backend.

Use **Record**, then **Stop and answer**. **Cancel** stops the active operation; **Clear** resets the visible text. Recording ends automatically after 30 seconds. Input is limited to 1,200 characters and generated output to 384 model tokens. Typed generation has a 60-second cancellation deadline; the complete recording workflow has a 90-second deadline. Framework cancellation is cooperative. Each question creates a fresh answer session.

Press **Read aloud** after an answer completes. **Stop speaking** stops playback and preserves the answer. Recording, answering, changing voice, clearing, and cancellation stop speech. Answers never autoplay. Playback is bounded to 4,000 characters and 120 seconds.

Expand **Voice** to choose among installed English voices or use **Automatic**, which prefers Premium, then Enhanced, then Standard quality. **Preview voice** reads an authored sample without calling the answer model. The app saves only the chosen voice identifier as a preference. It refreshes available voices when it becomes active; **Refresh voices** also reloads the list. The displayed voice is the one used for the next utterance.

For a higher-quality voice on macOS 26, open System Settings → Accessibility → Read & Speak → the information button beside System voice → English. Download an Enhanced or Premium voice, then refresh the app. On iOS 26 the route is Settings → Accessibility → Read & Speak → Voices → English. The named voice and storage size may differ by device. On the development Mac, Ava Premium was offered as a 280.2 MB download and displayed 323 MB installed. This is system voice storage, not app size or peak RAM. The Premium label is Apple’s quality tier; listening quality still needs evaluation.

## Development checks

From the `software/apple` directory:

```bash
swift test
swift run LocalVoiceCheck --readiness
swift run LocalVoiceCheck --check-answer
swift run LocalVoiceCheck --check-tts
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

The seventeen automated tests cover input bounds, unavailable models, streamed state, stale results after cancellation, final-transcript handoff, recoverable errors, manual playback, stop before recording, stale playback callbacks, clearing, missing voices, voice changes, removed assets, quality selection, audio interruptions, and the actual audio callback on a background executor. Interruption tests check that playback stops while preserving completed text and that cancelled partial/late output is discarded. The callback test also checks conversion and buffer ownership. The text-to-audio check uses an authored sentence and requires non-silent samples plus a completion marker; it does not play through the speaker, record a person, or score naturalness. Fake-backend tests do not measure model quality. An audio-file smoke check bypasses microphone capture; it cannot establish recording usability.

App inference and speech services need normal local framework access. A restricted development-tool sandbox may deny that access even when the desktop app works. Report such a failure separately from a model failure; do not add a cloud fallback to work around it.

## Shared code and the iPhone app

[`apple/Package.swift`](apple/Package.swift) defines the reusable `LocalVoiceCore`, SwiftUI app, command-line checks, and tests. The answer, input speech, and output speech interfaces keep providers replaceable. Playback retains its synthesizer and delegate until completion; a sendable bridge moves only completion work to MainActor. The nonisolated, sendable audio callback converts hardware buffers before the asynchronous analyzer consumes them; UI state stays on the main actor.

The [development record](../development/README.md) scopes the Mac slice, and [current status](../status.md) records checks and known limits. The [iPhone project](apple/iOS/README.md) compiles the same SwiftUI source and links the same core. It adds an app icon, permission descriptions, privacy manifest, and distribution metadata. The phone layout has larger primary controls and a keyboard Done button; iOS audio interruptions and disconnected audio devices stop active work. English remains the language scope. Reproduce the real app build from `software/apple`:

```bash
./build-ios.sh simulator
```

This produces a native iPhone app bundle. On the iOS 26.5 simulator, an authored typed question returned a local answer; manual read-aloud completed, voice selection/preview and explicit stop worked, and the software keyboard dismissed with Done. Local transcription was unavailable. The simulator had Standard English speaking voices; the Mac's Premium voice is not bundled with the app. Distribution signing, upload, Apple processing, and owner invitation are complete in the [delivery milestone](../development/ios_testflight.md). Use the [iPhone installation guide](apple/iOS/README.md) to accept the invitation and install the beta. The physical target iPhone/OS remains to be confirmed. Each phone needs its own eligible model and installed voice.

If an embedded open model is needed, freeze the same model artifact, quantization, prompt policy, and context budget for Mac and iPhone, then measure the actual phone. Jetson needs a separate local backend. Follow the [architecture](../design_direction.md), [model-selection intake](../../../resources/project_proposals/apple_local_voice_intake.md), and [results policy](../results/README.md) before expanding scope or claiming performance.
