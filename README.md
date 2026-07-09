<p align="center">
  <img src="docs/assets/longtail-inference-lab-hero.png" alt="Long Tail Inference Lab system diagram" width="100%">
</p>

# Long Tail Inference Lab

Experiments in edge LLM inference, open weight model serving, laptop plus VPS split inference, and long tail compute across everyday devices.

## Thesis

Open weight models are making inference portable. This lab explores how inference can run, split, route, benchmark, and be verified across the machines we already own: laptops, VPS instances, home servers, and edge devices.

The goal is not to claim that everyday devices replace GPU data centers. The goal is to measure where long tail compute is useful, where the network tax dominates, and which workloads belong on local or distributed inference fabric.

## Initial experiments

- Local open weight inference baseline
- Laptop only benchmark
- VPS only benchmark
- Laptop plus VPS split inference with llama.cpp RPC
- Network tax measurement
- Job level inference routing
- Quantized model variants for edge inference
- Edge LLM task evals
- Reproducible experiment metadata
- Device inventory probe
- [Wiki memory router with knowledge caching](docs/experiment-wiki-memory-router.md)
  - [Implementation note: pi agent harness](docs/experiment-wiki-memory-pi-harness.md)

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
