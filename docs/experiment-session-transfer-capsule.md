# Experiment: session transfer as a capsule

This experiment asks whether an inference session running on one machine can be packaged, transferred, and resumed on another machine without rebuilding its entire context.

llama.cpp already supports saving and restoring internal session state. The unanswered questions are whether that state is portable across ordinary machines, whether transferring it is faster than replaying the transcript, and whether successive snapshots are stable enough for efficient delta synchronization using commodity tools such as rsync.

The experiment is not trying to prove that session transfer works. It is trying to map the boundary where state transfer, transcript replay, or keeping the session pinned to one machine becomes the correct systems decision. This is the network tax question from the lab thesis, applied to inference state instead of activations.

## What a session actually is

To resume a session exactly, a capsule must capture:

- The token history: every token the engine has processed, in order. Kilobytes. The authoritative replay representation, see the capsule format below.
- The model identity: which weights, which quantization, which context settings. The capsule references weights by content hash, never includes them. Both machines are expected to already hold the model.
- The KV cache: the attention keys and values for every processed token. This is the heavy, expensive to rebuild part, and the only reason a capsule is more than a JSON file.
- Sampler state: sampling parameters, and RNG state if bit exact continuation matters.
- Engine metadata: engine version, backend, and KV cache type, because serialized state formats are engine and version sensitive.

## Sizing the problem

KV cache size per token is `2 x layers x kv_heads x head_dim x bytes_per_element`. Two worked examples at F16:

- Llama 3 8B: 32 layers, 8 KV heads, head dim 128 gives 128 KB per token. An 8K token session is about 1 GiB.
- Qwen2.5 7B: 28 layers, 4 KV heads, head dim 128 gives 56 KB per token. An 8K token session is about 450 MiB.

Quantizing the KV cache to q8_0 roughly halves these. Grouped query attention is why these numbers are tolerable at all; an older multi head attention model of the same size would be several times larger.

For scale, that 1 GiB Llama session takes about 9 seconds to move at 1 Gbps, about 90 seconds at 100 Mbps, and roughly 7 minutes on a 20 Mbps residential uplink, while replaying 8K tokens of prefill takes a few seconds on a consumer GPU and minutes on a laptop or VPS CPU. Whether transfer or replay wins is precisely what the phases below measure.

## Two related experiments

This document contains two different systems questions, and a result for one does not establish the other.

### Session migration

Move a session once from machine A to machine B. The comparison is complete state transfer plus restore, versus transcript transfer plus full prefill.

### Warm standby replication

Periodically copy snapshots to machine B so that a later switch requires only a final delta and optional token tail replay. Replication introduces costs migration does not have:

- Repeated snapshot serialization
- Network usage over the session lifetime
- Standby memory and storage
- Keeping model weights loaded on the standby
- Snapshot pauses
- Operational complexity

A migration can be worthwhile even when continuous replication is not. A successful one time migration does not prove that maintaining a warm standby is economical.

## Hypotheses

This experiment evaluates four separate hypotheses.

### H1: State portability

A session state file created by one llama.cpp process can be restored by another process when both use:

- Identical model weights
- Identical tokenizer and chat template
- Compatible llama.cpp versions
- Identical KV cache types
- Compatible context settings

"Compatible versions" is a checkable field, not a judgement call: state files carry an internal session version constant, so the manifest records both the llama.cpp release tag and that constant, and a mismatch fails the compatibility check before any restore is attempted.

Cross backend restoration, such as Metal to CPU or CUDA to CPU, is not assumed to be exact and must be measured separately.

### H2: Transfer can outperform replay

For sufficiently long contexts and sufficiently slow target hardware, transferring serialized session state and restoring it is faster than replaying the complete token history on the target. The complete decision rule is:

```text
save_time
+ transfer_time
+ verification_time
+ restore_time
+ tail_prefill_time
<
full_prefill_time
```

For a previously synchronized warm standby, save_time may already have been paid and transfer_time may contain only the final delta. Every term is measurable on this lab's hardware, so if H2 holds, the rule can become a routing decision rather than a guess.

