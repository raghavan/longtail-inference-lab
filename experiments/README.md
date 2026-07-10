# Experiment Index

Every experiment in the lab lives in its own folder here, with a `README.md` as the writeup and room alongside it for scripts, data, and results. Each experiment carries a status so you can tell at a glance what is an idea, what is being worked on, and what is finished.

## Lifecycle

| Status | Meaning |
|---|---|
| 💡 Proposed | Idea captured; no design yet |
| 📝 Designed | Hypothesis and method written up; not yet run |
| 🔬 Running | Actively collecting results |
| ✅ Completed | Results and learnings written up |
| 🧊 Parked | On hold; the writeup says why |

New experiments start from [TEMPLATE.md](TEMPLATE.md).

## 🔬 Running

None yet.

## 📝 Designed

| Experiment | What it asks | Teaches |
|---|---|---|
| [Wiki memory router](wiki-memory-router/README.md) | Can a markdown wiki act as a knowledge cache in front of tiered models, shrinking the tail over time? | knowledge caching, model routing, retrieval, distillation loops |
| [Session transfer capsule](session-transfer-capsule/README.md) | Can an inference session be packaged and resumed on another machine faster than replaying it? | KV cache internals, llama.cpp session state, transfer vs replay economics |
| [Agent session capsule complexity](agent-session-capsule-complexity/README.md) | How large are agent sessions, what dominates their bytes, and what would their derived state weigh? | agent session anatomy, measurement-before-design |

## 💡 Proposed

Ideas captured but not yet designed. Each becomes a folder here when the design work starts.

| Experiment | What it asks |
|---|---|
| Local open weight inference baseline | What does a reproducible local inference baseline look like on hardware we already own? |
| Laptop only benchmark | What throughput and latency does a laptop deliver across model sizes and quantizations? |
| VPS only benchmark | What does a modest VPS deliver, and at what cost per token? |
| Laptop plus VPS split inference | Does splitting a model across laptop and VPS with llama.cpp RPC ever beat either alone? |
| Network tax measurement | How much does the network erase the gains of distributing inference? |
| Job level inference routing | Which whole jobs (not layers) are worth routing to which device? |
| Quantized model variants for edge inference | Which quantization levels keep quality acceptable on edge hardware? |
| Edge LLM task evals | Which real tasks do small local models actually handle well? |
| Reproducible experiment metadata | What metadata must every run capture so results can be trusted and compared? |
| Device inventory probe | How do we characterize the compute, memory, and network of the devices in the fleet? |

## ✅ Completed

None yet — this section is the goal.
