# Local English speech output

**Status:** Development implementation checked on September 12, 2026; physical iPhone validation remains open.

This extension uses the relevant sections of the [experiment template](../../../resources/experiment_template/README.md). It extends the existing Mac application; it does not select a new answer model or complete the comparative platform evaluation.

## Question, decision, and workload

Can the app read a completed answer aloud locally on request, offer a higher-quality installed voice, and keep the implementation compatible with iOS without disrupting recording or answering?

The current scope is English general conversation, with playback only after pressing **Read aloud** or **Preview voice**. Preserve the visible answer when speaking, stopping, or choosing a voice. Use installed Apple system voices through `AVSpeechSynthesizer`, with no personal-voice permission, third-party provider, paid subscription, or retained audio. Additional languages are deferred. Translating interface labels would not itself materially change inference speed; avoiding an additional model keeps the current implementation and resource requirements smaller. No performance improvement has been measured.

## Implementation and observed constraints

The app prefers Premium, then Enhanced, then Standard English voices, with an English (United States) preference within the same quality tier. A selected installed voice overrides automatic ranking. The voice selector displays the actual name, quality, and locale; its preference is saved locally. No questions or answers are saved. A removed selection falls back to the best installed voice and updates the displayed selection. Preview uses a deliberately authored sentence, never a stored conversation.

The initial installed compact voice produced audio and the owner confirmed playback, but found the speech mechanical. A subsequent development check used `com.apple.voice.premium.en-US.Ava`, quality Premium. The system settings displayed a 280.2 MB download and 323 MB installed storage for this voice on the development Mac. These are Mac setup observations, not app download size, peak RAM, or an iPhone storage measurement. No paid subscription was added. System voice downloads require internet once; app playback uses the installed voice.

Voice availability belongs to each device. The shared API does not guarantee that a particular named Mac voice exists on every iPhone. Discover installed English voices at runtime and expose download guidance. The source compiled and linked for both arm64 and x86_64 iOS Simulator with the iOS 26.5 SDK and an iOS 26 deployment target. The [iPhone delivery milestone](ios_testflight.md) also records a packaged app, manual playback and voice-control checks in the simulator, and owner TestFlight delivery. Physical iPhone voice availability and quality remain untested.

## Success and stop boundaries

Success requires a reproducible build; real synthetic text-to-audio checks; manual-only playback; stop/cancel/restart behavior; playback stopped before microphone capture; visible voice selection and quality; and iOS SDK compilation.

Stop playback immediately before recording, answering, changing voices, clearing, or cancelling. Ignore completion callbacks from earlier playback. Bound each utterance to 4,000 characters and playback to 120 seconds. Keep partial and cancelled answers silent. If no installed eligible English voice exists, retain the answer and show the limitation. Never substitute a cloud service.

Speech delegate callbacks bridge only a sendable closure to MainActor. They do not move the non-sendable utterance into asynchronous tasks. On iOS, playback uses an automatically managed speech audio session after capture ends. The existing nonisolated microphone callback repair is preserved.

## Controls and validation

Seventeen shared automated tests cover input, generation, cancellation, and microphone-callback behavior plus manual playback, stop before recording, stale playback callbacks, clearing, missing voices, voice changes, removed assets, quality-based voice selection, and audio interruptions. An authored English sentence produced non-silent audio and a completion marker with the installed Premium voice on the Mac. Neither the test nor the Apple quality label is a human naturalness score.

Record app/source revision, OS/SDK, voice identifier, locale, and synthesis bounds. Apple manages the voice assets and does not expose a pinned weight revision or hash here. No private recordings, conversations, or screenshots enter the public record. A defined disconnected-network observation has not been performed.

## Completion and next question

The [status record](../status.md) and [software guide](../software/README.md) hold exact checks and reproduction steps. The owner confirmed basic iOS operation after installing the TestFlight beta; record the tested device/OS and confirm the individual speech paths. Evaluate installed English voice quality, local playback, stop/record transitions, interruptions, storage, memory, startup delay, and usefulness there before making phone quality or performance claims. Apple voices do not transfer to the later Jetson device; its local output backend remains a separate implementation decision.

## Primary references

- [Apple speech synthesizer](https://developer.apple.com/documentation/avfaudio/avspeechsynthesizer): speaking, stopping, delegate events, and generated audio buffers.
- [Apple voice quality](https://developer.apple.com/documentation/avfaudio/avspeechsynthesisvoicequality): Standard, Enhanced, and Premium qualities; higher-quality assets require download.
- [Change the Mac speaking voice](https://support.apple.com/guide/mac-help/change-the-voice-your-mac-uses-to-speak-text-mchlp2290/mac): system voice downloads and selection.
- [iPhone Read & Speak settings](https://support.apple.com/guide/iphone/hear-whats-on-the-screen-or-typed-iph96b214f0/ios): voice and dialect selection on iOS 26.
