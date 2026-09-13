# Conclusion: Terminal Artifact Memory

**Status:** Closed — inconclusive on the local transfer hypothesis  
**Closed:** September 12, 2026  
**Basis:** Repository evidence, two established research papers, and current first-party product documentation

## Decision

We are closing Terminal Artifact Memory and directing the laboratory's active work toward the Edge Offline Intelligence Device. The useful lesson is that experience can become reusable context outside a model's weights. Research has already demonstrated versions of that approach, and products such as Perplexity Computer now incorporate persistent memory and reusable skills into ordinary workflows.

Our narrower experiment remains unanswered: we did not establish that verified work from a fixed cloud teacher, distilled into approved Markdown, improves a fixed local student on disjoint terminal tasks. Closing the project is a decision about where to spend the lab's effort. It is neither a successful replication nor evidence that memory transfer fails.

## What we set out to test

The final protocol assigned public memory-build tasks to a fixed `gpt-5.6-sol` teacher, admitted only verified and sanitized evidence after human approval, and compared a fixed Qwen2.5-Coder-7B-Instruct Q4_K_M student with and without retrieved Markdown. M0 meant no memory; M2 meant approved memory. Each held-out task needed an executable-verifier outcome in both conditions before it could count toward transfer.

The [archived protocol](README.md) and [corrective preregistration](preregistrations/2026-08-01-gpt56-qwen32k-teacher-student-corrective.md) preserve the exact controls and disclosure boundaries.

## What our own evidence supports

| Record | Observation | Interpretation |
| --- | --- | --- |
| July 31 pilot | One attempted M0 probe became invalid before verification: its next request contained 16,616 tokens against a frozen 16,384-token context limit. | The chosen context and interaction policy could not finish that attempt. This was not a scored task failure. |
| Pilot transfer comparison | Zero completed M0/M2 pairs, zero verified memory contributions, and zero searchable pages. | M0/M2 pass rates, memory lift, positive transfer, and negative transfer are all unavailable. |
| August 1 corrective protocol | A dry preflight stopped on a combined Docker/Compose version comparison. The corrective specification separated the checks; no measured teacher/student attempt or execution-ledger slot was consumed. | A protocol correction and development checks do not establish transfer efficacy. |

These counts describe different phases: the original pilot consumed one invalid measured attempt; the later teacher/student protocol consumed zero measured attempts. They must not be merged into a claim that the entire project never attempted a run. The [pilot report](results/2026-07-31-measured-pilot/summary.md), [run accounting](results/2026-07-31-measured-pilot/run-accounting.csv), and [results index](results/README.md) are the evidence record.

The practical lessons from our work are concrete:

1. **A usable context budget comes before a learning curve.** The baseline must survive the actual tool transcript before an intervention can be evaluated.
2. **Stopping rules protect the meaning of a result.** Preserving the invalid attempt prevented a selective retry or denominator change from manufacturing evidence.
3. **Eligibility and benefit are separate.** A teacher's verified solution can qualify material for memory; only the student's paired outcomes can show that the memory helped.
4. **Provenance and disclosure need explicit boundaries.** Keeping a capture locally does not mean its original cloud interaction was private. The protocol separated those claims and specified what could be transmitted afterward.
5. **Research infrastructure has an opportunity cost.** We developed controls, manifests, sanitization, and accounting, but the efficacy question remained unmeasured. Further infrastructure work needs a stronger reason than the amount already invested.

## What established research taught us

### Reflexion — Shinn et al., NeurIPS 2023

