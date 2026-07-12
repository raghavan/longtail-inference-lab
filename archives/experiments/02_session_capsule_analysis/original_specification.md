# 02 Session Capsule Analysis

**Status:** Specified  
**Track:** Agent sessions and portable context  
**Difficulty:** Intermediate

## Research question

What does a real coding agent session contain, how does it grow, and when might replay, compression, or portable engine state become worthwhile?

## Why this belongs in the lab

A coding agent session accumulates instructions, user requests, model responses, tool calls, logs, file content, and derived model state. Before building a system that transfers or replicates sessions between machines, the lab needs to understand the artifact itself.

This experiment is deliberately measurement first. Its output is a privacy safe dataset and an analysis, not a transfer system.

## What you will learn

1. How agent session size changes over time.
2. Which components dominate session bytes.
3. Why total context processing can grow faster than the stored transcript.
4. How transcript compression compares with derived KV state size.
5. How measurement can prevent premature distributed systems design.

## Hypothesis

Coding agent sessions are likely to be heavy tailed. Most turns may be small, while a few large tool results, logs, or file reads dominate total size. The text transcript should compress well, while derived engine state may be orders of magnitude larger.

The measurements may show that compressed replay is sufficient for most sessions. That would be a useful negative result for more complex state transfer designs.

## Questions

1. What are the median, p95, and maximum transcript sizes?
2. What fraction of bytes comes from user text, model text, tool output, and instruction files?
3. How does cumulative size grow with turns?
4. Are per turn sizes stationary or heavy tailed?
5. How many tokens remain in the final context?
6. How compressible is each component?
7. What would the derived KV state weigh for representative local models?
8. What is the amplification ratio between derived state and stored transcript?

## Privacy boundary

The committed dataset contains metrics only.

It must not contain:

1. User or model message text.
2. Tool output content.
3. Repository names.
4. File paths found inside sessions.
5. Hostnames or machine identifiers.
6. Prompts, secrets, or credentials.

Each session receives a truncated hash identifier that permits joins between metric tables without naming the source session.

## Source material

The first source is pi coding agent session data stored as JSONL. Other harnesses may be added later if their session formats are inspectable and the same privacy boundary can be preserved.

The schema must identify the harness so results from different systems are never mixed silently.

## Dataset

### sessions.csv

One row per session.

| Column | Meaning |
| --- | --- |
| session_key | Truncated hash used only for joining metrics |
| harness | Session harness name |
| model | Model identifier where available |
| messages | Total entries |
| turns | User visible request and response cycles |
| tool_calls | Tool invocation count |
| transcript_bytes | Raw session file size |
| gzip_bytes | Compressed session size |
| user_bytes | Bytes attributed to user content |
| assistant_bytes | Bytes attributed to model content |
| tool_bytes | Bytes attributed to tool results |
| instruction_bytes | Bytes attributed to instruction files |
| final_context_tokens | Recorded usage where available, otherwise estimated |
| tokens_estimated | Whether final context tokens are estimated |

### turns.csv

One row per turn or session event.

| Column | Meaning |
| --- | --- |
| session_key | Join key for sessions.csv |
| turn_index | Position in the session |
| role | User, assistant, or tool |
| bytes | Size of the event |
| cumulative_bytes | Session size after the event |

## Derived state estimates

Derived KV state size is a calculation, not a direct measurement in this experiment.

For each reference model, estimate:

```text
KV bytes per token = 2 × layers × KV heads × head dimension × bytes per element
```

Multiply the result by final context tokens. Record model architecture and KV precision beside every estimate.

This permits comparison between the small authoritative replay representation and the much larger state that a local inference engine may maintain for fast continuation.

## Analysis dimensions

### Size distribution

Report median, p95, maximum, and the full distribution. Averages alone are not useful when a few large sessions dominate storage or transfer costs.

### Growth by turn

Plot cumulative transcript size against turn index. Compare linear, quadratic, and heavy tail interpretations.

A hosted agent may send much of its accumulated context again on every request. The stored transcript can grow roughly linearly while total processed context grows much faster.

### Composition

Measure which content classes dominate session bytes. The experiment should test rather than assume that tool output is the largest component.

### Compressibility

Measure compression ratio for the whole session and for each component where possible. Repetitive logs and structured JSON may compress substantially.

### State amplification

Compare estimated KV state bytes with transcript bytes. This indicates which sessions might justify state aware continuation and which are trivially inexpensive to replay.

## Experiment sequence

### Phase 1: extractor

Build a single pass metrics extractor that reads session files and emits only the approved schema.

### Phase 2: safety verification

Inspect generated output and run the repository safety scan. Confirm that no text content or local paths are present.

### Phase 3: collection

Measure a meaningful sample of sessions across different lengths, models, and task types where available.

### Phase 4: analysis

Publish distributions, composition charts, growth curves, compression ratios, and derived state estimates.

### Phase 5: decision

Conclude whether future work should study simple compressed replay, structured capsules, local engine state, or no transfer machinery at all.

## Completion condition

This experiment is complete when:

1. The metrics extractor is published.
2. The privacy safe dataset schema is validated.
3. A representative session sample is measured.
4. Size, composition, growth, compression, and amplification results are published.
5. The conclusion clearly states which follow up direction is justified by evidence.

## Results

Results have not yet been collected.

[Results workspace](results/README.md)

## What this experiment does not include

This project does not build migration, replication, failover, or cross machine session restore. Those ideas should return as separate projects only when this analysis supplies evidence that they are worthwhile.
