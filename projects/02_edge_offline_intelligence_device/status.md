# Current technical status

**Updated:** September 16, 2026
**App:** Mac Local Voice 0.2.0 (build 4); iPhone Local Voice Lab 0.3.0 (build 5), delivered through TestFlight, with basic iOS operation confirmed by the owner
**Tracking:** [Jetson procurement issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47); [iPhone/TestFlight issue 44](https://github.com/raghavan/longtail-inference-lab/issues/44); [speech-output milestone](https://github.com/raghavan/longtail-inference-lab/issues/42); [initial voice-input milestone](https://github.com/raghavan/longtail-inference-lab/issues/40)

## Current milestone

The [Linux/Jetson development application](software/jetson/README.md) now has local Ubuntu 22.04 ARM64 VM validation: pinned CPU runtimes and model hashes, 38 regression tests, real transcription/answer/speech-file generation with only loopback networking, actual CLI failure/cancellation checks, a tested system service, and compiled AtomS3-Lite button firmware. The [dated development record](results/2026-09-15-linux-vm-development.md) separates this evidence from physical hardware acceptance. CUDA, real USB devices, voice quality, on-board resource limits, and boot behavior remain open; no Jetson run has occurred.

All eight first-batch hardware items were ordered on September 13: the complete Orin Nano Super 8 GB kit from Arrow, six DigiKey audio/button/setup accessories, and the Newegg SanDisk Extreme 128 GB card. The supplied Arrow order confirmation matches the selected US-region kit at **$428.93 total**, comprising $399.00 in parts and $29.93 tax with free shipping. Arrow lists expected shipment September 14 and delivery September 21, 2026; actual dispatch, arrival, and device acceptance are not yet confirmed.

The [order record and arrival checklist](hardware/portable_procurement.md) preserves the exact eight parts and the next setup steps. DigiKey's $48.30 parts subtotal and Newegg's $42.99 card price are verified, while their final charges remain pending. The [budget](hardware/bill_of_materials.md) records $520.22 in known order costs so far, keeps the $1,000 first-year ceiling, and separates costs from remaining reserves. Do not repurchase any first-batch item. Public progress records omit all PII, order/tracking identifiers, private URLs, and raw purchase materials.

The first hardware stage is mains-powered speech input and output with a physical listening button; screen, battery, and portable enclosure are deferred. Jetson software, exact models, voice quality, memory headroom, latency, and the future battery target remain unmeasured.

The [macOS local voice development slice](development/README.md) is complete: local speech transcription, an editable visible transcript, and a streamed local text answer. The owner confirmed successful live voice input and visible text answers after the crash repair. The app now includes [local speech output](development/local_speech_output.md): manual **Read aloud** and **Stop speaking**, installed-voice selection, and a synthetic preview. Automatic selection prefers Premium, then Enhanced, then Standard English voices. The owner confirmed that initial read-aloud worked and found the compact voice mechanical; the updated app uses an installed Premium voice when available. The current workload is English general conversation, one question at a time. Additional languages are deferred. No web, document, or vector retrieval is included.

The [iPhone app and TestFlight delivery milestone](development/ios_testflight.md) is complete. The native target shares the Mac core and SwiftUI source; its typed-answer, manual speech, voice selection, and keyboard paths were exercised in the simulator. The arm64 archive passed signature verification, and App Store distribution signing and upload succeeded. Apple processed **0.3.0 (build 5)** and made it available in the internal **Owner testing** group. The TestFlight listing is **Local Voice Lab**; the installed app name remains **Local Voice**.

Following delivery on September 12, the owner confirmed that the beta works on their iOS device. This establishes owner-reported installation and basic operation on a physical iOS device. The report does not identify the device model, iOS version, or which individual voice-input, answer, and read-aloud paths were exercised. Those details, offline behavior, quality, and resource measurements remain open.

Delivery used existing Apple developer access and added no purchase or subscription. Distribution is limited to the authorized owner's internal TestFlight group; no public App Store release has occurred. Zero published comparative quality or performance measurements exist for Mac, iPhone, or Jetson. The first-year ceiling remains $1,000 across all required new hardware, subscriptions/software/distribution fees, tax, and shipping.

## Development checks observed

The development configuration was an M2 Pro with 16 GB memory, macOS 26.6 (25G70), Xcode 26.6, and the macOS 26.5 SDK. Swift 6 language mode is enabled. Apple's system models and speech assets are OS managed; exact weight revision, quantization, and asset hashes are not exposed by this implementation. The app has no retrieval or conversation-memory checkpoint. Prompt and bounds are in [AppleAnswerEngine](software/apple/Sources/LocalVoiceCore/AppleAnswerEngine.swift) and [Conversation](software/apple/Sources/LocalVoiceCore/Conversation.swift).

| Check | Observed outcome | Limit |
| --- | --- | --- |
| Native Mac build | Debug build and seventeen shared automated tests passed; prior release app packaging and signature verification passed | Build success does not establish model usefulness |
| Readiness | Local answer model available; English input speech assets and installed speech output reported ready | One development Mac only |
| Typed synthetic prompt | A real on-device answer was returned | Nonempty-output smoke check, no quality score or latency claim |
| Authored synthetic speech | A generated English audio fixture produced the expected transcript and a local text answer | File input bypasses microphone capture; no spontaneous-speech claim |
| Audio callback regression | A callback created from MainActor executed on a background executor, converted 48 kHz float audio to 16 kHz integer audio, and retained output after input reuse | Synthetic buffer test, not a transcription benchmark |
| App controls after repair | Microphone capture entered Listening; Cancel returned to idle; a completed question and visible answer were observed | Brief interactive check, not a reliability measurement |
| Local speech output | An authored English sentence produced 72,849 audio frames with non-silent samples and completion using `com.apple.voice.premium.en-US.Ava` | Buffer synthesis check, no human naturalness score; Apple manages asset revision and hash |
| Speech controls | Premium voice displayed and selected; Preview, Stop speaking, restart, and completion exercised in the packaged app | Brief interactive development check; no long-session reliability claim |
| iOS application build | Native app bundle compiled for arm64 and x86_64 iOS Simulator, SDK 26.5, deployment target iOS 26 | Compilation does not establish physical-phone eligibility or performance |
| iOS simulator interaction | iPhone 17 Pro simulator completed an authored typed question and manual read-aloud; voice selection, preview, explicit stop, and keyboard Done were exercised | Local transcription unavailable; Standard voices only; no physical-phone inference, audio, or performance claim |
| iPhone release archive | Xcode archive succeeded for 0.3.0 (build 5); arm64 binary, development signature, icon, privacy manifest, and iOS 26 minimum checked | Archive validation is separate from runtime behavior on a phone |
| App Store upload and processing | Distribution export and upload succeeded; Apple reports 0.3.0 (build 5) Complete in Build Uploads | Processing success does not establish app usefulness or public-release approval |
| Owner TestFlight access | At delivery, the internal group contained one build, Ready to Test, and one authorized owner tester, Invited | Distribution observation; future builds require deliberate group assignment |
| Physical iOS device basic use | Owner confirmed the delivered beta works on their iOS device | Owner report only; device/OS, individual feature paths, quality, offline behavior, and resource use are not yet recorded |
| Audio interruptions | Two controlled-backend regressions verify stopping playback preserves completed text and cancellation discards partial/late output | Physical calls, audio routes, and recording interruptions remain untested |
| Manual voice check | Owner confirmed voice input through visible text response in version 0.1.1 | No scored corpus, timing, private transcript, or recording retained in the public record |

The Premium voice setup displayed a 280.2 MB download and 323 MB installed storage on this Mac. These figures are OS voice-asset observations, not app size, peak RAM, or iPhone measurements. Only the voice preference is saved by the app; no conversation or audio is retained.

The [software guide](software/README.md) provides reproduction commands. Development checks and owner-reported basic iOS use are separate from the proposed platform evaluation. No latency distribution, memory-pressure result, disconnected-network test on Apple or Jetson hardware, structured iPhone evaluation, or Jetson run was collected. The separate Linux VM network-namespace check above applies only to that development environment.

## Failure and repair

Version 0.1.0 crashed after recording started. The audio-engine callback inherited MainActor isolation, while AVAudioEngine invoked it on its background audio queue. Swift's executor check trapped before processing the buffer. The earlier file-input speech check did not exercise that callback and missed the defect.

Version 0.1.1 constructs the callback in a nonisolated factory with a sendable closure. It captures only the converter and analyzer-input continuation, owns converted output buffers, and leaves UI updates on MainActor. A focused regression test invokes this same callback off the main queue. The rebuilt app then started and cancelled microphone capture without the reported crash, and the owner confirmed the voice-to-text-answer interaction.

The original crash report and personal screenshots remain private. This record contains only the technical cause, repair, and observed validation.

## Open validation

- Evaluate the Premium voice through listening checks; the Apple quality tier is not a conversational-naturalness score.
- Evaluate ordinary spoken questions, repeated record/stop/cancel cycles, permission denial, input-device changes, interruptions, and long sessions. A successful manual check does not establish reliability.
- Confirm offline operation after setup with a defined network-observation boundary.
- Record the tested iPhone/OS and confirm the individual voice-input, answer, and read-aloud paths. Test English voice availability, naturalness, startup delay, memory/storage, recording-to-playback transitions, and audio interruptions. Basic operation does not complete this gate.
- Freeze representative conversation cases and usefulness/resource gates before comparative measurements. The current single-turn prototype is not conversational memory.

## Durable record

The [project charter](README.md), [architecture](design_direction.md), [budget](hardware/bill_of_materials.md), and [intake](../../resources/project_proposals/apple_local_voice_intake.md) hold current decisions. GitHub issues track execution and link to these records. Follow the [public technical memory policy](../../areas/lab_operations/public_research_memory.md) for every update.
