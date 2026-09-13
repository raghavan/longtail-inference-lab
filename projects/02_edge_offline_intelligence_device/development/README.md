# macOS local voice development slice

**Status:** Complete development milestone on September 12, 2026; implementation and live voice check confirmed. Broader model selection remains open.

This record applies the relevant sections of the [experiment template](../../../resources/experiment_template/README.md) to the first implementation slice. It does not freeze or execute the broader Mac/iPhone model-selection experiment.

## One minute summary

**Question:** Can the development Mac capture one utterance, transcribe it locally, and display a streamed answer from its on-device language model, with clear readiness, failure, and cancellation behavior?

**Decision:** Build the smallest native interaction and use its observed failures to determine the next implementation step. Keep the model backend replaceable.

**Workload:** General offline conversation without web, document, or vector retrieval. English (United States) is the initial development control. Additional languages and the physical iPhone target remain open for later validation; they do not establish claims about this Mac slice.

**Success boundary:** A reproducible native Mac build; a real local answer smoke check; local transcription of a deliberately authored synthetic recording; explicit model-readiness and cancellation behavior. Live microphone usability requires a manual check by the operator.

**Stop boundary:** Stop the affected path if local assets are unavailable, capture cannot stop, or a local backend would require remote inference. Show the limitation. A successful build or synthetic test does not satisfy the broader quality or latency gates.

## Practical context and agreed constraints

The owner requested implementation to start. The first deliverable accepts voice and returns visible transcript and text answer. The later iPhone app should share application logic and model integration; the final Jetson device requires its own supported model backend. The confirmed first-year ceiling is $1,000 for hardware, required subscriptions/software/distribution fees, tax, and shipping.

The known development condition is Apple silicon with 16 GB memory, macOS 26.6, and Xcode 26.6. English is a reversible development default, not a final language-support promise. The target iPhone/OS and requested languages have been asked for; phone-specific model selection and release decisions remain pending those answers and device tests.

## Measurement objective, variables, and controls

This milestone verifies implementation behavior rather than comparing model quality. Use Apple's explicitly on-device answer backend and SpeechTranscriber, a fresh answer session per request, bounded input/output, a bounded recording duration, and one active interaction at a time. Record code revision and OS/build for real smoke checks. Keep the user-visible transcript editable so recognition and answer failures can be distinguished.

Separate a typed synthetic prompt from synthetic-audio transcription and from the manual microphone interaction. Record which paths actually ran. Freeze quality and performance controls later in the [model-selection intake](../../../resources/project_proposals/apple_local_voice_intake.md).

## Assumptions, tails, and failure boundaries

The system model and speech assets may be missing or become unavailable. Setup may download local assets; inference must use the local backend. Cancellation must prevent stale results from overwriting a newer interaction. Empty input, long input, permission denial, interrupted capture, model errors, and timeout must leave the UI usable.

Keep captured audio in memory and discard it at the end of the interaction. Keep transcript and answer in the current app session only. Publish authored synthetic fixtures and sanitized outcomes; never publish private speech, personal or emotional content, or raw host logs. The UI is not an instrumented proof of zero network traffic.

## Sequence and removal checks

1. Inspect model and speech readiness without capturing audio.
2. Build shared application state and a replaceable answer interface.
3. Connect the local model to typed input and verify streaming, input bounds, and cancellation.
4. Connect local speech transcription and record/stop controls; test a synthetic recording separately.
5. Package the Mac app and inspect its visible states. Leave a manual microphone check explicit.
6. Publish technical status with the build, smoke checks, failures, and next validation gate.

Typed input removes recognition from the path to locate failures. Controlled fake backends verify stale-result and cancellation behavior; label them as software tests, not model evidence.

## Reproduce, results, and interpretation

The [software guide](../software/README.md) holds build and run commands. The [status record](../status.md) reports seven passing automated checks, real local answer and synthetic speech checks, the microphone crash and repair, and owner-confirmed live voice input and visible text answers. [GitHub issue 40](https://github.com/raghavan/longtail-inference-lab/issues/40) tracks this slice. Zero published comparative quality or performance measurements exist for Mac, iPhone, or Jetson.

A successful smoke check establishes only that the named local path executed. It cannot establish broad conversational usefulness, stable tail latency, phone memory fitness, or device-level offline integrity. Synthetic speech is not equivalent to the owner's microphone, accent, room, or spontaneous utterances.

## Completion condition and next question

The development completion condition is met: the app builds, real local answer and synthetic speech paths ran, cancellation/error behavior was checked, limitations are recorded, and the owner confirmed the live voice interaction. The next gate is extended voice use and the physical iPhone compatibility check, followed by a frozen model-selection workload and measured comparison.
