# Apple Local Voice: Model Selection Intake

**Status:** Idea — comparative intake draft; measured execution has not begun. A separately specified Mac development slice now works.
**Track:** Local inference and Apple application systems
**Difficulty:** Intermediate
**Owner:** Raghavan
**Last updated:** September 12, 2026

This is a working copy of the [experiment template](../experiment_template/README.md) for the next bounded question within the [Edge Offline Intelligence Device project](../../projects/02_edge_offline_intelligence_device/README.md). User requirements are recorded as agreed; proposed methods and thresholds remain provisional until the material intake is complete.

## One minute summary

**Question:** Which local answer backend can serve the owner's intended voice-input tasks on both a Mac and the target iPhone within useful quality, latency, memory, and storage limits?

**Decision:** Evaluate Apple's on-device model first. If unavailable or insufficient for the selected task, choose the smallest tested open model that meets the same gates on the actual iPhone and use it on both Apple platforms.

**Workload:** General offline conversation, with no web or document/artifact retrieval. Languages and representative evaluation cases still need to be specified. Proposed pilot: 20 representative cases with three repetitions per backend and platform; use the same sanitized reference transcripts and approved speech recordings.

**Success boundary:** A backend meets the agreed usefulness and responsiveness criteria on both physical devices, works after network loss, and handles unavailable assets and cancellation clearly.

**Stop boundary:** No candidate is useful within the phone's resource envelope, or the interaction depends on remote inference. Narrow the workload or change the approach before expanding the application.

## Research question

Compare Apple's on-device answer backend with a compact embedded open model only when needed, holding the task set, transcript, answer instructions, and interaction policy fixed. Measure usefulness, end-of-recording to visible-answer latency, storage, memory, and failures on the development Mac and one named physical iPhone. Model-only typed-transcript trials separate answer quality from recognition quality; spoken trials measure the complete interaction.

## Why this belongs in the lab

The iPhone is the first constrained deployment target. A Mac-only success can conceal model storage, memory-pressure, thermal, eligibility, or language failures on the phone. This experiment tests useful local capability before spending the project budget on a physical appliance.

## Practical context

The owner wants to speak a request, see what was understood, and read a local answer. The agreed sequence is a macOS app, an iOS app distributed through the owner's TestFlight, a conditional launch decision, and a self-contained NVIDIA prototype. The Mac and iPhone should share their selected model integration. The confirmed first-year total ceiling is $1,000, including all new hardware for the end product and required subscriptions, software/distribution fees, tax, and shipping.

The Mac has an M2 Pro, 16 GB memory, macOS 26.6, and Xcode 26.6. A separately specified [development slice](../../projects/02_edge_offline_intelligence_device/development/README.md) has a working local voice-to-text-answer interaction and passing implementation checks. English is the current agreed language scope; additional languages are deferred. The target iPhone/OS and representative conversation cases remain material gaps for this comparison. The spending scope is confirmed: all required new hardware and first-year subscriptions/software/distribution fees share the $1,000 ceiling, including tax and shipping. The [architecture research](../../projects/02_edge_offline_intelligence_device/design_direction.md) records the primary sources and API limitations.

## Decision being informed

1. If Apple's local backend meets the gates on both devices, use it for the Apple apps and record its OS-managed model limits.
2. If it fails eligibility or useful tasks, compare compact embedded open models and retain the smallest tested candidate that passes.
3. If evidence is mixed, publish the task-specific boundary and run one targeted follow-up or simplify the task.
4. This pilot cannot justify broad assistant claims, App Store launch, or Jetson performance. Those require their own evidence.

## What you will learn

1. Whether Apple's local APIs suit the intended devices, languages, and tasks.
2. Which failures come from recognition and which come from the answer model.
3. How model storage, context, and runtime memory affect a real iPhone.
4. What can be shared between Apple apps and what requires a new backend on Jetson.

## Hypothesis or measurement objective

Measure the smallest useful local configuration. Do not assume that Apple Intelligence or any sub-billion-parameter model can answer the intended questions well. The outcome may be a narrower task definition instead of a model selection.

## Assumptions and model error

The sample must represent actual intended use and the phone must represent the first TestFlight target. Scripted speech may be clearer than spontaneous use; report that limitation. A simulator is useful for UI development but is not a memory or thermal proxy for the phone.

