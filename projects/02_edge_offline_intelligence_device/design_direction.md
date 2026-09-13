# ADR 01: Share the Apple app core and select models under iPhone constraints

**Status:** Proposed architecture; platform sequence and $1,000 first-year total ceiling agreed
**Date:** September 12, 2026
**Decider:** Project owner
**Evidence:** Mac development checks in [status](status.md); zero published comparative quality or performance measurements for Mac, iPhone, or Jetson

## Context

The first deliverable is a Mac app that transcribes speech locally, generates a local answer, displays text, and reads the completed answer aloud on request. The second is an iPhone app tested through TestFlight, with launch conditional on usefulness. The final prototype is a self-contained NVIDIA Jetson device. The Mac must exercise an answer model that the iPhone can actually use.

The development Mac runs macOS 26.6 on an M2 Pro with 16 GB memory; Xcode 26.6 is installed. English general conversation is the current workload; additional languages are deferred. The target iPhone/OS and representative cases are not yet specified. This prevents a final model choice. The [experiment intake](../../resources/project_proposals/apple_local_voice_intake.md) holds the proposed measurement plan. The separately specified [Mac development slice](development/README.md) implements the first Apple backend and has passed its development checks.

## Decision proposed

Use SwiftUI and a shared Swift core for the Mac and iPhone. Keep microphone capture, speech transcription, answer generation, and platform resource reporting behind small interfaces. Evaluate Apple's on-device speech and answer models first, then a small embedded open model if eligibility or quality requires it.

The first app needs a record/stop control, visible transcript, streamed text answer where supported, cancel, and clear model-readiness and failure states. The current app handles one question at a time. Installed Apple voices provide optional English read-aloud through `AVSpeechSynthesizer`, with explicit stop, preview, installed-voice selection, and no autoplay. Prefer Premium or Enhanced quality when installed; voice assets and storage are device specific. The native iPhone target shares the core and SwiftUI source; typed-answer and manual-speech simulator checks passed, while physical-phone behavior remains untested. Playback stops before a new recording or answer begins. Conversation history and additional languages remain outside this iteration.

```text
Mac / iPhone UI
       |
shared session controller, prompt policy, cancellation, evaluation events
       |                                  |
local Transcriber                    local AnswerEngine
       |                                  |
Apple Speech                         Apple SystemLanguageModel
or embedded speech model             or embedded open model
```

The shared interfaces describe capabilities and failures without assuming a particular provider's token stream, context window, or sampling controls. They carry readiness, final transcript, partial/final answer, cancellation, and sanitized timing events. The Jetson implementation follows this contract with a Linux audio/UI layer and local open models; SwiftUI and Apple system models do not transfer to it.

## Options considered

| Option | Benefit | Cost or limitation | Disposition |
| --- | --- | --- | --- |
| Apple speech + Apple on-device answer model | Same native APIs on Mac and iPhone; no separately bundled answer weights | Eligible devices, supported languages, enabled/downloaded assets, OS-managed model versions; workload limitations; Apple-only backend | First candidate to evaluate |
| Apple speech + embedded quantized open answer model | Same pinned answer artifact on Mac and iPhone; a path to reuse answer weights on Jetson | App-managed storage, runtime integration, context memory, startup, thermal and battery costs | Fallback if the selected task or phone rules out Apple's answer model |
| Embedded open speech + answer models | Greatest model portability and control | Two model assets and additional memory/runtime work; speech quality must be measured too | Use where Apple speech is unavailable or for the Jetson backend |

An inference server running on the Mac would not satisfy the iPhone's local execution requirement. The open-model path embeds inference in the app process.

## What Apple's APIs support

