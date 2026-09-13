# Long Tail Inference Lab

A research lab for moving useful intelligence closer to the person: onto local models, local evidence, and local hardware.

## Thesis

Useful intelligence should keep working when the network disappears. The lab builds from local applications toward self-contained hardware, measuring the complete interaction and the resources it consumes. Models and runtimes are replaceable parts; usefulness, latency, memory, energy, thermals, and offline integrity determine what to build next.

## Active project

### [02 Edge Offline Intelligence Device](projects/02_edge_offline_intelligence_device/README.md)

**Status:** Native Mac voice input, text answers, and optional local read-aloud work. Following TestFlight delivery of **Local Voice Lab 0.3.0 (build 5)**, the owner confirmed that the beta works on their iOS device. Detailed device evaluation and model-selection intake remain open. Zero published comparative quality or performance measurements for Mac, iPhone, or Jetson.

The project asks whether useful local voice input and text answers can fit an iPhone's constraints, share their model integration with a Mac app, and inform a self-contained NVIDIA device. The **first-year total ceiling is $1,000**, including all new hardware for the end product and required subscriptions, software/distribution fees, tax, and shipping.

| Iteration | Deliverable |
| --- | --- |
| 1. macOS | Native app with local speech transcription, a visible transcript, and a locally generated text answer with optional English read-aloud |
| 2. iOS | The same selected answer backend and shared application logic on iPhone; TestFlight testing, then a conditional launch decision |
| 3. Jetson | A self-contained NVIDIA prototype with its own local recognition, answering, input, output, and power |

The [architecture decision](projects/02_edge_offline_intelligence_device/design_direction.md) proposes evaluating Apple's on-device models first, with an embedded small open model if the target device or tasks require it. The Mac is designed around what the iPhone can use. Apple system models do not run on Jetson; that platform needs an open-model backend and its own validation.

The [Apple development app](projects/02_edge_offline_intelligence_device/software/README.md) accepts voice, displays local text answers, and reads a completed answer aloud only when requested. Seventeen shared automated tests passed. The owner confirmed the Mac interaction, and the native iPhone app completed typed-answer and manual-speech checks in the simulator. Local transcription was unavailable in that simulator. The [technical status](projects/02_edge_offline_intelligence_device/status.md) records the checks, initial crash, repair, completed TestFlight delivery, and physical-phone limits.

The [model-selection intake](resources/project_proposals/apple_local_voice_intake.md) records the broader quality and resource evaluation. English general conversation is the first workload; the target iPhone and representative cases remain open. Additional languages are deferred. Apple is the current development backend, with final model selection pending that evaluation.

The first Jetson stage uses an Orin Nano Super 8 GB, mains power, a listening button, a microphone, and a speaker for local spoken replies. The [shopping list and restart checklist](projects/02_edge_offline_intelligence_device/hardware/portable_procurement.md) records eight items across three stores. The owner confirmed ordering the six DigiKey accessories; the Jetson kit and storage card orders remain unconfirmed. The [project budget](projects/02_edge_offline_intelligence_device/hardware/bill_of_materials.md) records known parts costs and pending final charges. Screen, battery, and portable enclosure are deferred within that same ceiling. Jetson operation and the future battery target remain unmeasured; Mac, iPhone, and Jetson results remain separate.

## PARA organization

```text
projects/     active, bounded research
areas/        shared operations and the public website
resources/    learning material, proposals, templates, and media
archives/     closed, paused, and superseded research records
```

Each project needs a question, a measurement plan, a stop boundary, and a completion condition. Draft experiments remain in resources until their intake is complete. GitHub-required configuration remains under [`.github/`](.github/CONFIGURATION.md).

## Experiment lifecycle

```text
Idea → Specified → Running → Analyzing → Complete
```

A measured experiment is complete when it publishes its baseline, results, interpretation, limitations, and operational conclusion. Work can also be closed before that condition is met, with an explicit account of missing evidence and the decision to stop. Complete, Closed, and Paused work belongs in the archive.

## Learn through the lab

The [field guide](resources/learning/field_guide.md) follows model eligibility, local speech, answer usefulness, shared application design, phone resource constraints, and device measurements. Begin with a small real workload, isolate recognition from answer errors, and test the constrained device early.

## Safety posture

Process voice and answers locally; retain evaluation recordings only under an explicit policy. Publish approved examples and sanitized measurements. Separate setup downloads from offline inference, and verify the network boundary rather than inferring it from local storage.

Use GitHub for durable [technical project memory](areas/lab_operations/public_research_memory.md): decisions, real status, evidence, failures, and open questions. Keep personal or emotional information, private conversations, recordings, screenshots, and raw host logs out of public records.

Run the repository safety scan before committing:

```bash
python3 areas/lab_operations/safety_scan.py
```
