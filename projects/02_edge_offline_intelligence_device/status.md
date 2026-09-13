# Current technical status

**Updated:** September 12, 2026
**App:** Local Voice 0.1.1 (build 2), source in this revision
**Tracking:** [GitHub issue 40](https://github.com/raghavan/longtail-inference-lab/issues/40)

## Current milestone

The [macOS local voice development slice](development/README.md) is complete: local speech transcription, an editable visible transcript, and a streamed local text answer. The owner confirmed successful live voice input and visible text answers after the crash repair. The initial workload is general conversation in English (United States), one question at a time. No web, document, or vector retrieval is included.

No public app release, TestFlight upload, or hardware purchase has been performed in this milestone. Zero published comparative quality or performance measurements exist for Mac, iPhone, or Jetson. The first-year ceiling remains $1,000 across all required new hardware, subscriptions/software/distribution fees, tax, and shipping.

## Development checks observed

The development configuration was an M2 Pro with 16 GB memory, macOS 26.6 (25G70), Xcode 26.6, and the macOS 26.5 SDK. Swift 6 language mode is enabled. Apple's system models and speech assets are OS managed; exact weight revision, quantization, and asset hashes are not exposed by this implementation. The app has no retrieval or conversation-memory checkpoint. Prompt and bounds are in [AppleAnswerEngine](software/apple/Sources/LocalVoiceCore/AppleAnswerEngine.swift) and [Conversation](software/apple/Sources/LocalVoiceCore/Conversation.swift).

| Check | Observed outcome | Limit |
| --- | --- | --- |
| Native build | Debug build, seven automated tests, and release app packaging passed | Build success does not establish model usefulness |
| Readiness | Local answer model available; English speech assets prepared and reported ready | One development Mac only |
| Typed synthetic prompt | A real on-device answer was returned | Nonempty-output smoke check, no quality score or latency claim |
| Authored synthetic speech | A generated English audio fixture produced the expected transcript and a local text answer | File input bypasses microphone capture; no spontaneous-speech claim |
| Audio callback regression | A callback created from MainActor executed on a background executor, converted 48 kHz float audio to 16 kHz integer audio, and retained output after input reuse | Synthetic buffer test, not a transcription benchmark |
| App controls after repair | Microphone capture entered Listening; Cancel returned to idle; a completed question and visible answer were observed | Brief interactive check, not a reliability measurement |
| Manual voice check | Owner confirmed voice input through visible text response in version 0.1.1 | No scored corpus, timing, private transcript, or recording retained in the public record |

The [software guide](software/README.md) provides reproduction commands. Development checks are separate from the proposed platform evaluation. No latency distribution, memory-pressure result, disconnected-network test, iPhone run, or Jetson run was collected.

## Failure and repair

Version 0.1.0 crashed after recording started. The audio-engine callback inherited MainActor isolation, while AVAudioEngine invoked it on its background audio queue. Swift's executor check trapped before processing the buffer. The earlier file-input speech check did not exercise that callback and missed the defect.

Version 0.1.1 constructs the callback in a nonisolated factory with a sendable closure. It captures only the converter and analyzer-input continuation, owns converted output buffers, and leaves UI updates on MainActor. A focused regression test invokes this same callback off the main queue. The rebuilt app then started and cancelled microphone capture without the reported crash, and the owner confirmed the voice-to-text-answer interaction.

The original crash report and personal screenshots remain private. This record contains only the technical cause, repair, and observed validation.

## Open validation

- Evaluate ordinary spoken questions, repeated record/stop/cancel cycles, permission denial, input-device changes, interruptions, and long sessions. A successful manual check does not establish reliability.
- Confirm offline operation after setup with a defined network-observation boundary.
- Identify the physical iPhone/OS and requested language support; build and test that target before expanding the Mac feature set.
- Freeze representative conversation cases and usefulness/resource gates before comparative measurements. The current single-turn prototype is not conversational memory.

## Durable record

The [project charter](README.md), [architecture](design_direction.md), [budget](hardware/bill_of_materials.md), and [intake](../../resources/project_proposals/apple_local_voice_intake.md) hold current decisions. GitHub issues track execution and link to these records. Follow the [public technical memory policy](../../areas/lab_operations/public_research_memory.md) for every update.
