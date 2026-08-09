# Results

**No measurements exist for this project.**

No hardware has been ordered and no interaction has been recorded. Every number in this project is a target, a budget, or a threshold until a dated results folder appears here.

## What will be published

Each measured run gets a dated folder containing:

1. `provenance.json` — hardware, JetPack version, power mode, model identities with revisions and file hashes, runtime versions, prompt hash, question set hash, ambient conditions, and condition and block order.
2. `interactions.jsonl` — one line per interaction with the full per-stage latency ledger.
3. `resources.csv` — the 100 ms sampling of memory, temperature, and input power.
4. `offline-assertion.log` — interface packet counter deltas per interaction.
5. `summary.md` — distributions with p50, p95, p99, and maximum, the per-stage breakdown at p50 and p95, stress curves, removal analysis, and the operational conclusion.

## Publication rules

1. Negative, halted, and inconclusive results are published with the same prominence as positive ones. A device that is unusably slow is a result.
2. Discarded blocks are listed with the reason for discarding them.
3. A block with a nonzero offline packet delta is not published as a result until the cause is explained.
4. No raw audio is committed. Only synthetic or explicitly approved recordings may appear here.
5. No illustrative chart is presented as a measurement.
