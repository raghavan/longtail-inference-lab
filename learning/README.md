# A Field Guide to Learning LLM Inference

Running large language models outside the datacenter — on laptops, single-board computers, modest VPS instances, and ad-hoc clusters of everyday devices — sits at the intersection of several disciplines: GPU and CPU systems programming, numerical methods like quantization, distributed systems, and the fast-moving ecosystem of open-weight models. No single textbook covers it. The field advances through blog posts, GitHub pull requests, lecture series released for free, and a handful of unusually good online communities.

This chapter maps that landscape. It introduces the practitioners whose work defines the field, the essays and blogs that serve as its de facto literature, the courses that provide structured foundations, and the communities where the state of the art is discussed daily. It closes with a suggested path through all of it.

## The Practitioners

The clearest signal in this field comes from following individual people rather than institutions. A short list of names accounts for a remarkable share of the progress in efficient and edge inference.

### Systems and Performance

**Georgi Gerganov** created [llama.cpp](https://github.com/ggml-org/llama.cpp) and the ggml tensor library that underpins it, almost single-handedly making serious LLM inference on consumer hardware a reality. The llama.cpp repository is itself a running seminar: its pull requests document, in working code, nearly every technique that matters for edge inference — quantization formats, KV-cache management, speculative decoding, and CPU/GPU offloading among them.

**Tri Dao** is the author of FlashAttention and a co-creator of the Mamba architecture. His papers set the pace for attention and kernel efficiency, and reading them in sequence is one of the better ways to understand why modern inference is fast.

**Tim Dettmers** built the bitsandbytes library and co-authored QLoRA. His research made low-bit quantization practical, and his long-form guide to choosing GPUs for deep learning remains the canonical reference for hardware decisions on a budget.

**Horace He** works on the PyTorch compiler stack. His essay ["Making Deep Learning Go Brrrr From First Principles"](https://horace.io/brrr_intro.html) is required reading: it teaches the compute-bound versus memory-bound mental model that underlies all inference optimization.

**Awni Hannun** leads [MLX](https://github.com/ml-explore/mlx), Apple's array framework for machine learning on Apple silicon. For anyone whose "edge device" is a MacBook, MLX and its surrounding community are the frontier.

**Song Han** runs the MIT HAN Lab, the academic home of efficient deep learning. Techniques that began as papers from his group — AWQ, SmoothQuant, StreamingLLM — now ship in mainstream inference engines.

**Charles Frye** writes about GPU computing at Modal and authored much of the [GPU Glossary](https://modal.com/gpu-glossary), one of the most approachable entry points into GPU architecture and terminology.

**Alex Cheema** co-founded exo labs, whose open-source [exo](https://github.com/exo-explore/exo) project pursues a thesis directly relevant to this repository: aggregating everyday devices — phones, laptops, mini PCs — into a single inference cluster.

### Analysis and Ecosystem

**Dylan Patel** publishes [SemiAnalysis](https://semianalysis.com), the most-cited source on the hardware and economics of AI compute. Understanding why inference costs what it does starts here.

**Nathan Lambert** writes [Interconnects](https://www.interconnects.ai), the best ongoing chronicle of the open-weight model ecosystem — which models matter, which licenses matter, and where the open-versus-closed gap actually stands.

**Sebastian Raschka** writes [Ahead of AI](https://magazine.sebastianraschka.com), known for patient, code-backed deep dives into model architectures and efficiency techniques.

**Simon Willison** maintains a [prolific blog](https://simonwillison.net) with a relentlessly practical bent; his running coverage of local models documents what it is actually like to use them on ordinary hardware.

**Andrej Karpathy** builds teaching artifacts — nanoGPT, llm.c — that strip language models down to their essentials. There is no better source for from-scratch intuition about what an inference engine ultimately has to do.

## Essential Reading

A few essays function as the field's core literature and reward careful study.

- **["Transformer Inference Arithmetic"](https://kipp.ly/transformer-inference-arithmetic/)** by kipply teaches the back-of-the-envelope math of inference: KV-cache sizes, memory-bandwidth limits, and why batch size changes everything. It is the single best starting point in the field.
- **[Artificial Fintelligence](https://www.artfintel.com)** by Finbarr Timbers continues in the same spirit, with quantitative essays on inference economics and engine design.
- **["Large Transformer Model Inference Optimization"](https://lilianweng.github.io/posts/2023-01-10-inference-optimization/)** by Lilian Weng is the canonical survey of the optimization landscape — distillation, quantization, pruning, sparsity, and architectural tricks in one place.
- **The [vLLM blog](https://blog.vllm.ai)** documents the ideas — PagedAttention, continuous batching — that define modern high-throughput serving.
- **The [PyTorch blog](https://pytorch.org/blog/)** covers `torch.compile` and projects like GPT-fast, which show how far pure-PyTorch inference can be pushed.
- **The [GPU Glossary](https://modal.com/gpu-glossary)** from Modal is a dictionary-style reference for filling gaps in GPU vocabulary as they appear.
- **Chip Huyen's [blog](https://huyenchip.com/blog/)** and her book *AI Engineering* supply the production-serving perspective: latency budgets, evaluation, and the realities of running models for users.
- **[SemiAnalysis](https://semianalysis.com)**, noted above, is the reference for hardware supply, datacenter buildout, and inference cost modeling.

## Courses and Structured Study

Blog posts provide the field's news; these courses provide its foundations. All are available free online.

- **[GPU MODE lectures](https://www.youtube.com/@GPUMODE)** — a community-run lecture series on CUDA and GPU kernel programming, best paired with the textbook *Programming Massively Parallel Processors* (Kirk & Hwu), which the community reads together.
- **[MIT 6.5940: TinyML and Efficient Deep Learning Computing](https://hanlab.mit.edu/courses/2024-fall-65940)** (Song Han) — quantization, pruning, distillation, and on-device inference. Of everything listed here, this course is the closest match to edge LLM inference as a subject.
- **[CMU 10-414: Deep Learning Systems](https://dlsyscourse.org)** (Tianqi Chen et al.) — build a deep learning framework from scratch, including automatic differentiation and hardware acceleration. Excellent for understanding what inference engines do beneath the API.
- **[Stanford CS336: Language Modeling from Scratch](https://stanford-cs336.github.io/)** — a full pass through building language models, with real systems and inference-efficiency assignments.
- **[Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html)** (Andrej Karpathy) — the from-scratch foundation to take first if backpropagation and transformers are not yet second nature.

## Communities

The day-to-day conversation of the field happens in a few places.

- **[r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/)** is the town square of local and open-weight inference. New quantizations, benchmark results, and hardware configurations surface here before anywhere else.
- **The [GPU MODE Discord](https://discord.gg/gpumode)** is the best venue for kernel and performance questions, with active reading groups and working-group channels.
- **[llama.cpp GitHub Discussions](https://github.com/ggml-org/llama.cpp/discussions)** carry high-signal threads on edge-device specifics; the project's RPC backend is directly relevant to splitting inference between a laptop and a remote server.
- **The [exo](https://github.com/exo-explore/exo) and [Petals](https://github.com/bigscience-workshop/petals) projects** are where distributed and split inference across heterogeneous devices is actually being built; their issue trackers and community channels are the niche's meeting place.
- **The [EleutherAI Discord](https://www.eleuther.ai)** and **[Hugging Face community](https://huggingface.co)** cover the broader open-model ecosystem, and the **[MLX community on GitHub](https://github.com/ml-explore/mlx/discussions)** is the gathering point for inference on Apple silicon.

## A Suggested Path

A reader starting from general programming ability could do worse than the following sequence. Begin with kipply's "Transformer Inference Arithmetic" and Horace He's "Go Brrrr" essay to acquire the field's two core mental models: inference math and the memory-versus-compute dichotomy. Work through the MIT 6.5940 lectures for a structured treatment of quantization and on-device efficiency, dipping into GPU MODE lectures when kernel-level questions arise. Throughout, lurk in r/LocalLLaMA and the GPU MODE Discord — much of this field's knowledge is ambient and picked up by osmosis. Finally, study working systems: read llama.cpp pull requests, and examine how its RPC mode and the exo project partition a model across machines. That combination — arithmetic, coursework, community, and source code — covers the theory and practice of longtail inference end to end.
