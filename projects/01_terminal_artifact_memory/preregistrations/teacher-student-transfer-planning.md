# Teacher-to-local artifact memory transfer plan

**Status:** Planned protocol; not frozen or measured
**Track:** `artifact_memory`
**Last updated:** August 1 2026

This planning record applies the laboratory experiment template to the accepted teacher/student pivot. It is not a preregistration. The task split, context policy, external pins, thresholds, and run revision remain to be frozen before measurement.

## One minute summary

**Question:** Can verifier-passing public terminal work from fixed cloud teacher `gpt-5.6-sol`, distilled by the same model only after local sanitization, become approved Markdown memory that improves the exact pinned local Qwen student on disjoint held-out tasks?

**Decision:** Continue the compact transfer design only if complete held-out Qwen M0/M2 executable-verifier pairs show useful positive transfer with acceptable negative transfer and safety outcomes. Prefer simpler search or direct cloud inference if they do not.

**Workload:** Preregistered public Terminal Bench tasks separated into cloud-teacher memory builds and local-student held-out probes.

**Success boundary:** To be finalized numerically before measurement. At minimum, a complete pair must show Qwen fail under M0 and executable-verifier pass under M2 to count as positive transfer; teacher build passes do not count.

**Stop boundary:** Stop on verifier ineligibility, split contamination, provenance mismatch, scanner/canary failure, missing hash-scoped approval, incomplete pair accounting, or a preregistered negative-transfer/safety threshold breach.

## Research question and practical context

The fixed local student may lack rare engineering knowledge that a stronger cloud teacher can produce. The experiment asks whether compact verified memory transfers that knowledge without changing student weights or sending held-out evaluation data to cloud roles.

A positive result would identify qualified recurring task families suitable for local execution with approved memory. A negative result would avoid a complex memory layer. Mixed evidence should separate verifier adequacy, artifact quality, retrieval, student capacity, and context limitations.

This experiment will not justify production execution, generalize beyond the qualified split, establish that Markdown changes model weights, or treat a teacher score as student efficacy.

## Fixed accepted design

1. Cloud teacher and model-assisted distiller: exact identity `gpt-5.6-sol`.
2. Student and sole evaluation model: Apache-2.0 `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`, revision `13fb94bfda8c8cf22497dc57b78f391a9acb426a`, Q4_K_M, SHA-256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`, through pinned llama.cpp.
3. Memory builds and held-out probes are preregistered, nonempty, and disjoint.
4. The executable verifier alone establishes an individual run's eligibility or held-out outcome.
5. Task verifiers require private development-only positive, targeted-negative, determinism, and isolation qualification before measured use.
6. Local sanitizer, Gitleaks, canary, blocked-term, allowlist, contamination, and residual gates run before distillation.
7. The distiller receives only a generated field-allowlisted request containing public task data and sanitized evidence.
8. External human approval scopes exact request, source evidence, and draft hashes before admission.
9. Qwen runs paired M0 and M2; the retrieved-memory block is the only student-context difference.
10. No cloud SDK or unsupported provider API is introduced.

## Hypothesis

For qualified held-out structural-recurrence tasks, approved teacher-derived M2 Markdown will increase the exact local Qwen executable-verifier pass rate over M0 without exceeding preregistered negative-transfer, unsafe-error, contamination, latency, or context boundaries.

## Assumptions and model error

The measurement assumes task splits represent structural recurrence without solution leakage, verifier qualification catches plausible requirement failures, role/admission hashes describe the actual lifecycle, and paired controls remain fixed. These assumptions fail if qualification controls are weak, public task families overlap semantically enough to leak answers, an operator adapter misreports model identity, or context/rendering differs outside the retrieved block.

Unobservable variables include provider implementation details, residual verifier blind spots, and model/runtime nondeterminism beyond recorded controls. Mutation qualification raises confidence but cannot prove that a verifier perfectly captures task intent. Results should not generalize to private repositories, other models, unqualified tasks, or execution outside benchmark isolation.

## Tail and ruin boundaries

Demand tails are structurally recurring setup/build/service failures. Resource tails include long teacher/student trajectories, prompt processing, context exhaustion, and review effort. Failure tails include credential or private-path transmission, hidden-test leakage, verifier false acceptance, split contamination, stale/irrelevant memory, unsupported destructive commands, and missing-result denominator shrinkage.

No average lift can offset a privacy breach, contaminated held-out split, unqualified verifier, fabricated result, or executable-verifier override. The affected task/run stops and remains visible as ineligible, invalid, or not run.

## Path dependence

Teacher tool order changes raw evidence; sanitizer transformations determine distiller input; distillation wording and approval determine admitted memory; admission order changes the checkpoint; lexical retrieval changes the Qwen context. The protocol records every boundary hash and freezes page state before M2. Held-out M0 runs occur before memory construction.

## Variables and controls

The intervention is approved retrieved Markdown memory count. Fixed student controls include exact model bytes, quantization, llama.cpp, prompts, decoding, hardware, context policy, tools, task environment, attempt budget, and retrieval rule. Teacher and distiller identity/prompt are fixed for memory construction. Operator adapter and external versions are recorded exactly.

The exact next context policy is intentionally not selected here because the halted 16,384-token pilot showed it could fail before verification. It must be chosen and demonstrated in development before freezing the next run.

## Workload and evidence

Use only license-compatible public task instructions and public isolated benchmark interactions for teacher execution. Raw local trajectory exports, private qualification evidence, detailed scanner output, canaries, and local configuration remain ignored and uncommitted. Synthetic fixtures are controls only and can never be promoted to measured evidence.

The next preregistration must publish the exact build/evaluation task IDs, public requirement classes, family mapping, relevant-page mapping, verifier bundle hashes, and task/container pins.

## Experiment sequence

1. Freeze a new protocol, exact disjoint split, context policy, pins, adapters, checkpoints, and thresholds.
2. Qualify each task verifier privately in development.
3. Run all held-out Qwen M0 probes.
4. Run cloud-teacher memory builds and require exact executable-verifier passage.
5. Sanitize locally, generate allowlisted requests, obtain GPT-5.6-sol drafts, approve exact hashes, and admit pages.
6. Run the same held-out Qwen probes under M2.
7. Analyze every preregistered pair and missing/ineligible record.
8. Run planned stale/irrelevant-memory and simpler-search removal tests only after the core pair is complete.

## Metrics

Primary: structural held-out Qwen M2 verifier pass rate minus M0 pass rate.

Required secondary metrics: positive transfer, negative transfer, stable success, unresolved tasks, retrieval coverage, verified knowledge yield, wiki bytes, latency, prompt/output tokens, invalid/ineligible counts, unsafe confident errors, and safety/contamination stops. Numeric decision thresholds must be frozen before measurement.

## Reproduction and evidence state

Authoritative commands, templates, roles, disclosure inventory, qualification schema, storage rules, and operator sequence are in `SETUP.md` and `OPERATOR.md`. Exact measured versions, hardware, task paths, and environment-only secrets belong in ignored local manifests; only safe compact provenance and reviewed outputs may be published.

No teacher/student result exists. The 2026-07-31 halted 16K report remains the only genuine pilot accounting and contributes no transfer pair.

## Completion and next smallest question

Completion requires a published baseline, at least three approved memory checkpoints, complete held-out pairs, tail/failure analysis, stress and removal tests, limitations, and an operational conclusion. The next smallest question is the freshly preregistered qualified teacher/student pilot at its first approved checkpoint—not a broader platform, model comparison, or provider integration.
