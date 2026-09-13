# A Field Guide to Local Voice Applications and Devices

The [Edge Offline Intelligence Device](../../projects/02_edge_offline_intelligence_device/README.md) develops through a Mac app, an iPhone app, and a Jetson prototype. The Mac development slice works, basic iOS TestFlight operation is owner-confirmed, and [portable Jetson sourcing](../../projects/02_edge_offline_intelligence_device/hardware/portable_procurement.md) is in progress. There are zero published comparative quality or performance measurements for these iterations. This guide explains how to turn that sequence into evidence about useful local inference.

## 1. Trace the interaction

Follow microphone capture → local transcription → local answer generation → rendered text. The first app shows both transcript and answer, so recognition errors can be distinguished from answer errors. Record the end of speech capture, final transcript, first visible answer, and final rendered answer.

First-token timing omits recognition and rendering. Measure the full interval the person waits, and record model-only timing separately. The [software plan](../../projects/02_edge_offline_intelligence_device/software/README.md) defines the initial scope.

## 2. Understand what can be shared

Mac and iPhone can share application logic, prompt policy, evaluation cases, and the selected model integration. Apple system models are managed by the OS; identical weights across devices cannot be assumed. An open model can use the same frozen file and quantization, while accelerator and runtime behavior still vary.

Jetson needs a Linux platform layer and local open models. Reuse an interaction contract and evaluation evidence carefully; platform portability does not imply equal performance. The [architecture decision](../../projects/02_edge_offline_intelligence_device/design_direction.md) links the supporting Apple and runtime documentation.

## 3. Separate the resource measurements

App download size, persistent model files, shared system assets, peak app memory, and total device memory are different quantities. Apple-owned assets can reduce app packaging work while still consuming device resources. Open weights add context caches, runtime buffers, and audio/UI overhead when loaded.

The iPhone establishes the Apple app's practical limits. A model that fits the Mac has not yet passed a phone test. Observe cold starts, interruptions, memory pressure, and thermal behavior on the physical device.

## 4. Measure usefulness before expanding

Start with a small set of real intended tasks and a fixed scoring rubric. Test correct transcripts directly, then speech recordings of the same requests. If an answer fails both, investigate the answer model or task scope; if it fails only after speech recognition, investigate the transcript and audio conditions.

Prefer the smallest tested configuration that meets the workload. Parameter count is a cost signal, not a quality score. Record unsupported questions and explicit limitations alongside successful answers. The [intake draft](../project_proposals/apple_local_voice_intake.md) gives the proposed comparison and thresholds.

## 5. Make the offline claim precise

Initial app delivery and speech/model downloads can require connectivity. After setup, disable networking and test a full interaction. Inspect the app's dependencies and network behavior as the platform permits. An unavailable model must produce a clear local error.

An app's offline behavior does not imply that every unrelated OS service sends zero packets. Document the boundary being measured. Keep raw recordings transient unless retention is explicitly part of the evaluation.

## 6. Publish distributions and decisions

Report sample count, median, p95, maximum, and failed attempts. Keep cold and warm observations separate. A small pilot gives an unstable p99 estimate; state that uncertainty. Analyze the slow interactions themselves rather than adding unrelated stage percentiles.

Mac results, physical iPhone results, TestFlight feedback, and Jetson energy/thermal measurements answer different questions. Publish each separately, with the next operational decision and the limits of transfer. The [results policy](../../projects/02_edge_offline_intelligence_device/results/README.md) defines the expected evidence.
