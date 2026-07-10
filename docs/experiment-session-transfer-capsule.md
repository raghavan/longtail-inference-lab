# Experiment: session transfer as a capsule

This experiment asks whether a live inference session on one machine can be packaged as a self contained capsule, moved across the internet, and resumed on another machine as if it never left. The short answer is yes, and the interesting question is when it is worth it.

A session is more than a chat transcript. By the time a model has processed a long context, the machine holds a large piece of derived state, the KV cache, that took real compute to build. Moving a session is therefore a classic systems tradeoff: ship the state, or ship the inputs and recompute the state on the other side. This is the network tax question from the lab thesis, applied to inference state instead of activations.

## Hypothesis

For long contexts landing on weak hardware, transferring the KV cache over a decent link is faster than recomputing the prefill locally. For short contexts, fast target hardware, or slow links, replaying the transcript wins. There is a measurable break even point, and it can be predicted from four numbers: context length, KV bytes per token, link bandwidth, and target prefill speed.

## What a session actually is

To resume a session exactly, the capsule must capture:

- The transcript: every token of the conversation so far, including the system prompt and tool outputs. Kilobytes. Trivially portable.
- The model identity: which weights, which quantization, which context settings. The capsule should reference weights by content hash, never include them. Both machines are expected to already hold the model, which in this lab they do.
- The KV cache: the attention keys and values for every processed token. This is the heavy, expensive to rebuild part, and the only reason a capsule is more than a JSON file.
- Sampler state: sampling parameters, and RNG state if bit exact continuation matters.
- Engine metadata: engine name, version, and KV cache type, because serialized state formats are engine and version sensitive.

## Sizing the problem

KV cache size per token is `2 x layers x kv_heads x head_dim x bytes_per_element`. Two worked examples at F16:

- Llama 3 8B: 32 layers, 8 KV heads, head dim 128 gives 128 KB per token. An 8K token session is about 1 GiB.
- Qwen2.5 7B: 28 layers, 4 KV heads, head dim 128 gives 56 KB per token. An 8K token session is about 450 MiB.

Quantizing the KV cache to q8_0 roughly halves these. Grouped query attention is why these numbers are tolerable at all; an older multi head attention model of the same size would be several times larger.

Now the two sides of the tradeoff for that 1 GiB Llama session:

- Transfer: about 9 seconds at 1 Gbps, about 90 seconds at 100 Mbps, and roughly 7 minutes on a 20 Mbps residential uplink.
- Recompute: replaying 8K tokens of prefill takes a few seconds on a consumer GPU at 1000 or more tokens per second, but minutes on a laptop or VPS CPU running at tens of tokens per second.

So the capsule with KV state earns its keep exactly in this lab's home territory: CPU bound everyday devices on reasonable links. Between two GPU machines on a slow link, recomputing is usually cheaper than shipping.

## Capsule format

A capsule is a single archive containing:

- `manifest.json`: capsule version, model content hash, engine and version, quantization, context length, KV cache type, token count, creation time, and a content hash of the state payload for integrity.
- `transcript.json`: the full token sequence and message structure. This makes every capsule degradable: any machine that has the weights can resume from the transcript alone, even if it cannot load the state payload.
- `state.bin`: the serialized engine state, present only in Tier 1 capsules below.

The transcript is always included precisely so the state payload is an optimization, never a dependency.

## Transfer tiers

### Tier 0: transcript replay

Ship only the transcript and recompute the prefill on the target. Engine agnostic, version agnostic, tiny, and always correct. Prefill on identical weights and settings rebuilds the same KV state up to floating point noise. This is the baseline every other tier must beat.

### Tier 1: state capsule

Ship the serialized KV cache alongside the transcript. llama.cpp supports this today with no new code:

- `llama-cli --prompt-cache FILE` writes and reloads session state.
- The C API exposes `llama_state_save_file` and `llama_state_load_file`, with per sequence variants.
- `llama-server` started with `--slot-save-path` exposes `/slots/{id}?action=save` and `?action=restore`, which turns session transfer into two HTTP calls and one file copy.

The procedure between machine A and machine B is: save the slot on A, move the file with any encrypted transport, restore the slot on B, continue generating. The constraint is strict compatibility: same model file, same KV cache type, and a close enough engine version, because the state format is an internal format, not a stable interchange format. The manifest exists to check all of this before attempting a restore, and the transcript is the fallback when the check fails.

### Tier 2: streaming KV migration

The datacenter version of this idea ships KV state between machines continuously rather than as a file: disaggregated prefill in vLLM, LMCache, and Mooncake style transfer engines. Worth studying as the reference point for what the technique looks like at scale, but overkill for this lab. A file shaped capsule is the right granularity for everyday devices.

## The break even rule

Ship the state when:

```
kv_bytes / link_bandwidth  <  context_tokens / target_prefill_speed
```

Everything in this inequality is measurable on this lab's hardware, which makes it a routing rule, not a guess. A session router could compute both sides per transfer and pick the cheaper path automatically, the same job level routing posture as the rest of the lab.

## Interaction with split inference

One caveat from the lab's llama.cpp RPC experiments: in split inference, the KV cache for offloaded layers lives on the RPC backend, not the host. A capsule captured on the host must gather state across the split, and a session resumed into a different split topology is effectively a different engine configuration. Simplest position for now: capsules are captured and restored on single machine sessions, and split sessions fall back to Tier 0.

## Metrics

- Transfer time versus recompute time across context lengths from 1K to 32K tokens, on at least three pairings: laptop to VPS, VPS to laptop, and laptop to laptop over the internet.
- Measured break even point versus the predicted one, per link and per device.
- Restore fidelity: token level agreement of continuations after Tier 1 restore versus Tier 0 replay versus never moving at all.
- Capsule overhead: serialization and deserialization time, which the inequality above ignores and which may matter on slow disks.
- Compression: how much a KV state payload actually compresses, and whether KV quantization before transfer beats generic compression after.

## Security posture

A capsule contains the entire conversation, which is exactly the private prompt material this repo refuses to commit. Capsules are data in flight, never repo content. Transport must be encrypted, capsules should be encrypted at rest on both ends, the manifest hash must be verified before restore, and restoring a state blob from an untrusted source is equivalent to feeding untrusted input to the engine's deserializer and should simply not be done.

## Open questions

- How sensitive are llama.cpp state files across engine versions in practice, and can the manifest check be made reliable rather than hopeful?
- Does KV cache quantization to q8_0 or q4_0 before transfer degrade continuation quality measurably, or is it free bandwidth?
- Can a capsule be restored into a larger context window than it was saved from, to migrate a session from a small machine to a bigger one mid conversation?
- Is delta transfer worth it for a session that bounces between two machines repeatedly, shipping only the KV entries for tokens added since the last sync?
- At what context length does capsule transfer become the wrong tool entirely, and the right move is to keep the session pinned to one machine and route new jobs instead?

## Relation to the lab thesis

Session transfer is long tail compute made liquid. If sessions can move, then the question of where inference runs becomes a per moment routing decision rather than a per conversation commitment: start a conversation on a laptop, escalate the heavy middle to a VPS, and pull it back to the edge for the cheap tail. The capsule is the unit that makes the network tax explicit, one file whose size and transfer time can be weighed directly against the compute it saves.
