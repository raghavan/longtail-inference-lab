# A Field Guide to Learning LLM Inference

Running language models on laptops, modest servers, and small clusters sits at the intersection of model architecture, numerical methods, systems performance, distributed systems, and evaluation.

This guide provides a path through those subjects using the experiments in this repository as practical anchors.

## Learning path

### 1. Inference arithmetic

Learn how model weights, context length, KV state, memory bandwidth, prompt processing, and token generation affect latency and memory use.

Recommended starting points:

1. Transformer Inference Arithmetic by kipply.
2. Making Deep Learning Go Brrrr From First Principles by Horace He.
3. The Modal GPU Glossary.

### 2. Efficient local inference

Study quantization, CPU and GPU offload, memory mapped weights, batching, and runtime design.

Useful systems to inspect:

1. llama.cpp.
2. MLX.
3. vLLM.
4. Ollama.

### 3. Durable knowledge and routing

Study retrieval, confidence, escalation, caching, and evaluation. Then follow [Experiment 01: Memory Wiki](../../projects/01_memory_wiki/README.md).

The important question is not whether local inference is cheaper. It is whether the system can recognize when local inference is good enough.

### 4. Context and session state

Study token histories, instructions, tool output, KV state, compression, replay, and continuation. Then follow [Experiment 02: Session Capsule Analysis](../../projects/02_session_capsule_analysis/README.md).

The important question is not whether state can be moved. It is whether measurements show that moving state is worth the complexity.

### 5. Distributed inference

After the first two experiments produce evidence, study job routing, model partitioning, network tax, failure recovery, and heterogeneous hardware.

Relevant projects and communities include llama.cpp RPC, exo, Petals, GPU MODE, and LocalLLaMA.

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

For each project:

1. Read the research question.
2. Reproduce the baseline.
3. Explain every metric in your own words.
4. Predict the result before running it.
5. Compare the prediction with the measurement.
6. Record one limitation.
7. Propose one smaller next experiment.

The goal is not to collect links. The goal is to build systems intuition through measured experiments.
