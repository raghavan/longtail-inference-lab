# Experiment: wiki memory router with knowledge caching

This experiment treats a markdown wiki as a knowledge cache in front of a tiered set of models. Questions that the wiki plus a local model can answer stay local and cheap. Questions that fall in the tail escalate to frontier models, and the answers are distilled back into the wiki so the tail shrinks over time.

The framing is deliberately borrowed from systems engineering. A cache has a hit path, a miss path, an eviction and refresh story, and metrics that tell you whether it is earning its keep. This experiment asks whether team or personal knowledge behaves the same way.

## Hypothesis

Most questions in a given domain are head questions: they repeat, they cluster, and a small local model with good retrieval can answer them well. A minority are tail questions that need frontier reasoning. If frontier answers are written back into the wiki, tail questions migrate into the head, and the local answer rate should climb over time without quality loss.

![Illustrative index comparing a first run without the wiki cache (90) against a run after wiki cache distillation (60), across repo discovery, stage, and production edge cases](images/wiki-cache-distillation-index.jpeg)

*Illustrative index. A real experiment should measure token usage, tool calls, retries, wall time, and success rate per lifecycle stage.*

## Architecture

### Gateway

LiteLLM runs as the gateway and presents one OpenAI compatible endpoint to callers. Behind it sit three backends:

- a local Qwen coder model served on our own hardware
- Claude via API
- Codex via API

The router logic lives at the gateway layer, so callers never choose a model directly. They ask a question, and the router decides where it goes.

### Memory

A markdown wiki is the memory substrate. Each entry is a plain markdown file with a title, a short summary, a body, and links to related entries. Markdown keeps the memory human readable, diffable, and reviewable in normal pull requests, which matters for the write back loop below.

### Retrieval

Retrieval has two stages:

1. Embedding search over wiki entries returns the top matches for the incoming question.
2. One hop link traversal expands the result set by following links from the top matches to their directly linked neighbors.

The one hop expansion is a cheap way to pull in context that embedding similarity alone misses, such as an entry that defines a term the top match uses without explaining. We deliberately stop at one hop to keep the context bounded and the latency predictable.

### Head vs tail classifier

Before answering, the router classifies the question as head or tail using two signals:

- Retrieval similarity: how close the best wiki matches are to the question. Strong matches suggest the knowledge is already cached.
- Local model confidence: the local Qwen model produces a draft answer, and we score its confidence using token level log probabilities and a self assessment prompt.

Both signals feed a simple threshold rule to start. If retrieval similarity and local confidence are both above threshold, the question is head and the local answer is returned. Otherwise it is tail. The thresholds are tunable and are themselves an experimental variable.

### Escalation

Tail questions escalate to a frontier model through the same gateway. The escalated request carries the retrieved wiki context and the local draft, so the frontier model can correct or extend rather than start cold. Routing between Claude and Codex is by task type: code heavy questions go to Codex, general reasoning and writing go to Claude, with the mapping itself open to revision as we measure quality.

### Write back loop

Every escalated answer is a candidate wiki entry. A distillation step rewrites the frontier answer into wiki form: a stable title, a summary, a body stripped of conversational framing, and links to related entries. The distilled entry lands as a pull request against the wiki rather than a direct write, so a human reviews what enters memory.

This loop is the point of the experiment. If it works, the wiki accumulates exactly the knowledge that was expensive to produce, and the next similar question is a cache hit on local inference.

## Metrics

- Local answer rate: fraction of questions answered by the local model without escalation, tracked over time. The hypothesis predicts this climbs as the wiki grows.
- Routing regret: how often the classifier was wrong in either direction. False escalations waste money on questions the local model could answer. False local answers ship worse quality than the question deserved. Measured by sampling routed questions and answering them on both paths.
- Escalation cost: spend on frontier API calls per question and in total, compared against an everything goes to the frontier baseline.
- Quality evals: a fixed eval set of head and tail questions scored on both paths, so we can see whether local answers on head questions actually match frontier quality, and whether write back degrades or improves answers over time.
- Wiki health: entry count, staleness of entries, duplication rate, orphan entries with no inbound links, and how often retrieved entries actually contribute to an accepted answer.

## Open design questions

- What are the right thresholds for the head vs tail split, and should they be learned rather than hand tuned?
- How should the classifier combine retrieval similarity and local confidence when they disagree, for example strong retrieval but a low confidence draft?
- When should a wiki entry be updated versus a new entry created, and who or what decides that during distillation?
- How is staleness detected and handled? Cached knowledge that has gone wrong is worse than a cache miss.
- Does one hop traversal earn its latency, or does a larger embedding top k capture the same context more simply?
- How do we keep the wiki from bloating with near duplicate entries as the write back loop runs?
- Should escalation ever bypass the wiki entirely, for example when retrieval similarity is near zero and the context would only add noise?
- What is the smallest local model that keeps the local answer rate worthwhile, and how does quantization affect the confidence signal?

## Relation to the lab thesis

This experiment is job level routing applied to knowledge work. The local Qwen model is the long tail compute, the frontier models are the data center, and the wiki is the mechanism that shifts work from the expensive tier to the cheap tier over time. The measurement question is the same as everywhere else in this lab: where is local inference genuinely good enough, and what does it cost to find out.
