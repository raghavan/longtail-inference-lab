# Experiment Title

**Status:** Idea  
**Track:** Choose one  
**Difficulty:** Beginner, Intermediate, or Advanced  
**Owner:** Name or team  
**Last updated:** YYYY MM DD

## How to use this template

Treat this as a working research notebook, not a form to complete for its own sake.

Replace every prompt with concrete language. Remove sections that truly do not apply, but do not omit assumptions, failure boundaries, or limitations without explaining why. Prefer the smallest experiment that can change a real decision.

## One minute summary

**Question:** What are we trying to learn?

**Decision:** What will we do differently if the result is positive, negative, or uncertain?

**Workload:** What real task, session, repository, device, or user situation does this represent?

**Success boundary:** What result would make the approach useful enough to continue?

**Stop boundary:** What result would tell us to stop, simplify, or choose another approach?

## Research question

State one bounded question that can be answered with evidence.

A useful question identifies:

1. The system or behavior being studied.
2. The workload or population being observed.
3. The outcome being measured.
4. The comparison or baseline.
5. The conditions under which the answer should hold.

## Why this belongs in the lab

Explain how the question helps identify where long tail inference is useful, insufficient, fragile, unsafe, or unnecessarily complex.

## Practical context

Describe the real situation that motivated the experiment.

1. Who experiences the problem?
2. What are they trying to accomplish?
3. What constraint matters in practice, such as cost, latency, privacy, reliability, energy, memory, or portability?
4. What happens today without this experiment?
5. Why is the answer worth knowing now?

## Decision being informed

State the operational decision this experiment should inform.

Complete these statements:

1. If the evidence supports the idea, we will...
2. If the evidence does not support the idea, we will...
3. If the evidence is mixed or incomplete, we will...
4. This experiment will not justify...

## What you will learn

List the practical learning outcomes for someone who reads or reproduces the experiment.

1. Learning outcome one.
2. Learning outcome two.
3. Learning outcome three.

## Hypothesis or measurement objective

Write a falsifiable hypothesis.

When exploration must happen before a useful hypothesis exists, state the exact measurement objective instead. Do not invent confidence before the system has been observed.

## Assumptions and model error

Answer these questions before collecting results:

1. What assumptions make this measurement valid?
2. What observations would invalidate those assumptions?
3. Which important variables are not observable?
4. How sensitive is the conclusion to measurement error?
5. Where should this result not be generalized?
6. What are we pretending to know that we may not actually know?
7. Which proxy measurements could be mistaken for the real outcome?

## Tail characteristics

Identify which tails matter in this experiment.

### Demand tail

Which uncommon or difficult tasks are we trying to handle?

### Resource tail

Which requests dominate tokens, latency, retries, memory, bandwidth, energy, or cost?

### Failure tail

Which rare errors could create disproportionate harm?

Report distributions where possible. Include median, p95, p99, maximum, and the share of total resource use or failures caused by the largest observations. Do not rely on averages alone when a few cases dominate the result.

## Ruin boundary

Define outcomes that are unacceptable even if average performance improves.

Answer:

1. What can fail disproportionately?
2. What outcome must never be traded for lower cost or higher local answer rate?
3. How will the experiment prevent that outcome?
4. How will it detect that the boundary was crossed?
5. How could the system recover or contain damage?
6. What human review or escalation remains mandatory?

## Path dependence

Describe how earlier events could change the final outcome.

Consider:

1. Conversation history.
2. Tool call order.
3. Retrieved context.
4. Previous failures or retries.
5. Memory write order.
6. Model or runtime changes.
7. Compression, replay, or summarization choices.

Where practical, run the same final task through several different histories and compare the results.

## Variables and controls

Identify:

1. What changes between runs.
2. What remains fixed.
3. Which external factors may influence the result.
4. Which sources of variation cannot be controlled.
5. How many repeated runs are needed to understand run to run variability.

## Workload and evidence source

Prefer real workloads when they can be collected safely.

Document:

1. Where the workload came from.
2. Why it represents the intended use case.
3. What was removed or transformed for privacy.
4. Which important cases may be missing.
5. Whether synthetic inputs are controls, supplements, or the primary evidence.

## Experiment sequence

Use only the phases needed to answer the question.

### Phase 1: observe the current system

Measure the current behavior before introducing a new mechanism. Record the simplest baseline that a practitioner could use today.

### Phase 2: test the smallest useful intervention

Introduce the minimum change needed to test the idea. Avoid building the full system before the core assumption has evidence.

### Phase 3: stress and fragility tests

Gradually worsen realistic conditions such as context length, memory pressure, stale knowledge, irrelevant retrieval, network delay, model capacity, task novelty, tool output size, or concurrency.

Record whether performance degrades gradually or collapses after a threshold.

### Phase 4: removal test

Remove or simplify the proposed mechanism.

Ask:

1. Does a simpler method perform nearly as well?
2. Which component contributes measurable value?
3. Which component adds complexity without changing the decision?
4. Would doing nothing be a reasonable outcome?

### Phase 5: analysis and decision

Compare the baseline, intervention, stress conditions, and simpler alternatives. Explain uncertainty, failure concentration, and practical consequences.

## Metrics

Define every metric, its unit, and how it is calculated.

For each metric, explain:

1. Why it matters to the decision.
2. What direction is better.
3. What threshold is meaningful.
4. What measurement error is expected.
5. Whether the metric hides important tail behavior.

Avoid ambiguous terms such as faster, cheaper, safer, or better without a calculation and a threshold.

## Reproduce

Document enough detail for another person to reproduce the result safely.

Include:

1. Commands.
2. Configuration.
3. Dataset or workload description.
4. Runtime and model versions.
5. Hardware details.
6. Random seeds where relevant.
7. Number of repeated runs.
8. Safe placeholders for private paths, hosts, credentials, and session content.

## Results

Link or include:

1. Raw measurements.
2. Derived analysis.
3. Distribution plots.
4. Stress curves.
5. Failure examples that are safe to publish.
6. Comparison with the simplest baseline.
7. Notes about missing or discarded data.

Results should remain visible when they are negative, inconclusive, or inconvenient.

## Operational conclusion

Complete this decision record:

**Evidence observed:** What did the measurements show?

**Decision supported:** What action is now justified?

**Decision not supported:** What should not be built, deployed, or claimed?

**Safe operating region:** Under which workloads and conditions did the approach remain acceptable?

**Escalation conditions:** When should the system defer to a stronger model, a human, or a safer process?

**Confidence:** How certain are we, and what evidence would materially change the conclusion?

## Interpretation

Explain what the evidence supports and what it does not support.

Distinguish direct observations from calculations, estimates, and speculation.

## Limitations and open evidence

Record:

1. Important sources of uncertainty.
2. Missing workloads or populations.
3. Unobserved variables.
4. Measurement weaknesses.
5. Conditions not tested.
6. Results that may not transfer to other models, devices, domains, or users.
7. Questions that remain genuinely open.

## Completion condition

List the evidence required before the experiment can be marked Complete.

A complete experiment should normally include:

1. A published baseline.
2. A reproducible intervention.
3. Tail and failure analysis.
4. At least one stress or removal test.
5. An operational conclusion.
6. Limitations and unresolved questions.
7. A clear statement of what should happen next.

## Next smallest question

Propose the smallest follow up experiment justified by the result.

Do not expand the project merely because additional work is possible. Continue only when the next question can change a meaningful decision.
