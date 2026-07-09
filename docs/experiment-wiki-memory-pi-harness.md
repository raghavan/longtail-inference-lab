# Implementation note: building the wiki memory router on the pi agent harness

This note assesses whether the [wiki memory router experiment](experiment-wiki-memory-router.md) can be built on [pi](https://github.com/badlogic/pi-mono), Mario Zechner's minimal agent harness. Short answer: yes, and it is a good fit. Pi replaces most of the plumbing the experiment needs — multi-provider model access, an agent loop with custom tools, and per-session logs — while leaving the interesting parts, the classifier and the write back loop, as application code we own.

## What pi is

Pi is a TypeScript monorepo of small, composable packages rather than a monolithic agent product:

- `pi-ai`: a unified, typed LLM API across OpenAI, Anthropic, Google, and OpenAI-compatible endpoints, including local servers such as llama.cpp and vLLM.
- `pi-agent-core`: the agent loop with tool calling and state management, usable as a library for custom agents.
- `pi-coding-agent`: an interactive CLI coding agent built on the two packages above, extensible with custom tools and system prompts.

The design philosophy matches this lab's: minimal, hackable, bring your own keys, no lock-in to a single provider or subscription.

## Mapping pi onto the experiment architecture

### Gateway

The original design puts LiteLLM in front of three backends as a network-level gateway. Pi offers a different shape: `pi-ai` is an in-process library that already speaks to Claude, OpenAI, and any OpenAI-compatible endpoint, so the local Qwen model served by llama.cpp or vLLM is just another configured model. The router then becomes ordinary application code calling `pi-ai`, not proxy configuration.

Two viable arrangements:

1. **Pi-native.** Drop LiteLLM. The router is a small TypeScript service built on `pi-ai` that owns model selection directly. Fewer moving parts, and the routing decision lives next to the classifier signals it depends on.
2. **Hybrid.** Keep LiteLLM as the shared endpoint for other callers and point `pi-ai` at it as a single OpenAI-compatible backend. This preserves the "callers never choose a model" property for non-pi clients at the cost of one more hop.

For a first pass the pi-native arrangement is simpler and keeps the experiment self-contained.

### Retrieval

Pi does not ship an embedding store, so retrieval stays ours: embedding search over wiki entries plus one hop link traversal, exposed to the agent as a custom tool (for example `wiki_search`) registered with `pi-agent-core`. This is the intended extension point — pi's default toolset is deliberately tiny, and adding domain tools is the normal way to specialize it.

### Head vs tail classifier

The classifier needs two signals:

- **Retrieval similarity** comes from our own retrieval layer, independent of pi.
- **Local model confidence** needs token-level log probabilities from the Qwen draft. Logprobs are part of the OpenAI-compatible API surface that llama.cpp and vLLM expose, but whether `pi-ai` passes them through cleanly needs verification early — if it does not, the draft call can hit the local endpoint directly while everything else stays on pi. The self-assessment prompt is just another `pi-ai` call.

The threshold rule itself is plain code in the router, as before.

### Escalation

Escalation is a second `pi-ai` call to Claude or the OpenAI backend, carrying the retrieved wiki context and the local draft in the prompt. Because both tiers sit behind the same typed API, the by-task-type routing between frontier models is a lookup table, and revising the mapping is a code change rather than gateway reconfiguration.

### Write back loop

This is where pi earns extra keep. The distillation step — rewrite a frontier answer into a wiki entry with a stable title, summary, body, and links, then open a pull request — is exactly the shape of work `pi-coding-agent` does well: editing markdown files in a repo under a custom system prompt. The distiller can run as a pi agent invocation over the wiki checkout, with the human review gate unchanged: distilled entries land as pull requests, never direct writes.

### Metrics

Pi records sessions as structured logs including requests, responses, and token usage. That gives several of the experiment's metrics nearly for free:

- **Local answer rate**: count sessions resolved without an escalation call.
- **Escalation cost**: token usage per frontier call, summed against the everything-goes-to-frontier baseline.
- **Routing regret and quality evals**: pi can be driven programmatically, so the fixed eval set runs as a script that replays each question down both paths and stores the paired transcripts for scoring.

Wiki health metrics remain ours, computed over the markdown files directly.

## Honest caveats

- **Language.** Pi is TypeScript; this lab's tooling so far is Python. The router and tools would be TypeScript, or `pi-ai` gets used only where it pays and Python keeps the analysis side.
- **Logprobs passthrough** is the main technical unknown and should be the first thing verified, since the confidence signal depends on it.
- **No permission system.** Pi deliberately omits built-in sandboxing; the write back agent should run in a container with access to nothing but the wiki checkout, per pi's own containerization guidance.
- **Embedding retrieval is not included.** Expected, but it means the retrieval stage is built and benchmarked by us either way.

## Suggested first slice

1. Serve Qwen locally via llama.cpp and register it plus Claude in a `pi-ai` config; verify logprobs come through from the local endpoint.
2. Build `wiki_search` (embedding top-k plus one hop) as a custom tool and a thin router script implementing the threshold rule.
3. Wire escalation with context-and-draft carry-over.
4. Run the fixed eval set through the router and compute local answer rate and escalation cost from pi's session logs.
5. Add the write back distiller as a `pi-coding-agent` invocation that opens wiki pull requests.

Steps 1–4 are enough to test the core hypothesis; step 5 closes the loop that makes the tail shrink.
