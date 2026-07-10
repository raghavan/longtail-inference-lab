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

## Warm standby with rsync

The tiers above describe a one shot move. A cheaper posture for planned machine switches is to keep a standby machine continuously close to current, so that changing machines during downtime is a small final delta rather than a full transfer.

rsync is a surprisingly good fit for this, for a structural reason: a KV cache is append mostly. The keys and values for tokens already processed never change as the session grows; new tokens only add entries. So successive saves of the same session share most of their bytes, and rsync's rolling checksum finds those shared runs even when the serialized layout shifts them around inside the file, which it does, because state is stored per layer and each layer's region grows. A block level diff keyed to fixed offsets would miss this; rsync's content matching does not. The expected sync cost is roughly the KV bytes for tokens added since the last sync, plus metadata, not the whole capsule.

The loop looks like:

1. On the active machine, save the slot to a snapshot file on a cadence: every N turns, or on idle. Never sync a file the engine is still writing; save first, sync the completed snapshot.
2. `rsync` the snapshot and manifest to the standby over SSH. rsync writes to a temporary file and renames, so the standby always holds a complete capsule, never a torn one.
3. The standby runs `llama-server` with the same model already loaded and `--slot-save-path` pointed at the synced directory. Failover is one restore call.

The detail that makes the cadence forgiving is hybrid resume. The synced state file is a checkpoint at some token count N, and the transcript names every token after N. On failover, the standby restores the checkpoint and prefills only the tail since the last sync. The recovery point is not the last sync; it is the last transcript update, which is kilobytes and can be synced on every turn. The state file just determines how much prefill the standby has to do, so even a lazy sync cadence, say every ten minutes on an idle link, keeps failover fast.

Two cautions. First, `--inplace` trades away the atomic rename for less temporary disk usage, which opens a window where the standby's copy is torn; avoid it by default, and if a small disk forces it, gate every restore on a payload hash check as in the runbook below. Second, `-z` compression buys little on F16 KV payloads, which are close to incompressible noise; quantizing the KV cache at save time is the effective compression. And as everywhere in this repo, the capsule carries the full private conversation, so the transport is SSH and the standby's copy is treated with the same care as the original.

This is still Tier 1 correctness wise: same model, same KV cache type, close engine versions on both machines, with the transcript as the always available fallback.

## First run: laptop and VPS hot swap with live rsync

This section is the concrete first experiment: one local machine and one VPS, a live rsync loop keeping the KV cache replicated, and a hot swap of the active session in both directions. Hostnames below are SSH config aliases, `local` and `vps`, in keeping with this repo's rule against committing real hostnames or addresses.

### Preconditions

- The same GGUF model file on both machines, verified once: `sha256sum` output must match. Record the hash in the capsule manifest.
- The same llama.cpp release tag built on both machines, even though the backends differ, GPU or CPU on the laptop and CPU on the VPS. State files serialize to a common format, but this pairing is exactly what the fidelity metric below exists to verify before trusting it.
- The same KV cache type on both sides, for example both default F16 or both `--cache-type-k q8_0 --cache-type-v q8_0`.
- Both machines run `llama-server` with a dedicated capsule directory: `llama-server -m model.gguf --slot-save-path ~/capsules ...` with matching context settings. The standby sits warm with the model loaded and zero traffic.

### The live sync loop

On the active machine, after each completed response, or on a timer during long generations:

```bash
# 1. snapshot the slot (never sync what the engine is mid-write on)
curl -s -X POST "http://127.0.0.1:8080/slots/0?action=save" \
  -H 'Content-Type: application/json' -d '{"filename":"session.bin"}'

# 2. ship the payload, then the manifest, in that order
rsync -a --partial --stats ~/capsules/session.bin vps:capsules/ >> sync.log
sha256sum ~/capsules/session.bin > ~/capsules/session.manifest
rsync -a ~/capsules/session.manifest ~/capsules/transcript.json vps:capsules/
```

The two rsync calls are deliberate. The manifest carries the payload hash and lands only after the payload it describes, so the standby can always tell a settled capsule from one still in flight. This ordering is also what makes an `--inplace` variant safe on a disk constrained VPS: rsync's default temp file and rename needs headroom equal to the state file size, and `--inplace` removes that, at the cost of a window where `session.bin` is torn. With hash verification gating every restore, a torn payload fails the check and the standby falls back to the previous transcript plus replay, so nothing incorrect can be resumed. Use the default rename mode when disk allows; use `--inplace` plus mandatory hash check when it does not.

`--stats` in the payload sync is not decoration, it is the experiment: `Total bytes sent` per sync, logged against the token count, is the delta efficiency measurement.

### The swap, planned

1. Stop sending new requests to the active machine and let the in flight response finish.
2. Run one final iteration of the sync loop. This delta is one response worth of KV, typically a few MB, seconds even on a residential uplink.
3. On the standby: verify and restore.

```bash
cd ~/capsules && sha256sum -c session.manifest && \
curl -s -X POST "http://127.0.0.1:8080/slots/0?action=restore" \
  -H 'Content-Type: application/json' -d '{"filename":"session.bin"}'
```

4. Repoint the client at the other machine. The clean way is to never point clients at machines at all: put the gateway from the wiki memory router experiment in front, and the swap becomes a backend flip in LiteLLM config while the client URL never changes.
5. Reverse the roles. The old active machine becomes the standby, and the sync loop runs in the opposite direction. Nothing about the loop is direction specific.

