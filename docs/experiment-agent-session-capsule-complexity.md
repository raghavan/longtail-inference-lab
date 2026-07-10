# Experiment: agent session capsule complexity

Before building any transfer machinery for agent sessions, this experiment measures what an agent session capsule actually is: how large sessions are, what they are made of, how they grow over a session's lifetime, and what the derived engine state would weigh if it were ever captured. The output is a dataset, not a system. Future experiments may build on the dataset; nothing is decided now.

## Why measure first

The [session transfer capsule experiment](experiment-session-transfer-capsule.md) defines capsule mechanics for raw model sessions: state files, tiers, delta sync, fidelity. Agent sessions looked like a straightforward extension, a transcript plus the instruction files that shaped it, until the design work made clear how little is actually known about agent sessions as artifacts. Typical sizes: unknown. Growth over a session's life: unknown. Whether tool output or model text dominates the bytes: unknown. Whether derived state would even be worth shipping: unknown. An earlier version of this work jumped straight to a packaging tool; it was removed in favor of this measurement pass, because every design decision it embedded was a guess about exactly these numbers.

## Questions

- How large is a typical agent session transcript, and what is the distribution across sessions: median, p95, maximum?
- What dominates the bytes: user text, model text, tool output, or instruction files?
- How does size grow with turns? Is per turn size roughly stationary, or heavy tailed, where one pasted log or one large tool result outweighs fifty ordinary turns?
- How many tokens does the final context hold, and what would the derived KV state weigh for reference local models?
- How compressible is each component?
- What is the amplification ratio per session: derived state bytes over transcript bytes?

## The dataset

Metrics only. The extraction reads session files and writes numbers; no session content, no message text, no file paths from inside conversations ever enters the dataset. That rule is what makes the dataset committable to this repo under its safety posture. Session identity is a truncated hash, so rows can be correlated across the two files without naming anything.

Source material is pi coding agent sessions, stored as JSONL under `~/.pi/agent/sessions/`, one JSON object per line with a type field, which makes metrics extraction a single pass per file. Other harnesses with inspectable session formats can be added as further rows with a different harness value; the schema does not assume pi.

### `sessions.csv`, one row per session

| Column | Meaning |
|---|---|
| session_key | truncated sha256 of file identity, no content |
| harness | pi, or other harnesses later |
| model | model identifier the session ran against |
| messages | total entries |
| turns | user visible request and response cycles |
| tool_calls | tool invocation count |
| transcript_bytes | raw JSONL size |
| gzip_bytes | gzipped JSONL size |
| user_bytes | bytes of user authored content |
| assistant_bytes | bytes of model authored content |
| tool_bytes | bytes of tool results |
| instruction_bytes | bytes of AGENTS.md and CLAUDE.md files in scope at session time |
| final_context_tokens | from harness recorded usage where present, else estimated and flagged |
| tokens_estimated | whether the previous column is an estimate |

### `turns.csv`, one row per turn

| Column | Meaning |
|---|---|
| session_key | joins to sessions.csv |
| turn_index | position in the session |
| role | user, assistant, or tool |
| bytes | this turn's size |
| cumulative_bytes | transcript size after this turn |

Token counts come from the harness where its entries record usage; where they do not, the estimate is bytes divided by four and the row is flagged, so estimated and measured rows are never mixed silently.

Derived state weights are computed columns, not measurements: final context tokens multiplied by the per token KV cost of reference models, 56 KB per token for Qwen2.5 7B at F16 and 128 KB per token for Llama 3 8B at F16, halved for q8_0, per the sizing section of the transfer experiment. Keeping them as derived columns means new reference models can be added without touching any session again.

## Analysis dimensions

### Scaling with turns

Transcript growth should be roughly linear in turns if per turn sizes are stationary. The interesting question is whether they are: coding agent tool output is plausibly heavy tailed, one build log or file dump outweighing many turns of conversation, in which case medians and p95s diverge sharply and the mean is misleading. `turns.csv` exists to settle this.

There is a second, less visible growth curve. An agent backed by a hosted API re sends its entire context on every request, so the total tokens processed over a session's lifetime grows roughly quadratically in turns even while the transcript grows linearly. The dataset makes the actual exponent measurable from cumulative bytes per turn. That number is the baseline any future caching or state transfer idea would be judged against, and it is worth knowing even if nothing is ever built.

### Composition

What fraction of each session is user text, model text, tool output, and instructions. The hypothesis worth checking, not assuming: tool output dominates coding agent sessions, and instructions are a rounding error per session but a fixed cost every session pays.

### Derived state weight

The transfer experiment quotes a worked example where a model's KV state is four to five orders of magnitude larger than the text that produced it. This experiment measures the actual distribution of that amplification ratio across real sessions rather than one arithmetic example. Sessions where the ratio is extreme are the ones where state transfer could matter; sessions where the final context is small are the ones where replay is trivially cheap and no machinery is warranted.

### Compressibility

gzip ratio of the full transcript and of each component separately. Text and JSONL structure should compress well; if tool output dominates and compresses even better, log text is repetitive, then a compressed Tier 0 agent capsule may be small enough that nothing beyond it is ever needed for agent sessions. That would be a useful negative result for the transfer direction.

## Results

To be filled in as sessions are measured:

| Quantity | Value |
|---|---:|
| Sessions measured | TBD |
| Median transcript bytes | TBD |
| p95 transcript bytes | TBD |
| Median turns per session | TBD |
| Tool output fraction of bytes, median | TBD |
| gzip ratio, median | TBD |
| Final context tokens, median | TBD |
| Derived KV at Qwen2.5 7B F16, median | TBD |
| Amplification ratio, median | TBD |
| Per turn bytes, median and p95 | TBD |

## What this is not

No transfer tooling, no replication loop, no capsule format for agent sessions, and no commitment that any of those get built. If the dataset shows agent sessions are small and replay is cheap, agent capsule transfer is uninteresting and this experiment will have cost a few hours instead of a system. Each such result narrows where the transfer work should aim. Future experiments build on this dataset only after it exists.

## Relation to the lab thesis

This is the lab's measurement posture applied to its own tooling: the same discipline of measuring the network tax before believing in distributed inference, aimed at agent sessions before believing in agent session transfer. The dataset is small, safe to commit, and accumulates value the way the wiki memory router's cache does, every future question about agent session behavior starts from data already on disk.
