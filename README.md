<p align="center">
  <img src="resources/assets/longtail-inference-lab-hero.png" alt="Long Tail Inference Lab system diagram" width="100%">
</p>

# Long Tail Inference Lab

A research lab for moving useful intelligence closer to the person: onto local models, local evidence, and local hardware.

## Thesis

A lightweight local model does not need to know everything to become useful. It may need access to compact approved evidence produced by a stronger teacher on separate verified work.

Long Tail Inference Lab's preregistered protocol tests transfer from a fixed `gpt-5.6-sol` cloud teacher and sanitized-evidence distiller to one fixed local Qwen student. The student model stays fixed, approved teacher-derived Markdown memory grows, and held-out executable-verifier M0/M2 pairs decide whether capability improves.

The second question is physical. If local intelligence is worth having, it has to survive the network going away — inside one object, on one battery, within a latency a person will actually wait through. That constraint is measured in seconds, joules, and degrees rather than verifier passes.

## Active projects

Two projects are active, and neither has published a measurement yet. They share a method rather than evidence: fixed controls, an authoritative measurement named before the first run, and published negative results.

### [01 Terminal Artifact Memory](projects/01_terminal_artifact_memory/README.md)

**Status:** Corrective preregistration awaiting merge (zero measured attempts and zero ledger slots consumed)

**Question:** Can verifier-passing public terminal work from a fixed `gpt-5.6-sol` cloud teacher become approved Markdown memory that improves a fixed local Qwen student on disjoint held-out tasks?

The cloud teacher solves only preregistered public memory-build tasks, so that interaction crosses the selected cloud boundary. Its resulting raw capture is retained in ignored local storage and is not retransmitted for distillation; strict local sanitizer, Gitleaks, canary, contamination, and residual gates run before an allowlisted sanitized-evidence packet may be sent to the same model. External human approval scoped to exact hashes is mandatory before admission. The exact local Qwen student is then evaluated under paired M0 (no memory) and M2 (approved Markdown retrieval), with the retrieved-memory block as the only student-context difference.

The executable verifier alone establishes build eligibility and held-out student outcomes. Teacher scores, model confidence, narrative success, tool-exit impressions, and distillation quality never substitute. Private verifier qualification raises confidence in each pinned task verifier without exposing hidden tests or verifier internals to either model.

The teacher boundary pins host Codex CLI 0.146.0, keeps subscription OAuth on the host, exposes only the isolated task tool, and captures ATIF provenance. A pre-measurement dry run exposed an impossible combined Docker/Compose version check, so measurement remains blocked pending a corrective freeze that validates those two exact pins separately; no measured actor or execution-ledger slot was consumed. The earlier genuine pilot remains intact: its first local Qwen M0 probe exceeded the frozen 16,384-token context before executable verification, so it produced no pair or memory checkpoint. See the [halted pilot report](projects/01_terminal_artifact_memory/results/2026-07-31-measured-pilot/summary.md). No teacher/student experiment has been measured yet.

### [02 Edge Offline Intelligence Device](projects/02_edge_offline_intelligence_device/README.md)

**Status:** Specified (hardware not ordered and zero measurements taken)

**Question:** How much useful spoken intelligence fits inside one self-contained device that keeps working when the network disappears?

A push-to-talk voice appliance whose entire conversation path — capture, speech recognition, answer generation, speech synthesis, playback — runs on local hardware with no cloud service, companion phone, or local network server. The device is the stable product boundary; the models are replaceable parts.

The first bounded question is [Experiment 02.1](projects/02_edge_offline_intelligence_device/experiments/01_spoken_latency_and_residency.md). On a fixed Jetson Orin Nano Super 8 GB running a fixed modular pipeline, how is button-release-to-first-spoken-word latency distributed, can all three models be held resident within 8 GB at all, and does residency justify its complexity against sequential load and unload? The experiment runs entirely offline with an interface packet-counter assertion as a ruin boundary, and decomposes every interaction into a per-stage latency ledger so that a slow system names its own bottleneck rather than reporting one opaque number.

Before any hardware is bought, the complete loop runs as a [laptop pilot](projects/02_edge_offline_intelligence_device/software/README.md) on general-purpose hardware. The pilot is a different hardware condition and its output is never pooled with device runs, but it carries the whole controller, the ledger schema, and the analysis unchanged.

No latency, memory, energy, or thermal figure has been measured. Every number in that project is currently a target or a budget.

## PARA organization

```text
projects/
  01_terminal_artifact_memory/
  02_edge_offline_intelligence_device/

areas/
  lab_operations/
  public_website/

resources/
  assets/
  briefs/
  experiment_template/
  learning/
  project_proposals/
```

### Projects

Projects contain active work with a bounded research question, a measurement plan, and a completion condition. There is no cap on how many run at once, so each carries that burden alone and states its measurement status honestly wherever it is listed.

### Areas

Areas are ongoing responsibilities that keep the lab trustworthy, including reproducibility, safety, experiment discipline, result quality, repository maintenance, and public communication.

The [public website](areas/public_website/README.md) is an Area because it remains active as the laboratory evolves.

### Resources

Resources contain reusable learning material, references, proposals, templates, briefs, and media.

GitHub requires workflow configuration under `.github/`. That folder is repository plumbing rather than research content. Its purpose is documented in [`.github/CONFIGURATION.md`](.github/CONFIGURATION.md).

## Experiment lifecycle

```text
Idea → Specified → Running → Analyzing → Complete
```

An experiment is complete only when its baseline, results, interpretation, limitations, and operational conclusion are published.

## Learn through the lab

The active project is designed as a learning module:

1. Separate cloud teacher, cloud distiller, and local student roles.
2. Qualify task verifiers without exposing verifier internals to a model.
3. Build an explicit local-retention and cloud-disclosure boundary.
4. Admit only verifier-passing, sanitized, hash-approved Markdown.
5. Hold exact local Qwen controls fixed while memory grows.
6. Measure positive and negative transfer on disjoint held-out tasks.
7. Publish positive, negative, halted, and inconclusive results.

Start with the [field guide to learning LLM inference](resources/learning/field_guide.md).

## Safety posture

This repository avoids committing private hostnames, IP addresses, SSH details, API keys, tunnel configuration, private prompts, session content, and local machine paths.

Run the safety scan locally:

```bash
python3 areas/lab_operations/safety_scan.py
```

Or run it through pre commit:

```bash
pre-commit run --all-files
```