Apple's `SpeechAnalyzer` and `SpeechTranscriber` support on-device transcription on iOS 26 and macOS 26. Check device availability, supported locale, and installed assets. Apple manages the speech assets in system storage and runs this recognition outside the app's process; that changes app accounting but does not make the device resource cost zero. [Apple speech introduction](https://developer.apple.com/videos/play/wwdc2025/277/), [SpeechTranscriber](https://developer.apple.com/documentation/speech/speechtranscriber), [AssetInventory](https://developer.apple.com/documentation/speech/assetinventory).

Use the explicitly on-device `SystemLanguageModel` answer backend. The current Foundation Models framework also documents cloud options, so choosing the framework alone does not establish locality. Check model availability and handle ineligible hardware, disabled Apple Intelligence, and assets that are not ready. [Foundation Models](https://developer.apple.com/documentation/foundationmodels), [SystemLanguageModel](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel).

Apple describes the local model as useful for tasks such as summarization, extraction, text understanding, and writing. Its guidance cautions about math, coding, logical reasoning, and world-knowledge demands. This is a reason to evaluate actual intended questions before promising a general assistant. The documented on-device context window is 4,096 tokens across instructions, input, and output; verify it for the deployed OS/model. [Generation and task guidance](https://developer.apple.com/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models).

The app APIs require OS 26 or later on the Apple path. Apple Intelligence additionally requires eligible hardware, enabled settings, supported language/region, and downloaded assets. Apple's support page lists iPhone 15 Pro models and iPhone 16 or later, and estimates 7 GB of device storage for Apple Intelligence as a whole. This is a shared system requirement, not our app's download size. [Apple Intelligence requirements](https://support.apple.com/en-us/121115).

Apple controls model updates with OS releases. Mac and iPhone can share the integration, prompts, and evaluation criteria without guaranteeing identical system weights. Record OS builds and any exposed model metadata, and rerun the evaluation after upgrades. [Updating prompts for model versions](https://developer.apple.com/documentation/foundationmodels/updating-prompts-for-new-model-versions).

## Open-model candidates and portability

For a fallback, start with a small candidate band rather than selecting the largest model the Mac can run. Qwen3-0.6B is a compact text-model control. Qwen3.5-0.8B is another current candidate, but its model card scopes it toward prototyping and warns about thinking loops. Test bounded output and a non-thinking configuration where supported. A model around 1–2B, such as Qwen3-1.7B, is a possible next comparison only if the smaller candidates fail useful tasks. These are a shortlist, not a claim about the best or globally smallest usable model. [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B), [Qwen3-1.7B GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF).

`llama.cpp` provides an iOS/macOS XCFramework and Apple Metal and NVIDIA CUDA backends. This makes it a reasonable embedded-runtime candidate across the three platforms. Freeze the runtime revision, exact converted model, quantization, license, chat template, context limit, and decoding settings after compatibility checks. Verify current-model support in the selected mobile build; an upstream example is not a successful iPhone test. [XCFramework documentation](https://github.com/ggml-org/llama.cpp/blob/master/docs/xcframework.md), [runtime backends](https://github.com/ggml-org/llama.cpp).

Model file size, app download size, persistent storage, and peak runtime memory are different measurements. Quantization reduces weights but does not remove context caches, temporary buffers, UI, or audio costs. There is no single safe memory allowance for every iPhone; use the actual device under pressure and record termination and thermal behavior.

## Consequences and action items

1. Confirm the target iPhone/OS and choose representative English general-conversation cases. Agree on usefulness and acceptable wait time in the intake. The $1,000 first-year budget scope is confirmed and includes all required hardware, subscriptions, software/distribution fees, tax, and shipping.
2. The authorized Mac development slice, including optional English speech output, now works. Identify and test the physical iPhone before expanding the Mac feature set, then complete the comparative intake. The product iteration order remains Mac then iOS; compatibility is checked early.
3. Compare answers on correct typed transcripts first, then the complete spoken interaction. This separates answer-model limitations from speech-recognition errors.
4. Keep the selected backend and prompt policy aligned across Mac and iPhone. Ship a small capability surface with explicit unsupported/unavailable states and no automatic cloud fallback.
5. Test offline after initial assets are installed. TestFlight delivery and model downloads belong to setup, not measured offline inference. Clear or asset-missing states must fail visibly rather than silently use a server.
6. Use TestFlight for physical-device feedback, then make a recorded launch decision. Apple Developer membership is $99 per year if not already covered; beta distribution and App Store release have their own review steps. [TestFlight](https://developer.apple.com/testflight/), [membership](https://developer.apple.com/programs/whats-included/).
7. Before Jetson procurement, select a full configuration within the remaining $1,000 first-year ceiling. An 8 GB Orin Nano and a 16 GB Orin NX are different tiers. Revalidate local model and speech backends on Jetson, then measure the physical system. [NVIDIA lineup](https://developer.nvidia.com/embedded/jetson-modules).
