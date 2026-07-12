# A Field Guide to Learning LLM Inference

Running language models on laptops, modest servers, and small clusters sits at the intersection of model architecture, numerical methods, systems performance, retrieval, evaluation, and distributed systems.

This guide uses the active experiment as a practical anchor. The goal is not to collect links. It is to build systems intuition through measured work.

## Learning path

### 1. Inference arithmetic

Learn how model weights, context length, KV state, memory bandwidth, prompt processing, and token generation affect latency and memory use.

Recommended starting points:

1. Transformer Inference Arithmetic by kipply.
2. Making Deep Learning Go Brrrr From First Principles by Horace He.
3. The Modal GPU Glossary.

### 2. Efficient local inference

Study quantization, CPU and GPU offload, memory mapped weights, batching, context management, and runtime design.

Useful systems to inspect:

1. llama.cpp.
2. MLX.
3. vLLM.
4. Ollama.

The active experiment freezes these choices during its core learning curve. That prevents a model or runtime upgrade from being mistaken for a memory improvement.

### 3. Terminal benchmarks and verification

Study how a terminal benchmark defines an isolated environment, a task, an allowed action surface, and an executable verifier.

Important questions include:

1. Does the verifier measure the outcome that matters?
2. Can hidden tests leak into model context?
3. Are task families genuinely independent?
4. Does the benchmark reward a brittle shortcut?
5. Which tasks represent recurring engineering patterns?
6. Which actions would be unsafe outside the sandbox?

Executable verification is stronger than stylistic answer grading, but it still requires contamination checks and careful interpretation.

### 4. Artifact memory

Follow [Experiment 01: Terminal Artifact Memory](../../projects/01_terminal_artifact_memory/README.md).

Study how completed work becomes:

1. Sanitized terminal evidence.
2. Command and outcome pairs.
3. Failure signatures.
4. Environment facts.
5. Verified resolutions.
6. Distilled Markdown pages.
7. Searchable indexes.
8. Provenance and freshness metadata.

The central experimental control is simple:

> The model stays fixed. The memory grows.

This makes it possible to measure whether accumulated verified work creates capability lift without changing model weights.

### 5. Retrieval and ranking

Begin with lexical retrieval before adding embeddings or learned ranking.

Learn:

1. BM25 and inverted indexes.
2. Embedding similarity.
3. Hybrid retrieval.
4. Reranking.
5. Retrieval precision and recall.
6. Context budget allocation.
7. Contradiction detection.
8. Staleness and supersession.

A sophisticated retriever is not automatically better. Removal tests should determine whether it changes the operational decision.

### 6. Evaluation and local sufficiency

Separate authoritative outcomes from learned predictions.

Authoritative outcomes may include:

1. Executable verifier pass.
2. Deterministic expected fact checks.
3. Evidence support.
4. Absence of prohibited actions.
5. Appropriate abstention.

A small regression model can then estimate the probability that a local answer will succeed. It should not replace the verifier.

Study calibration, held out task family evaluation, false local routing, unnecessary escalation, confidence intervals, and unsafe confident errors.

### 7. Distributed inference and routing

Distributed execution, frontier escalation, and cross device state remain possible future directions.

They should follow evidence rather than precede it. First determine:

1. Whether artifact memory creates meaningful local lift.
2. Where the lift stops.
3. Which tasks remain in the tail.
4. Whether local sufficiency can be predicted safely.
5. Whether the network or frontier cost is large enough to justify routing machinery.

Relevant systems and communities include llama.cpp RPC, exo, Petals, GPU MODE, and LocalLLaMA.

## Practitioners to follow

### Systems and performance

1. Georgi Gerganov for llama.cpp and ggml.
2. Tri Dao for attention and kernel efficiency.
3. Tim Dettmers for quantization and practical hardware analysis.
4. Horace He for compiler and performance reasoning.
5. Awni Hannun for MLX and Apple silicon inference.
6. Song Han for efficient deep learning.
7. Alex Cheema for distributed inference across everyday devices.

### Analysis and ecosystem

1. Nathan Lambert for the open model ecosystem.
2. Sebastian Raschka for code backed model explanations.
3. Simon Willison for practical local model experimentation.
4. Andrej Karpathy for first principles learning artifacts.
5. Chip Huyen for production evaluation and serving.

## Structured study

1. MIT 6.5940 for efficient deep learning and TinyML.
2. CMU 10 414 for deep learning systems.
3. Stanford CS336 for language modeling from scratch.
4. GPU MODE lectures for GPU programming and kernels.
5. Neural Networks: Zero to Hero for first principles foundations.

## How to use this repository as a course

For the active project:

1. Read the research question.
2. Predict the no memory baseline.
3. Explain every metric in your own words.
4. Inspect the artifact schema.
5. Reproduce the first three task pilot.
6. Compare raw evidence with distilled memory.
7. Examine every false local answer.
8. Remove one component and measure what changes.
9. Record one limitation.
10. Propose the smallest next question justified by evidence.