### H3: Serialized snapshots may support efficient delta synchronization

The logical KV cache is append mostly: keys and values for previously processed tokens do not normally change when new tokens are appended. It does not follow automatically that the serialized state file is append mostly. The serializer may rewrite:

- Metadata and offsets
- Per layer regions
- Sequence bookkeeping
- Checksums
- Allocator state
- Fixed capacity buffers
- Backend specific state

rsync uses rolling checksums and can recognize moved byte ranges, so it may still find common regions when offsets shift. There is a second failure mode beyond wholesale rewriting: granularity. rsync matches blocks of a minimum size, roughly the square root of the file size by default, so if the format interleaves changed and unchanged state at a scale finer than the block size, matched runs become too short to exploit and delta efficiency collapses even though the underlying tensors barely changed.

The experiment therefore measures:

```text
delta efficiency =
actual bytes transferred by rsync
/
theoretical KV bytes added since the previous snapshot
```

A result near 1.0 would mean generic delta synchronization approaches the theoretical floor. A much larger result would indicate that the serialization format is unsuitable for efficient content defined synchronization. This is a central measurement, not an assumption.

### H4: Restored continuation remains faithful

A restored session should produce continuation behavior close to an uninterrupted control session. Exact token equality may not hold across different compute backends, because small numerical differences can alter token selection. Fidelity must therefore be measured at the logit, token, and semantic levels, as defined under fidelity measurements below.

## Capsule format

A capsule generation contains four files.

### `manifest.json`

- Capsule schema version
- Generation number
- Model SHA256
- Tokenizer identity
- Chat template hash
- llama.cpp commit or release tag, and the internal session version constant
- Backend type
- KV cache types
- Context configuration
- Number of tokens represented by the state payload
- State payload SHA256
- Creation timestamp

### `messages.json`

The human readable conversation structure: system prompts, user messages, assistant messages, and tool outputs. This file exists for humans and for clients; it is not the replay source.

### `tokens.json`

The exact ordered token IDs processed by the model. This is the authoritative replay representation. Message text alone may tokenize differently when the tokenizer, chat template, tool formatting, or engine version changes.

Provenance matters: token IDs must be captured from the engine at request time, prompt tokens via `/tokenize` when the request is built and generated tokens via `return_tokens` in the completion response. Re tokenizing `messages.json` after the fact defeats the purpose of this file.

### `state.bin`

The serialized llama.cpp state payload. This is an optimization. A target that cannot safely restore it must fall back to replaying `tokens.json`.

## Snapshot generations

Snapshots are immutable and generation numbered; nothing overwrites `session.bin` in place:

```text
session.000041.bin
session.000041.sha256
manifest.000041.json
tokens.000041.json
CURRENT
```

The transfer sequence is:

1. Create a complete local snapshot
2. Compute its payload hash
3. Transfer the payload
4. Transfer its manifest and token log
5. Verify the generation on the standby
6. Atomically update `CURRENT`

The standby retains at least two verified generations. If the newest generation is incomplete or invalid, it restores the previous verified generation and replays the remaining token tail. This is a real rollback mechanism: a sync that dies mid transfer can never leave the standby with only a torn newest state.

One correction this scheme requires, or it silently breaks the delta measurement: rsync computes deltas against a destination file of the same name, and `session.000042.bin` has no counterpart on the standby, so by default every generation ships as a full copy. The transfer must give rsync a basis file explicitly, either `--fuzzy`, which selects a similar named file in the destination directory, so the previous generation serves as the basis, or `--copy-dest` pointed at the prior generation. Phase 4 measures with and without the basis file, to separate "the format is delta unfriendly" from "the transfer was misconfigured".

## Synchronization commands

Hostnames are SSH config aliases, `local` and `vps`, in keeping with this repo's rule against committing real hostnames or addresses. On the active machine, after each completed response:

