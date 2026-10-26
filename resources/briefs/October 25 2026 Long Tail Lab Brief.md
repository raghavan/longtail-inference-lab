# Long Tail Lab Brief

**Edition:** October 25 2026  
**Reading time:** About 30 minutes  
**Editorial question:** What would make the first offline Jetson voice result trustworthy, and which insights from memory, runtime state, and security should remain design notes rather than new features?

## The laboratory checkpoint

The current [README](../../README.md) identifies one active project, [Edge Offline Intelligence Device](../../projects/02_edge_offline_intelligence_device/README.md). Its Mac application has demonstrated a native voice to text answer interaction. The iPhone TestFlight beta has owner reported basic operation, but its representative task evaluation is incomplete. The [Linux voice application](../../projects/02_edge_offline_intelligence_device/software/jetson/README.md) has 38 passing tests and real offline inference in an Ubuntu ARM64 CPU virtual machine. These are development results, **not physical Jetson benchmarks**.

The [public issue for Jetson qualification](https://github.com/raghavan/longtail-inference-lab/issues/47) remains open. Its latest documented checkpoint says the first hardware batch was ordered, not received or accepted. No open pull requests were found on October 25, and the latest repository commit before this edition added the [October 11 reading brief](October%2011%202026%20Long%20Tail%20Lab%20Brief.md) on October 12. The latest implementation commit remains the September 16 Linux development slice. The [Apple model selection intake](../project_proposals/apple_local_voice_intake.md) still lacks a completed physical phone workload and scoring record. Do not infer that the ordered device has arrived or that published comparative latency, quality, memory, thermal, or energy results exist.

The Linux answer path currently pins **Qwen2.5 1.5B Instruct Q4_K_M**, Whisper tiny.en, and eSpeak NG. It uses a single question with no conversation history, retrieval, external actions, or network fallback. This edition therefore puts physical measurement first. The other readings are useful tests of future assumptions, not a request to expand the application. All new papers below are author reported preprints. Four sources were released October 14 to October 21, two on October 9 and 10, with one older operating systems reference; the six selections comprise five recent papers and one foundational document.

## 1. The energy cost of an answer has a fixed part and a growing part

**Source:** [Seeing at the Edge: Energy Characterization of Vision-Language Model Inference on Edge Platforms](https://arxiv.org/abs/2610.20136), submitted October 14 2026.

**What it is.** This study measures input side, total system energy, latency, and sustained thermal behavior for text and vision language workloads on a Raspberry Pi 5 with Hailo hardware and a **Jetson Orin Nano Super**. It separates fixed request energy from incremental output token energy. The authors report that their compared Jetson GPU stack favors shorter outputs while their Pi NPU stack favors longer ones, with a crossover near 40 output tokens **for those particular models and deployment stacks**. The study explicitly warns that different quantization and serving systems prevent a silicon only comparison.

**Why it matters here.** This is unusually close to the lab's planned Jetson hardware, but it is not the same voice pipeline. The transferable method is stronger than the reported winner: measure complete input power rather than equating a module power rail with wall power, separate cold setup from warm requests, control prompt cache reuse, and label the fixed cost of each interaction separately from decode work. The Mac, iPhone, and Jetson must still have independent records.

**Read or inspect.** Sections **IV-A** (power instrumentation), **IV-C** (warmup, cache guards, temperature and pairing), **V-D**, **V-G**, **V-H**, **V-I**, and **VI** (limits of comparison).

**Experiment or design question.** For a frozen set of authored text prompts on the qualified physical Jetson, does complete press to spoken answer duration change approximately linearly with answer length, or do recognition, audio startup, and thermal state dominate? If only software rail telemetry is available, mark it as partial power evidence rather than total system Joules.

## 2. A compression benchmark can accidentally avoid the compressed state

**Source:** [EdgeLLM-Nano: Auditing Polar-Guided Key-Cache Compression and Consistency-Anchored Pruning on a 33.6 MB On-Device Language Model](https://arxiv.org/abs/2610.14475), submitted October 10 2026.

**What it is.** An 8.39 million parameter testbed examines KV cache quantization and pruning with controls. The authors show that their single shot perplexity procedure gives the same score across cache variants because it does not exercise the modified cache. Their Long-Context Decode Fidelity protocol does exercise that cache and exposes differences. On their Raspberry Pi 5 testbed, the tested compression backends also consumed more energy per token than the uncompressed baseline. This is a small model and a limited workload, not a forecast for Qwen2.5 on Jetson.

**Why it matters here.** The lab values reproducible open weight inference. A technically valid benchmark number can still answer the wrong question. Before discussing KV compression or lower bit arithmetic, verify that the actual tested inference path uses the altered state, and record energy and latency overhead as well as saved bytes. The current single turn, 2,048 token context does not establish a KV memory bottleneck.

**Read or inspect.** Sections **III-A** (LCDF definition), **IV** (controls), **V-C** and **V-D** (cache comparisons), **V-F** (Pi power and latency), and **VI** (threats to validity).

**Experiment or design question.** Can a tiny, authored regression fixture prove that a purported runtime or cache optimization is exercised during autoregressive decode, rather than merely passing a model load or perplexity check? Do not introduce a new cache backend until the existing one has a physical memory profile.

## 3. A memory index should point to evidence, not silently become evidence

**Source:** [Multimodal Filesystem Memory for Long-Horizon Embodied Agents](https://arxiv.org/abs/2610.22686), submitted October 15 2026.

**What it is.** The authors organize episodic observations, an index with pointers, and agent written knowledge in a filesystem. Index cues retrieve the underlying episodes when compact notes omit details. They evaluate the approach on long horizon Minecraft and computer use tasks; those reported task results are not local voice results.

**Why it matters here.** The historical **Memory Wiki** question was whether reviewed knowledge can prevent unnecessary generation, while **Session Capsule Analysis** asked what state is actually portable. This work sharpens a distinction: a short retrieval cue is a *locator*, not proof that a derived statement is true. Equally important, its raw episode retention is inappropriate to copy into the current voice product. The lab's public memory policy and local transient audio boundary take priority over this architecture.

**Read or inspect.** Sections **3.2** (three stores), **3.3** (cue to evidence retrieval), **3.4** (consolidation), **4.3** (ablations), and **6** (limitations).

**Experiment or design question.** On fully authored, nonsensitive example records outside the live voice path, can a compact index plus evidence pointer answer questions that a same size prose summary misses? Measure unsupported answers and dangling pointers, and require deletion to invalidate all derived references.

## 4. Distributed state can make the network part of the critical path

**Source:** [SAKURA: Serving Attention Key-Value State Under Rate Adaptation for Private Image Editing on Phones](https://arxiv.org/abs/2610.29733), submitted October 21 2026.

**What it is.** For phone based diffusion image editing, SAKURA studies keeping request specific computation on device while serving reusable attention state from another location. The authors compress state according to a bandwidth budget and overlap transfer, reconstruction, and inference. They report latency and storage gains against their selected image editing baselines on a Snapdragon phone. This is **not an LLM voice serving benchmark**.

**Why it matters here.** The original heterogeneous compute research asked whether network transfer erases remote compute benefits. SAKURA supplies a more precise decomposition: remote state may save local storage yet increase first response delay, especially as available bandwidth changes. It also illustrates a privacy distinction between reusable templates and request specific inputs. The current Local Voice design is strictly offline and therefore **must not** adopt cloud cache delivery.

**Read or inspect.** The paper's **system architecture and cache representation**, **bandwidth adaptation and pipelined execution**, then its **network sensitivity experiments** and limitations.

**Experiment or design question.** In a separate future, synthetic job routing study, what is the break even transfer size when network variance and cache reconstruction time are included? Which state, if any, is public enough to cross the [proposed privacy boundary](../project_proposals/privacy_aware_inference_boundary.md)? For the active device the allowed remote transfer remains zero.

## 5. Local execution answers only one part of the privacy question

**Source:** [Physical Side-Channel Attacks on Edge LLMs: Extracting Output Tokens and User Prompts](https://arxiv.org/abs/2610.14215), submitted October 9 2026.

**What it is.** A security study reports electromagnetic leakage attacks against LLaMA 3.2 1B inference on a Raspberry Pi 5. Its authors explore profiled keyword recovery, broader token inference, and semantic prompt recovery under specific physical proximity and profiling assumptions. They do **not** demonstrate these results on this lab's Orin, Mac, or iPhone.

**Why it matters here.** The [Privacy Aware Inference Boundary proposal](../project_proposals/privacy_aware_inference_boundary.md) concerns what crosses software, tool, and remote model boundaries. A self contained device also has physical and local storage threats. This paper broadens the threat inventory without weakening the immediate requirement to prove no unapproved network inference. Specialized lab instrumentation and physical proximity are a different adversary from a remote API.

**Read or inspect.** Sections **IV** (threat model), **V** (methods), **VI** (reported results), and **VII** (limitations and discussion).

**Experiment or design question.** Can the lab state separate confidentiality claims for network traffic, stored recordings, diagnostic logs, stolen devices, and nearby physical observers? Which claims can be tested today without collecting real speech or buying security hardware? Do not describe an offline pass as proof against all these threats.

## 6. Adjacent operating systems idea: measure stalled time, not just used memory

**Source:** [Linux kernel documentation: Pressure Stall Information](https://cdn.kernel.org/doc/html/latest/accounting/psi.html), foundational documentation dated April 2018. See also [cgroup v2 memory events](https://cdn.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html).

**What it is.** Linux PSI exposes CPU, memory, and I/O contention through aggregate stall counters and short window averages. The distinction between **some** stalled tasks and **full** stalls can expose lost progress that process RSS or average CPU utilization does not explain. Cgroup memory events can add context when those interfaces are available.

**Why it matters here.** On an 8 GB device, the question is not merely whether model weights fit. Recognition, text generation, speech output, the OS, and shared cache may interfere with one another. A voice interaction can have an acceptable peak process RSS yet still experience memory reclaim stalls and poor tail responsiveness. PSI is a diagnostic signal, **not proof** that a specific model caused a stall, and availability must be checked on the actual kernel.

**Read or inspect.** **Pressure interface** and **Monitoring for pressure thresholds** in the PSI guide; **memory.events** and **memory.pressure** in the cgroup v2 guide.

**Experiment or design question.** For a known, synthetic sequence of text only inference requests in the existing Linux VM, do deltas from `/proc/pressure/memory` and `/proc/pressure/io` track deliberately induced contention when latency increases? Keep idle controls, resource attribution limits, and failed attempts visible. Repeat on Jetson only when it has passed receipt and setup checks.

## Recommended deep read

Read **Seeing at the Edge**, especially **IV-A**, **IV-C**, **V-G**, **V-H**, and **VI**. Draft a two column method audit: what the paper measured at the electrical input versus what the lab can currently observe in software. Record which measurements require external instrumentation, and do not borrow its energy figures. The practical lesson is the boundary of a measurement, not a predicted token rate.

## Small build for the next two weeks

Add a **content free contention sampler** to the proposed interaction acceptance ledger from the [October 11 brief](October%2011%202026%20Long%20Tail%20Lab%20Brief.md), without changing models, prompting, or the audio path. This is a scoped measurement addition, not a new inference project.

1. At each trial start and finish, collect available Linux PSI `total` counters for memory, CPU, and I/O, process peak memory if observable, a monotonic elapsed time, and an explicit device label. Mark unsupported counters as unavailable.
2. Record success, timeout, cancellation, and failure as separate outcomes, with no prompt text, transcripts, generated answers, audio files, private filesystem paths, IP addresses, or host identifiers.
3. Validate parsing and missing counter handling with authored fixtures. In the Ubuntu ARM64 VM, compare idle trials with a deliberately bounded synthetic contention trial. Do not interpret VM values as Jetson performance.
4. After physical hardware qualification, repeat the same protocol on Jetson and add OS, kernel, runtime revision, model hash, charging or power mode, and a note about sensor scope. Measure the full interaction separately when safe audio equipment is available.
5. Acceptance is a small versioned schema, fixture driven tests, and a report showing that contention and incomplete trials are visible. No conclusion about optimal quantization or battery life is required.

## Idea not to pursue yet

**Do not build network served KV state or a cloud assisted voice fallback.** SAKURA's mechanism is intellectually useful, but this laboratory's present success boundary requires the voice loop to work with the network disconnected. Remote dependency would erase that property before the first physical baseline exists. A future distributed study needs its own explicit experiment intake, privacy policy, and comparison with job level routing.

## Compact knowledge map

| Reading | Lab connection | What changes in our thinking |
| --- | --- | --- |
| Seeing at the Edge | **Active Edge Offline Intelligence Device** | End to end energy and latency must declare the instrument boundary and output length. |
| EdgeLLM-Nano | **Active device evaluation and open weight runtime discipline** | The benchmark must exercise the modified cache; a smaller footprint is not automatically lower energy. |
| Multimodal Filesystem Memory | **Historical Memory Wiki; Session Capsule Analysis** | Separate evidence pointers, derived knowledge, and transient working state; avoid unapproved raw retention. |
| SAKURA | **Privacy Aware Inference Boundary proposal; historical distributed compute questions** | State transfer size, network variance, and sensitivity labels belong in any future routing decision. |
| Physical Side-Channel Attacks | **Privacy Aware Inference Boundary proposal** | Offline traffic guarantees are not equivalent to physical confidentiality. |
| Linux PSI | **Active device instrumentation** | Inspect resource stall time and failure outcomes alongside speed and memory size. |

## Evidence rules for this edition

The cited papers are preprints and their numbers apply only to the authors' evaluated configurations. The Linux kernel references describe interfaces, not observed behavior on the lab's device. Repository status is from the public default branch and open issue and pull request listings inspected on October 25 2026. No new laboratory result, hardware acceptance, completed model selection, or privacy guarantee is claimed here. Public reporting remains limited to sanitized, explicitly approved engineering observations.