The swap back, VPS to laptop when the laptop returns, is the same five steps with the aliases exchanged. A session can bounce between the two machines indefinitely, and after the first full sync in each direction, every subsequent sync is a delta.

### The swap, unplanned

If the active machine disappears without a final sync, the standby holds the last settled capsule at token count N and a transcript that is at most one sync interval stale. Restore the capsule, replay whatever transcript tail exists beyond N, and accept that anything generated after the last transcript sync is lost. This is the recovery point objective of the setup, and it is bounded by the sync cadence, which is exactly why the transcript, being kilobytes, should ride along on every loop iteration.

### What to record per run

- Per sync: `Total bytes sent`, wall time, and the session token count at save time. Plot bytes against new tokens since the previous sync; the slope is the delta efficiency, and the theoretical floor is the KV bytes per token of the model.
- Per swap: end to end time from the last client response on machine A to the first token of a continued response on machine B, broken into final sync, restore, and any tail prefill.
- Fidelity: immediately after each swap, run a fixed continuation prompt at temperature 0 on the restored session and compare it against the same continuation on an unswapped control session. Divergence here, on the GPU to CPU pairing especially, is a finding, not a nuisance.
- The control: the same swap done as Tier 0, transcript only with full prefill on the target, so every hot swap number has its recompute baseline next to it.

## The break even rule

Ship the state when:

```
kv_bytes / link_bandwidth  <  context_tokens / target_prefill_speed
```

Everything in this inequality is measurable on this lab's hardware, which makes it a routing rule, not a guess. A session router could compute both sides per transfer and pick the cheaper path automatically, the same job level routing posture as the rest of the lab.

## Interaction with split inference

One caveat from the lab's llama.cpp RPC experiments: in split inference, the KV cache for offloaded layers lives on the RPC backend, not the host. A capsule captured on the host must gather state across the split, and a session resumed into a different split topology is effectively a different engine configuration. Simplest position for now: capsules are captured and restored on single machine sessions, and split sessions fall back to Tier 0.

## Related work

Hot swapping in flight LLM requests between machines is an active research area, and most of it validates the mechanics this experiment relies on:

- [Llumnix](https://arxiv.org/abs/2406.03243) (OSDI 2024) live migrates running requests between vLLM instances. Its key trick is the same property the rsync section leans on: the KV cache is append only, so it copies the cache for already processed tokens in parallel with ongoing decoding, and the request's downtime shrinks to one iteration's worth of new state. It also measures the naive alternatives, recompute or stop and copy, at over 50x the cost of a decoding step.
- [SpotServe](https://arxiv.org/abs/2311.15566) (ASPLOS 2024) is the closest match to the downtime motivation: it serves LLMs on preemptible spot instances, commits inference progress at the token level, and resumes interrupted requests on surviving machines rather than restarting them.
- [CacheGen](https://dl.acm.org/doi/10.1145/3651890.3672274) (SIGCOMM 2024) is the closest match to the network constraint: it treats KV caches as something to ship over ordinary bandwidth limited links, encodes them into compact bitstreams with a custom tensor codec, and adapts compression to available bandwidth, reporting 3.5 to 4.3x size reduction. This directly informs the compression open question below.
- [Mooncake](https://arxiv.org/abs/2407.00079) (FAST 2025 best paper) and [LMCache](https://blog.lmcache.ai/en/2025/05/08/lmcache-x-mooncake-unite-to-pioneer-kvcache-centric-llm-serving-system/) build entire serving architectures around a disaggregated KV cache pool moved by an RDMA transfer engine, the Tier 2 world at datacenter scale.
- [AttentionStore / CachedAttention](https://arxiv.org/abs/2403.19708) (ATC 2024) and Pensieve persist KV caches of idle conversations to cheaper storage tiers and restore them when the session resumes, cutting time to first token by up to 88 percent. That is the single machine version of a capsule: same save and restore economics, no network hop.
- [ServerlessLLM](https://arxiv.org/abs/2401.14351) (OSDI 2024) attacks the adjacent problem of loading checkpoints fast enough that moving work between machines is viable at all.

What none of this work does is the specific thing proposed here: replicate serialized session state to a standby over a commodity internet link using content defined delta sync, rsync style, between everyday devices. The research systems assume datacenter fabrics, RDMA, or at minimum machines in the same cluster; CacheGen assumes constrained bandwidth but solves it with compression on a one shot transfer, not with incremental replication to a warm replica. The gap makes sense: for a fleet, generic delta sync is less efficient than purpose built transfer engines. For two or three personally owned machines on residential links, rsync is infrastructure that already exists, and whether it is good enough is exactly a long tail question, unglamorous, unpublished, and measurable.

## Metrics

- Transfer time versus recompute time across context lengths from 1K to 32K tokens, on at least three pairings: laptop to VPS, VPS to laptop, and laptop to laptop over the internet.
- Measured break even point versus the predicted one, per link and per device.
- Restore fidelity: token level agreement of continuations after Tier 1 restore versus Tier 0 replay versus never moving at all.
- Capsule overhead: serialization and deserialization time, which the inequality above ignores and which may matter on slow disks.
- Compression: how much a KV state payload actually compresses, and whether KV quantization before transfer beats generic compression after.
- Delta efficiency: bytes rsync actually ships per sync in the warm standby loop versus the KV bytes of tokens added since the last sync, which is the theoretical floor.
- Failover time from a warm standby: restore time plus tail prefill time, as a function of sync cadence.

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