Apple may not expose exact weights or all system-process resource use. Record OS/build and available metadata, mark unobservable fields, and re-evaluate after OS/model updates. Open-model weights and runtime revisions can be pinned; hardware-dependent numerical differences can still occur.

Do not equate parameter count with peak memory, app footprint with all device storage, or a locally stored transcript with absence of network transmission. A small pilot cannot establish stable p99 behavior or rare-event safety.

## Tail characteristics

**Demand tail:** Accents, background noise, names, requested languages, ambiguous utterances, and less familiar task variants.

**Resource tail:** Cold model start, long input, long output, repeated turns, low available memory, and a warm device.

**Failure tail:** Wrong transcription that changes the request, confident unsupported answers, endless generation, asset unavailability, crashes, and failure to cancel. Report slow and failed attempts alongside completed ones.

## Ruin boundary

Local inference must not silently switch to a server. An unavailable local backend produces a visible failure. Audio, transcripts, and answers remain transient by default; retained evaluation material requires an agreed local policy and publication permission.

The baseline returns text and performs no external actions. Mark interruption and partial output clearly, stop capture when recording ends or the session is cancelled, and bound generation. A breached privacy boundary or persistent resource failure stops that condition until its cause is understood. No high-stakes reliability claim follows from this pilot.

## Path dependence

Use a fresh single-turn session for the proposed baseline. Report cold start separately from warm repetitions. Counterbalance backend order to reduce thermal and practice bias, and record retries rather than replacing failures. If conversational memory becomes a requirement, define separate history conditions before adding it.

## Variables and controls

Vary the answer backend and physical platform. Freeze workload revision, reference transcript, speech recording, locale, answer instructions, input/output bounds, and the supported decoding controls within each backend. Tokenization and sampling controls are not necessarily equivalent across providers; record differences instead of implying exact equivalence.

For open models, also freeze source revision, conversion, quantization, file hash, license, runtime, and context size. Hold power/charging state, room conditions, and competing work as steady as practical. Record unavoidable variation. Proposed sample size is exploratory: 60 attempts per candidate per platform, with additional stress trials reported separately.

## Workload and evidence source

The initial task family is general offline conversation, with no web or document/artifact retrieval. Use English for this iteration and select representative cases for that family. Use 20 sanitized cases reflecting that answer, including a few deliberately difficult cases. Record the source, expected useful behavior, reference transcript, and a scoring rubric before testing.

Label authored or synthetic material explicitly. Do not use it to claim success on private notes, spontaneous conversations, or broader populations that were not tested. Keep scoring references outside model inputs unless supplying source text is part of the task itself.

## Experiment sequence

### Phase 1: observe the current system

After intake and implementation authorization, check speech locale/assets and answer-model readiness on both physical devices. Run a minimal native slice. Score answers to correct typed transcripts before connecting microphone errors to the result.

### Phase 2: test the smallest useful intervention

Add local recording, visible transcript, and local text answer on the Mac using the same selected backend intended for iPhone. Run the early iPhone slice before expanding the Mac UI. If Apple fails eligibility or task quality, test a bounded small open-model shortlist described in the architecture decision.

### Phase 3: stress and fragility tests

Repeat with cold start, network disabled after asset installation, longer inputs, ambient noise, cancellation, audio interruption, a warm phone, and ordinary memory pressure. Test unavailable model/assets explicitly. Use a defined safe output/time cap and count exhaustion as failure.

### Phase 4: removal test

Replace recognition output with the correct transcript to locate speech-induced failures. Compare the smallest candidate with a larger one only where the smaller one fails the agreed task. Retain extra model cost only if it changes the practical decision.

### Phase 5: analysis and decision

Publish separate platform results and per-case failures. Choose a backend, narrow the workload, or stop. Then freeze the Mac implementation plan and the physical iPhone/TestFlight validation gate. Hardware remains a later iteration.

## Metrics

These initial gates are **proposed**, not agreed performance requirements or observed results. Confirm them with the workload before measured collection.

