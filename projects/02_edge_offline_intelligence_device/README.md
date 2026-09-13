# 02 Edge Offline Intelligence Device

**Status:** Active project; Mac app works and the owner confirmed basic use of the iOS TestFlight beta. Seven of eight hardware items are ordered: six DigiKey accessories and one Newegg microSD card. The Jetson kit order remains unconfirmed. Detailed device evaluation and model-selection intake remain open.
**Evidence:** Development checks, owner-confirmed Mac voice input/text response, and an owner report of basic iOS operation; zero published comparative quality or performance measurements for Mac, iPhone, or Jetson.
**Track:** Local inference and device systems
**Last updated:** September 13, 2026

## One minute summary

**Question:** Can a useful local voice-to-text-and-answer experience fit the constraints of an iPhone, share its model integration with a Mac app, and inform a self-contained Jetson device?

**Decision:** Build in three iterations: macOS, iOS with TestFlight, then Jetson. Choose the Apple app model against the target iPhone's constraints from the start. The project has a **$1,000 total ceiling for its first year**, including all new hardware for the end product and required subscriptions, software/distribution fees, tax, and shipping.

**First interaction:** Speak into the Mac, see the transcript, and read a locally generated answer. Recognition, answer generation, and optional English speech synthesis run on the device. A completed answer remains visible and plays only after pressing **Read aloud**.

**Next bounded question:** Which local answer backend meets the selected workload on both the Mac and the target iPhone with acceptable quality, latency, memory, and storage? The [intake draft](../../resources/project_proposals/apple_local_voice_intake.md) records the agreed scope, proposed comparisons, and material questions still open. It is not a frozen experiment or an implementation claim.

## Iterations and decision gates

| Iteration | Deliverable | Evidence needed to advance |
| --- | --- | --- |
| 1. macOS | Native app: record speech, display transcript, generate and display a text answer locally, with optional English read-aloud and visible stop, cancel, and error states | Real speech and model runs on the selected workload; a small early compatibility check on the target iPhone; measured quality, text latency, memory, storage, and offline operation |
| 2. iOS | Native iPhone app using the same selected answer backend, prompt policy, and shared application logic; distribution through the owner's TestFlight | Physical-device tests under memory pressure, cold start, interruptions, thermal load, and loss of connectivity; beta feedback against agreed usefulness criteria |
| 3. Jetson | Self-contained NVIDIA device running recognition and answers locally, with its own input, output, storage, and power | A complete parts quote within the remaining budget and measured Jetson latency, memory, energy, thermals, and offline integrity |

A successful TestFlight beta supports a launch decision; launch remains conditional on the evidence and App Store review. The first physical stage is a mains-powered Jetson: press a button to record, press again to finish, then receive a locally generated spoken reply. Screen, battery, and portable enclosure are later decisions. The eventual approximately two-hour battery target is unmeasured. Each platform publishes its own measurements.

## Agreed requirements and proposed defaults

The September 12 direction fixes the platform sequence, local recognition and answering, visible text and optional manual English speech output on the Mac, Mac/iPhone model continuity, conditional iOS launch, NVIDIA as the physical prototype target, and the $1,000 first-year total ceiling.

The [architecture decision](design_direction.md) proposes SwiftUI with a shared Swift application core, Apple on-device speech recognition, and evaluation of Apple's on-device Foundation Models backend first. If it cannot serve the chosen workload or target phone, evaluate a small quantized open model in an embedded runtime. These are recommendations awaiting the model-selection experiment, not measured winners.

For Apple models, continuity means the same on-device integration and tested behavior: Apple controls system model updates, so identical weights cannot be promised across OS versions. With an open model, freeze the same model artifact, quantization, prompt policy, and context budget for Mac and iPhone. Numerical output can still vary by runtime and accelerator.

Apple's model is an Apple-platform dependency. Jetson requires a local open-model backend and a different platform layer. Reuse the interaction contract, prompts, evaluation cases, and portable model artifacts where applicable; validate each backend on its own hardware.

