<p align="center">
  <img src="docs/assets/longtail-inference-lab-hero.png" alt="Long Tail Inference Lab system diagram" width="100%">
</p>

# Long Tail Inference Lab

Experiments in edge LLM inference, open weight model serving, laptop plus VPS split inference, and long tail compute across everyday devices.

## Thesis

Open weight models are making inference portable. This lab explores how inference can run, split, route, benchmark, and be verified across the machines we already own: laptops, VPS instances, home servers, and edge devices.

The goal is not to claim that everyday devices replace GPU data centers. The goal is to measure where long tail compute is useful, where the network tax dominates, and which workloads belong on local or distributed inference fabric.

## Experiments

### Documented

| Experiment | Summary |
|---|---|
| [Wiki memory router with knowledge caching](docs/experiment-wiki-memory-router.md) | A markdown wiki as a knowledge cache in front of tiered models. Head questions stay local, tail questions escalate to frontier models, and frontier answers are distilled back into the wiki so the tail shrinks over time. |
| [Session transfer as a capsule](docs/experiment-session-transfer-capsule.md) | Package an inference session (token history, KV cache, sampler state) on one machine and resume it on another. Maps where state transfer, transcript replay, or pinning the session wins. |
| [Agent session capsule complexity](docs/experiment-agent-session-capsule-complexity.md) | Measure what an agent session capsule actually is before building transfer machinery: session sizes, what dominates the bytes, growth over a session's life, and derived state weight. |

### Planned

| Experiment | Summary |
|---|---|
| Local open weight inference baseline | Establish a reference setup and baseline numbers for running open weight models locally. |
| Laptop only benchmark | Measure inference throughput and latency on a laptop alone. |
| VPS only benchmark | Measure inference throughput and latency on a VPS alone. |
| Laptop plus VPS split inference | Split a model across laptop and VPS with llama.cpp RPC and measure the cost of the split. |
| Network tax measurement | Quantify how network latency and bandwidth dominate or disappear across split inference topologies. |
| Job level inference routing | Route whole jobs, rather than layers or tokens, to the device best suited to run them. |
| Quantized model variants for edge inference | Compare quantization levels for quality and speed on constrained edge devices. |
| Edge LLM task evals | Evaluate which real tasks small edge models handle well and where they fall over. |
| Reproducible experiment metadata | Record hardware, model, and configuration metadata so every experiment can be rerun. |
| Device inventory probe | Probe and catalog the compute available across everyday devices. |

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