| Metric | Definition and direction | Proposed pilot gate or reporting rule |
| --- | --- | --- |
| Useful answers | Owner scores each response against a task-specific rubric; higher is better | At least 90% useful responses and at least 18 of 20 cases useful in two of three repetitions; report failures by task |
| Transcription error | Word error rate against reference text where appropriate; use a language-appropriate alternative when word segmentation is unsuitable | Report overall and per-case errors plus meaning-changing errors; define an acceptable boundary after languages/tasks are known |
| First visible answer | Monotonic time from end of recording to first rendered answer text, excluding status labels | Proposed warm p95 ≤5 seconds on each device; separate model-only and cold-start timings |
| Completed answer | End of recording to final rendered answer | Proposed warm p95 ≤15 seconds under a frozen short-answer length policy |
| Reliability | Completed, failed, cancelled, and timed-out attempts with total counts | No unexplained crash, memory termination, hung generation, or failure to cancel in the pilot; report all observed failures |
| Footprint | App download/install size, extra model assets, and measured peak app memory | Report separately; select a phone-specific limit before model selection, with observed headroom under pressure |
| Offline operation | Completed interaction with required assets present and network unavailable; inspect app dependencies/traffic with platform-appropriate tools | Every offline test completes or gives an explicit local error; zero app inference or content transfer to a remote service |

Report sample count, p50, p95, and maximum. Any p99 from this small pilot is exploratory. App instrumentation omits microphone-to-buffer and display scheduling effects unless explicitly measured; system-owned speech/model memory may not be fully visible. Record these limits. Battery percentage changes are only a coarse proxy for energy; Jetson needs device power measurement.

## Reproduce

The [software guide](../../projects/02_edge_offline_intelligence_device/software/README.md) contains Mac and iPhone build, delivery, and development-check commands. Before measured execution, record the build revision, signed development configuration, OS and hardware class, model/runtime metadata, speech assets/locale, workload and prompt hashes, repetition order, power state, and measurement procedure. Use portable paths and sanitized identifiers. Keep initialization downloads separate from offline runs.

## Results

Zero measured comparative results for this intake. The [development checks and owner TestFlight delivery](../../projects/02_edge_offline_intelligence_device/status.md) establish an implemented interaction and a beta available for physical-phone evaluation. They do not establish answer quality or platform performance. Publish future results through the project's [results policy](../../projects/02_edge_offline_intelligence_device/results/README.md), including incomplete and failed conditions.

## Operational conclusion

**Evidence observed:** Primary documentation supports candidate local Apple APIs and an embedded open-model alternative. The Mac development slice works, including owner-confirmed voice input and text answers. The native iPhone app completed simulator checks and TestFlight delivery, after which the owner confirmed basic iOS operation. Device/OS details, individual feature checks, and workload quality remain open.

**Decision supported:** Record the three-iteration direction and prepare the bounded model-selection test.

**Decision not supported:** A final model choice, broad conversational usefulness, a public release, or a claim that any model fits the Jetson's operating envelope. The separately authorized owner beta enables evaluation and is not evidence of readiness for a wider audience.

**Safe operating region:** Not measured.

**Escalation conditions:** Unsupported local tasks produce an explicit limitation or require human judgment. This plan does not authorize cloud fallback.

**Confidence:** High in the documented platform distinctions; undetermined in application usefulness and performance.

## Interpretation

The Apple path can share native integration with less app-managed model packaging. The open-model path offers stronger artifact continuity across Mac, iPhone, and Jetson. Their practical tradeoff must be measured against the selected workload; model size alone cannot resolve it.

## Limitations and open evidence

Material intake still needed: tested iPhone and OS; representative English general-conversation cases. The first-year spending scope is confirmed. Agree the provisional usefulness, latency, transcription, and resource gates once those answers make them concrete. Separate development milestones implemented the Mac app and delivered Local Voice Lab 0.3.0 (build 5) through the owner's internal TestFlight group. The owner confirmed that the beta works on their iOS device; detailed feature, quality, offline, and resource checks remain open. No new purchase or comparative measured execution has occurred.

Exact Apple model weights and some system resource costs may remain unobservable. One owner, one phone, and a small scripted workload do not establish general usability. Jetson and a launch-quality iOS beta require independent evaluation.

## Completion condition

A complete experiment publishes a reproducible baseline, candidate comparison where needed, usefulness scores, latency/resource distributions, complete attempt accounting, a stress and removal test, offline evidence and its limits, and a recorded backend or stop decision. Until the material intake and frozen plan are complete, this stays in resources as a proposal.

## Next smallest question

After selection, does the complete Mac interaction remain useful in ordinary speech, and does the same backend survive the physical iPhone's TestFlight conditions? Specify that follow-up from observed failures rather than expanding the feature list in advance.