## Budget and hardware

The [shopping list and restart checklist](hardware/portable_procurement.md) contains eight exact items from Arrow, DigiKey, and Newegg. It records dated stock observations, setup dependencies, and the proposed device acceptance steps. The owner confirmed ordering all six DigiKey accessories on September 13; the export confirms $48.30 in parts, with the final delivered total pending. The Newegg order summary confirms one SanDisk Extreme 128 GB card at $42.99, with final charges and fulfillment pending. The Jetson kit order remains unconfirmed. Do not repurchase the seven ordered items.

The [budget](hardware/bill_of_materials.md) records the confirmed $1,000 first-year ceiling: all new hardware needed for the end product, required subscriptions and software/distribution fees, tax, and shipping. Reuse the already-owned Mac and iPhone; any new development or test hardware and required renewals during the first year also count toward the ceiling.

The selected first-batch compute target is the complete Orin Nano Super developer kit with 8 GB of included shared working memory. A separate 128 GB SanDisk microSD card supplies storage. A 16 GB configuration belongs to the Orin NX family and requires a complete quote; it is not an extra RAM stick for this kit. Exact local answer, transcription, and voice models still need selection and qualification. See [NVIDIA's module lineup](https://developer.nvidia.com/embedded/jetson-modules).

## Measurement and stop boundaries

Select a small representative workload and freeze the scoring rubric before measured comparisons. Measure transcription errors, answer usefulness, first visible answer latency, completion latency, cold starts, peak app memory, model storage, failures, and offline behavior. Count failed, cancelled, and timed-out attempts; a fast failure is not a fast answer.

Stop or narrow the approach if no local candidate meets the agreed workload within the target phone's resource constraints. Stop a run on an unexpected cloud dependency, unsupported model or language, persistent memory failure, or unresponsive cancellation. Report the failure and decide whether to simplify the task or change the backend. Hardware procurement stays within the remaining project ceiling.

The project can be marked complete when the three iterations have dated, reproducible results; the iOS beta has a recorded launch or no-launch decision; and the Jetson prototype has a device-level operating envelope and total cost account. Closing early requires a conclusion that states the missing evidence.

## Current implementation state

Mac Local Voice 0.2.0 (build 4) extends the [specified Mac development slice](development/README.md) with [manual local speech output](development/local_speech_output.md). The owner confirmed voice input, text answers, and read-aloud. An initial microphone callback crash was repaired and covered by a background-callback regression test.

The [iPhone beta](development/ios_testflight.md), 0.3.0 (build 5), uses the same core and SwiftUI source in a native app target. Seventeen shared automated tests passed, and the iOS simulator completed an authored typed question and manual read-aloud. Local speech recognition was unavailable in that simulator. Apple accepted and processed the signed upload for the internal owner group. The owner then confirmed that the beta works on their iOS device. The TestFlight listing is **Local Voice Lab**; the installed app is **Local Voice**. This is a report of basic operation; the device/OS and individual feature checks are still to be recorded. The [technical status](status.md) records each platform's configuration and evidence limits.

The app handles one question at a time, with no conversation history. English is the current language scope; additional languages are deferred. General conversation is the task family. The tested iPhone/OS and representative evaluation cases remain to be recorded. No structured evaluation on iPhone or run on Jetson has been recorded.

Read the [software guide](software/README.md), [intake](../../resources/project_proposals/apple_local_voice_intake.md), and [results policy](results/README.md) before expanding the implementation. The intake records proposed gates; no latency or quality threshold is a measured result.

## Data handling

Process microphone audio, transcripts, and answers locally. Default to transient audio and session state; retain recordings only for explicitly agreed evaluation. Publish synthetic or approved examples and sanitized measurements. Separate initial app/model downloads from offline interaction testing. Never treat local storage alone as proof of no transmission.