```bash
set -euo pipefail

CAPSULE_DIR="$HOME/capsules"
cd "$CAPSULE_DIR"

GEN="$(cat CURRENT 2>/dev/null || echo 000000)"
GEN="$(printf '%06d' $((10#$GEN + 1)))"
PAYLOAD="session.${GEN}.bin"

# 1. snapshot the slot (never sync what the engine is mid write on)
curl --fail --silent --show-error \
  -X POST "http://127.0.0.1:8080/slots/0?action=save" \
  -H "Content-Type: application/json" \
  -d "{\"filename\":\"${PAYLOAD}\"}"

# 2. emit the sidecars; the save endpoint produces only the payload,
#    so the client layer that tracked token IDs writes these two
write_tokens_json  "tokens.${GEN}.json"
write_manifest     "manifest.${GEN}.json" "$PAYLOAD"
sha256sum "$PAYLOAD" > "session.${GEN}.sha256"

# 3. payload first, previous generation as the delta basis
rsync -a --partial --fuzzy --stats "$PAYLOAD" vps:capsules/ >> sync.log

# 4. sidecars only after the payload they describe
rsync -a "session.${GEN}.sha256" "manifest.${GEN}.json" "tokens.${GEN}.json" vps:capsules/

# 5. advance the pointer last
printf '%s\n' "$GEN" > CURRENT
rsync -a CURRENT vps:capsules/
```

Hashing runs inside the capsule directory so the manifest records a bare filename, and verification on the standby does not depend on the source machine's absolute paths. `--stats` is not decoration, it is the experiment: `Total bytes sent` per sync, logged against token count, is the delta efficiency measurement. `-z` compression is expected to buy little on F16 KV payloads, which are close to incompressible; KV quantization at save time is the effective compression, and Phase 4 checks both expectations.

On the standby, verification and restore:

```bash
set -euo pipefail
cd "$HOME/capsules"

GEN="$(cat CURRENT)"
if sha256sum -c "session.${GEN}.sha256"; then
  curl --fail --silent --show-error \
    -X POST "http://127.0.0.1:8080/slots/0?action=restore" \
    -H "Content-Type: application/json" \
    -d "{\"filename\":\"session.${GEN}.bin\"}"
else
  echo "generation ${GEN} invalid, falling back to previous verified generation" >&2
fi
```

The fallback path restores the newest earlier generation whose hash verifies, then replays the token tail from the latest `tokens.*.json` beyond that generation's token count.

## Experimental sequence

### Phase 1: local save and restore

Run entirely on one machine. For context lengths of 1K, 4K, 8K, 16K, and 32K tokens:

1. Build the context
2. Save session state
3. Stop the process
4. Start a fresh process
5. Restore the state
6. Continue with a fixed prompt

Record: state file size, save time, restore time, restore success, next token logit agreement, deterministic continuation agreement. This phase validates the basic mechanism before introducing networking or backend differences.

### Phase 2: cross machine portability

Transfer complete state files without delta synchronization. Test each available pairing independently: CPU to CPU, Metal to Metal, CUDA to CUDA, Metal to CPU, CUDA to CPU, CPU to accelerator. Do not assume results from one pairing apply to another.

### Phase 3: transfer versus replay

For each machine pairing and context length, compare:

- Tier 0: transfer token history and fully prefill the target.
- Tier 1: save, transfer, verify, restore, and continue.

Measure end to end time to first generated token. Repeat under controlled bandwidth and latency conditions.

### Phase 4: delta synchronization

Create a sequence of snapshots after adding fixed token increments: 32, 128, 512, and 1,024 tokens. For each increment, record: full snapshot size, bytes sent by rsync, sender CPU time, receiver CPU time, snapshot time, transfer time, and the ratio to theoretical new KV bytes. Compare rsync with a basis file, rsync without one, full copy, and optional compression.

### Phase 5: planned failover

Perform a coordinated switch after a final verified synchronization. Measure: quiescence time, final delta transfer, restore time, tail prefill time, time to first token, and total user visible interruption. Repoint clients at the gateway layer, the LiteLLM setup from the wiki memory router experiment, so a swap is a backend flip and the client URL never changes. Then reverse the roles; nothing about the loop is direction specific.

