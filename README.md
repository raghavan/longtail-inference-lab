<p align="center">
  <img src="docs/assets/longtail-inference-lab-hero.png" alt="Long Tail Inference Lab system diagram" width="100%">
</p>

# Long Tail Inference Lab

Experiments in edge LLM inference, open weight model serving, laptop plus VPS split inference, and long tail compute across everyday devices.

## Thesis

Open weight models are making inference portable. This lab explores how inference can run, split, route, benchmark, and be verified across the machines we already own: laptops, VPS instances, home servers, and edge devices.

The goal is not to claim that everyday devices replace GPU data centers. The goal is to measure where long tail compute is useful, where the network tax dominates, and which workloads belong on local or distributed inference fabric.

## How this repo is organized

The lab is organized as a series of experiments, each moving through a lifecycle:

**💡 Proposed → 📝 Designed → 🔬 Running → ✅ Completed** (or 🧊 Parked)

| Where | What you'll find |
|---|---|
| [**experiments/**](experiments/README.md) | The experiment index — every experiment by status, one folder each with writeup, scripts, and results |
| [**learning/**](learning/README.md) | A field guide to learning LLM inference: the people, essays, courses, and communities behind this field |
| [**docs/**](docs/) | Lab-wide documentation, such as the [safety scan](docs/safety-scan.md) |

**Start with the [experiment index](experiments/README.md)** to see what is new, in progress, and completed. Each experiment writeup states what it asks, what you can learn from it, and how to reproduce it. If you are new to LLM inference itself, start with the [field guide](learning/README.md) instead.

## Currently designed experiments

- [Wiki memory router with knowledge caching](experiments/wiki-memory-router/README.md) — a markdown wiki as a knowledge cache in front of tiered models
- [Session transfer as a capsule](experiments/session-transfer-capsule/README.md) — packaging inference sessions to resume on another machine
- [Agent session capsule complexity](experiments/agent-session-capsule-complexity/README.md) — measuring what agent sessions weigh before building transfer machinery

Ten more proposed experiments — baselines, benchmarks, split inference, routing, and quantization — are queued in the [index](experiments/README.md#-proposed).

## Contributing an experiment

Copy [experiments/TEMPLATE.md](experiments/TEMPLATE.md) into a new folder under `experiments/`, add it to the index, and keep the status line current as it moves through the lifecycle.

## Safety posture

This repo intentionally avoids committing private hostnames, IP addresses, SSH details, API keys, tunnel configuration, private prompts, and local machine paths. A lightweight safety scan is included for local pre commit usage and CI.

Run locally:

```bash
python3 scripts/safety_scan.py
```

Or with pre commit:

```bash
pre-commit run --all-files
```
