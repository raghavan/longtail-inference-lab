# 02 Edge Offline Intelligence Device

**Status:** Specified — hardware not ordered, zero measurements taken
**Track:** Edge inference and device systems
**Difficulty:** Advanced
**Last updated:** August 9 2026

## One minute summary

**Question:** How much useful spoken intelligence fits inside one self-contained device that keeps working when the network disappears?

**Object under study:** a push-to-talk voice appliance whose entire conversation path — capture, speech recognition, answer generation, speech synthesis, playback — runs on local hardware with no cloud service, companion phone, or local network server.

**Current evidence:** none. No hardware has been ordered and no measurement has been taken. Every number in this project is a target or a budget until a results file says otherwise.

**Why it is a project rather than an experiment:** the device only becomes real when latency, memory, energy, thermals, audio quality, and physical interaction behave as one appliance. Each of those is a separate bounded experiment. This folder holds the charter; `experiments/` holds the bounded questions.

## Decisions already taken

| Decision | Choice | Date | Basis |
| --- | --- | --- | --- |
| Compute tier | Jetson Orin NX 16 GB (Super) rather than the Orin Nano Super 8 GB | August 9 2026 | Owner decision to buy the higher tier directly |
| Interaction model | Push to talk, half duplex, no wake word in the first version | August 9 2026 | Design direction: lower idle power, clearer turn boundaries, no continuous speech processing |
| Model architecture | Separate speech recognition, answer generation, and speech synthesis models | August 9 2026 | Design direction: memory control, replaceability, per-stage benchmarking |
| First bounded question | Spoken response latency and residency policy | August 9 2026 | Recalibrated below |

### Consequence of buying the higher tier

The design direction framed memory contention as the leading technical risk, because three models competing for 8 GB is genuinely tight. Buying 16 GB substantially relieves that risk before it is ever measured, which changes what the first experiment should ask.

The sharp question is no longer *do the models fit*. It is **what does the extra memory actually buy in the only currency the user experiences: the delay between releasing the button and hearing the first word.**

That reframing has an uncomfortable corollary the project should accept in advance: if the sequential-loading baseline meets the latency target on its own, then residency bought nothing, and the honest conclusion is that the 8 GB part would have been sufficient. The first experiment is designed so that outcome is visible rather than obscured.

## First bounded experiment

**[Experiment 02.1 — Spoken response latency and residency policy](experiments/01_spoken_latency_and_residency.md)**

Does keeping speech recognition, answer generation, and speech synthesis simultaneously resident — which 16 GB permits and 8 GB does not — reduce button-release-to-first-spoken-word latency enough to justify the complexity, compared with sequential load and unload?

The experiment is a 2×2: residency policy (sequential, resident) crossed with speech synthesis policy (whole answer, sentence streamed). It runs entirely offline with an egress counter asserting zero outbound packets, and it decomposes every interaction into a per-stage latency ledger so the result names the component to fix rather than reporting one opaque number.

## What this project is deliberately not building yet

1. No wake word.
2. No enclosure.
3. No battery, until the desk prototype has a measured power profile to size it against.
4. No offline knowledge retrieval, until the basic voice loop is dependable.
5. No conversation memory beyond the current session.
6. No tool calling, smart home control, or agent framework.
7. No custom audio hardware bring-up inside the first experiment. See the audio decoupling note below.

Each item above is a cost. The design direction treats every visible feature as a cost, and this project holds that line.

### Audio decoupling note

The design direction proposes the M5Stack Atom VoiceS3R as the smallest integrated audio front end, and asks whether it can act as a direct USB audio device attached to the Jetson.

Public specifications describe it as an ESP32-S3 device with an I2S codec, not a native USB audio class peripheral, so attaching it as a plug-and-play sound card is likely to require custom firmware rather than a cable. That is a real research question, but it is a *different* research question from latency.

Bringing up bespoke audio firmware inside the latency experiment would confound the primary measurement: an unexplained 300 ms would have two candidate causes and no way to separate them. So Experiment 02.1 uses a known-good USB audio path as a reference instrument, and the tiny module becomes its own bounded experiment once the latency baseline exists.

## Phase map

| Phase | Goal | Gate to the next phase |
| --- | --- | --- |
| 1. Desk prototype | Complete offline voice loop on mains power with reference audio | Experiment 02.1 publishes a latency, memory, energy, and offline-integrity baseline |
| 2. Tiny audio integration | Atom VoiceS3R as the capture and playback path | Word error rate and intelligibility within a defined margin of the reference path |
| 3. Portable power | Certified battery pack and regulated power path | Peak inference load sustained without brownout; measured conversations per charge |
| 4. Enclosure | One object, one control, hidden machinery | Safe surface temperature under sustained load |
| 5. Daily use pilot | Weeks of ordinary use | Recorded preference, failures, and abandonment against a phone |

Phases do not begin because the previous one felt finished. Each begins when the previous phase has published measurements against its gate.

## Structure

```text
projects/02_edge_offline_intelligence_device/
  README.md                                    this charter
  design_direction.md                          full systems and product direction
  experiments/
    01_spoken_latency_and_residency.md         first bounded experiment
  hardware/
    bill_of_materials.md                       what to order, with links and risks
  results/
    README.md                                  published measurements
```

## Safety, privacy, and publication rules

1. Voice data collected during development stays local. Only synthetic or explicitly approved recordings may be committed.
2. The scripted question set is public and authored by the operator, so no third-party voice is captured.
3. Raw audio is discarded after transcription unless development mode is explicitly enabled, and development mode must be recorded in the run metadata.
4. No private hostnames, network configuration, serial numbers, or local machine paths enter this repository. Run `python3 areas/lab_operations/safety_scan.py` before committing.
5. A physical microphone mute, once fitted, overrides all software behavior.

## Relationship to the lab thesis

Project 01 asks whether a small local model can borrow capability from verified work done elsewhere. This project asks the physical version of the same question: how much capability can be carried, owned, and relied upon when nothing else is reachable.

The two share a discipline rather than a protocol. Both fix their controls, name their authoritative measurement in advance, and publish negative results. Neither borrows the other's evidence.