### Phase 6: unplanned failover

Terminate the active machine without a final synchronization. Restore the latest verified generation and replay the exact token tail. Measure: tokens lost, tokens replayed, recovery time, and continuation fidelity. The recovery point is bounded by the sync cadence, which is why `tokens.json`, being kilobytes, rides along on every loop iteration.

## Fidelity measurements

Fidelity is evaluated at four levels.

### Restore validity

Did the engine accept the state file without error?

### Logit agreement

At the first continuation position, compare: argmax token agreement, top 5 token overlap, maximum absolute logit difference, mean absolute logit difference, and cosine similarity.

### Token continuation

At temperature zero, compare agreement over 1, 8, 32, and 128 tokens. Report the first divergence position.

### Semantic agreement

For continuations that diverge numerically, compare whether they remain semantically equivalent and factually consistent. Semantic agreement does not replace numerical measurements; it is an additional observation.

## Results

Migration, to be filled in as phases run:

| Source | Target | Backend pairing | Context | Link | Tier 0 TTFT | Tier 1 TTFT | Winner | Restore valid | First divergence |
|---|---|---|---:|---:|---:|---:|---|---|---:|
| Laptop | VPS | Metal to CPU | 1K | TBD | TBD | TBD | TBD | TBD | TBD |
| Laptop | VPS | Metal to CPU | 4K | TBD | TBD | TBD | TBD | TBD | TBD |
| Laptop | VPS | Metal to CPU | 8K | TBD | TBD | TBD | TBD | TBD | TBD |
| VPS | Laptop | CPU to Metal | 8K | TBD | TBD | TBD | TBD | TBD | TBD |

Replication:

| Context before sync | New tokens | Snapshot size | Theoretical new KV | rsync bytes sent | Delta ratio | Snapshot time | Sync time |
|---:|---:|---:|---:|---:|---:|---:|---:|
| TBD | 32 | TBD | TBD | TBD | TBD | TBD | TBD |
| TBD | 128 | TBD | TBD | TBD | TBD | TBD | TBD |
| TBD | 512 | TBD | TBD | TBD | TBD | TBD | TBD |
| TBD | 1024 | TBD | TBD | TBD | TBD | TBD | TBD |

## Interaction with split inference

One caveat from the lab's llama.cpp RPC experiments: in split inference, the KV cache for offloaded layers lives on the RPC backend, not the host. A capsule captured on the host must gather state across the split, and a session resumed into a different split topology is effectively a different engine configuration. Simplest position for now: capsules are captured and restored on single machine sessions, and split sessions fall back to token replay.

## Agent sessions as capsules