Reflexion turns task feedback into textual reflections that an agent carries into later attempts, without updating the language model's weights. The paper reports improvements in decision-making, reasoning, and programming under its tested feedback and retry settings. This establishes a practical precedent for changing an agent's behavior through remembered experience. [Conference paper](https://proceedings.neurips.cc/paper_files/paper/2023/file/1b44b878bb782e6954cd888628510e90-Paper-Conference.pdf).

Our takeaway is to treat memory as an intervention whose value depends on useful feedback and actionable content. Reflexion also discusses dependence on the quality of self-evaluation. Its repeated-attempt results do not answer our separate question about transferring approved teacher artifacts to a smaller local student on held-out tasks. [Reflexion proceedings entry](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html).

### ExpeL — Zhao et al., AAAI 2024

ExpeL collects experiences from training tasks, extracts natural-language insights, and retrieves successful experiences when attempting unseen evaluation tasks. It retains the model's parameters and reports improved performance across its evaluated domains. Its use of cross-task experience makes it a close conceptual precedent for our proposed memory pipeline. [Conference paper](https://ojs.aaai.org/index.php/AAAI/article/view/29936/31635).

Our takeaway is that a memory store should preserve reusable lessons and select relevant examples. Accumulating transcripts alone is not a learning objective. ExpeL gives a reason to investigate this architecture; its results do not establish the effect size, reliability, or context cost of our specific teacher, student, sanitization process, and terminal workload. [ExpeL proceedings entry](https://ojs.aaai.org/index.php/AAAI/article/view/29936).

Together, these papers support external experience as a useful part of an agent's design. They leave substantial questions about transfer across models, misleading memories, staleness, and resource limits. We are retaining that design knowledge without claiming we resolved those questions.

## How Perplexity Computer already uses the broader pattern

Perplexity's documentation describes **Brain** as a background process that learns from sessions, connected sources, created artifacts, and corrections. It maintains a source-linked wiki and graph of projects, people, and work, updates changed information, and lets users inspect, edit, or delete entries. The documentation describes a research preview rollout to Max and Enterprise Max users. This is a product example of turning previous work into context for later work. [What is Brain?](https://www.perplexity.ai/help-center/en/articles/19700001-what-is-brain) (updated September 5, 2026; accessed September 12, 2026).

**Computer Skills** address reusable procedure: task-specific instructions can be created conversationally or uploaded as Markdown, including a `SKILL.md` package, and relevant skills activate in later conversations. Skills and memory serve related purposes, but a reusable instruction file does not by itself demonstrate learning from verified executions. [How to use Computer Skills](https://www.perplexity.ai/help-center/en/articles/13914413-how-to-use-computer-skills) (updated September 3, 2026; accessed September 12, 2026).

Perplexity also describes **Portable Computer** running a local agent stack on NVIDIA DGX Spark, with cloud escalation when authorized. That makes local execution part of the product comparison too. Its documented desktop platform and optional cloud path do not establish the feasibility of our fully offline spoken loop on an 8 GB Jetson. [Introducing Portable Computer](https://www.perplexity.ai/en-GB/hub/blog/introducing-portable-computer-for-local-first-ai) (accessed September 12, 2026).

These are first-party descriptions of product behavior, not an independent audit. The reviewed pages do not document our exact verifier-gated teacher/student experiment or publish its paired local-student comparison. The defensible conclusion is that products already implement the broader memory-and-reuse pattern, while our particular hypothesis remains open.

## Operational conclusion and next work

**Evidence observed:** one halted, unscored pilot and no completed local transfer comparison. The literature supplies relevant prior results; product documentation supplies examples of adoption.

**Decision supported:** close this line of active work, preserve its evidence and reproducibility record, and focus on building and measuring the device. No further memory checkpoint or corrective run is planned under this project.

**Claims not supported:** a positive or negative memory-lift estimate, a useful operating range for this student, a cost saving, or a finding that a commercial product has validated our protocol.

**Confidence:** high in the description of the archived evidence; undetermined for the local transfer hypothesis. Reopening would require a bounded question that changes a practical decision and a feasible baseline under a fresh preregistration.

The next active project is the [Edge Offline Intelligence Device](../../projects/02_edge_offline_intelligence_device/README.md). The September 12 direction is iterative: a macOS app with local speech transcription and text answers; an iOS app using the same selected model integration, evaluated through TestFlight with launch conditional on the result; then a self-contained NVIDIA Jetson prototype. The first-year total ceiling is **$1,000**, including all new hardware for the end product and required subscriptions, software/distribution fees, tax, and shipping. Model selection is driven by the iPhone's constraints, with Apple on-device intelligence evaluated first and a compact open-model fallback if needed.

The [model-selection intake](../../resources/project_proposals/apple_local_voice_intake.md) records the next bounded question and its missing decisions. The [Mac development status](../../projects/02_edge_offline_intelligence_device/status.md) records the first working voice-to-text-answer slice; there are zero published comparative quality or performance measurements for Mac, iPhone, or Jetson. The Orin Nano Super 8 GB is a hardware candidate; a 16 GB Orin NX alternative requires a complete configuration within the total budget. This transition is a project decision, not a finding that any candidate model or device meets the full intended requirements.