A CLI coding agent session is a session in exactly the sense above, plus one thing the chat framing hides: the instructions. Harnesses like [pi](https://github.com/badlogic/pi-mono) assemble their system context at startup from a global `~/.pi/agent/AGENTS.md` and any `AGENTS.md` or `CLAUDE.md` found walking up from the working directory, and store the conversation as JSONL under `~/.pi/agent/sessions/`. Those instruction files are part of the prompt that produced the KV state, so any capsule that omits them cannot replay faithfully on a machine where the files differ.

Which tier an agent capsule could reach is decided by the backend: a harness talking to a hosted API is permanently Tier 0, transcript and instructions only, while one talking to a local `llama-server` could in principle carry engine state. Whether any of that machinery is worth building is deliberately not assumed here. How large agent sessions actually are, what dominates their bytes, and what their derived state would weigh is measured first, as its own experiment: [agent session capsule complexity](experiment-agent-session-capsule-complexity.md).

## Related work

Hot swapping in flight LLM requests between machines is an active research area, and most of it bears on the hypotheses above:

- [Llumnix](https://arxiv.org/abs/2406.03243) (OSDI 2024) live migrates running requests between vLLM instances. Its key trick is the property H3 probes at the serialization layer: the logical KV cache is append only, so it copies the cache for already processed tokens in parallel with ongoing decoding, and the request's downtime shrinks to one iteration's worth of new state. It also measures the naive alternatives, recompute or stop and copy, at over 50x the cost of a decoding step.
- [SpotServe](https://arxiv.org/abs/2311.15566) (ASPLOS 2024) is the closest match to the downtime motivation: it serves LLMs on preemptible spot instances, commits inference progress at the token level, and resumes interrupted requests on surviving machines rather than restarting them.
- [CacheGen](https://dl.acm.org/doi/10.1145/3651890.3672274) (SIGCOMM 2024) is the closest match to the network constraint: it treats KV caches as something to ship over ordinary bandwidth limited links, encodes them into compact bitstreams with a custom tensor codec, and adapts compression to available bandwidth, reporting 3.5 to 4.3x size reduction. This directly informs the compression comparison in Phase 4.
- [Mooncake](https://arxiv.org/abs/2407.00079) (FAST 2025 best paper) and [LMCache](https://blog.lmcache.ai/en/2025/05/08/lmcache-x-mooncake-unite-to-pioneer-kvcache-centric-llm-serving-system/) build entire serving architectures around a disaggregated KV cache pool moved by an RDMA transfer engine, the datacenter scale version of this idea.
- [AttentionStore / CachedAttention](https://arxiv.org/abs/2403.19708) (ATC 2024) and Pensieve persist KV caches of idle conversations to cheaper storage tiers and restore them when the session resumes, cutting time to first token by up to 88 percent. That is the single machine version of a capsule: same save and restore economics, no network hop.
- [ServerlessLLM](https://arxiv.org/abs/2401.14351) (OSDI 2024) attacks the adjacent problem of loading checkpoints fast enough that moving work between machines is viable at all.

What none of this work does is the specific thing proposed here: replicate serialized session state to a standby over a commodity internet link using content defined delta sync, rsync style, between everyday devices. The research systems assume datacenter fabrics, RDMA, or at minimum machines in the same cluster; CacheGen assumes constrained bandwidth but solves it with compression on a one shot transfer, not with incremental replication to a warm replica. The gap makes sense: for a fleet, generic delta sync is less efficient than purpose built transfer engines. For two or three personally owned machines on residential links, rsync is infrastructure that already exists, and whether it is good enough is exactly a long tail question, unglamorous, unpublished, and measurable.

## Security posture

A capsule contains the entire conversation, which is exactly the private prompt material this repo refuses to commit. Capsules are data in flight, never repo content. Transport must be encrypted, capsules should be encrypted at rest on both ends, the manifest hash must be verified before restore, and restoring a state blob from an untrusted source is equivalent to feeding untrusted input to the engine's deserializer and should simply not be done.

## Success criteria

The experiment supports session capsule migration if:

1. State restore succeeds reliably for at least one cross machine pairing
2. Restored continuation is sufficiently faithful for the intended workload
3. Tier 1 beats transcript replay for a measurable region of context lengths and link speeds
4. The measured crossover point can be predicted with reasonable accuracy from the H2 decision rule

Warm standby replication is considered useful only if:

1. Successive snapshots produce meaningful byte reuse
2. Synchronization overhead remains small relative to session runtime
3. Planned or unplanned failover is substantially faster than full replay
4. Standby resource costs are justified by the expected switching frequency

A negative result remains useful. Examples include: state files are not portable across compute backends; serialized snapshots are too unstable for rsync; save and restore overhead dominates transfer savings; full replay wins for realistic context lengths; warm standby cost exceeds its recovery benefit. Each result narrows the conditions under which portable inference sessions are practical.

## Relation to the lab thesis

If sessions can move, the question of where inference runs becomes a per moment routing decision rather than a per conversation commitment: start a conversation on a laptop, escalate the heavy middle to a VPS, and pull it back to the edge for the cheap tail. The capsule is the unit that makes the network tax explicit, one file whose size and transfer time can be weighed directly against the compute it saves. Whether that unit is practical on everyday devices and residential links is not assumed here; it is what the phases above exist to measure.
