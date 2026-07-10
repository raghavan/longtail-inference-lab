# Future directions: novel arenas for the lab

This doc surveys where the lab could go next. It starts from what the existing experiments reveal about the lab's point of view, checks that against where the field moved in 2025 and 2026, and proposes arenas that are both a natural fit and genuinely under-explored.

## The lab's point of view, as revealed so far

Reading the thesis, the experiment list, and the wiki memory router doc together, a few commitments are visible:

- **Systems metaphors applied to inference.** The wiki memory router treats knowledge as a cache with hit paths, miss paths, eviction, and regret metrics. This habit of borrowing distributed-systems vocabulary is the lab's most distinctive asset.
- **Measurement over advocacy.** The thesis explicitly refuses to claim everyday devices replace data centers. The question is always "where is local genuinely good enough, and what does it cost to find out."
- **Economics as a first-class metric.** Network tax, routing regret, escalation cost. The lab cares about the price of a token, not just its latency.
- **Tiering.** Local ↔ frontier escalation shows up in the routing experiments and the wiki router alike.
- **Human-reviewable substrates.** Markdown memory, pull-request write-back, safety scans. Knowledge changes go through review like code does.

## What changed in the field

Three shifts since the lab's initial experiment list matter for choosing what's next:

1. **Small models got genuinely useful, and the constraint moved.** Sub-billion-parameter models now handle real tasks, NPUs ship in every flagship device, and the binding constraint on everyday hardware is memory bandwidth (roughly 50–90 GB/s on mobile versus 2–3 TB/s in the data center), not TOPS. Decode is memory-bound, so everyday devices are structurally bad at interactive decode but much less handicapped at throughput-insensitive work.
2. **Routing and cascades became a crowded academic lane.** RouteLLM-style routers, decision-theoretic cascade analyses, and dedicated routing benchmarks all landed in 2025–26. Pure "which model should answer this" work now needs differentiation to be interesting.
3. **Distributed speculative decoding arrived as the new split-inference primitive.** Multiple 2025–26 papers (DSSD, DiP-SD, privacy-aware split inference over WANs) split the draft/verify loop across device and edge rather than splitting layers. Almost all of it is simulation or lab-network work; practitioner-grade measurements on real consumer links barely exist.

## Recommended arenas

Ordered by fit-times-novelty, each with the systems framing and a first experiment small enough to actually run.

### 1. The network tax on speculation

Layer-split inference (the current llama.cpp RPC experiment) ships activations across the wire every token, so the network tax is paid constantly. Split speculative decoding changes the unit of exchange: a small local draft model generates tokens cheaply, and a remote verifier (VPS or frontier API) checks batches of them. The wire now carries candidate token sequences, and the tax is paid per verification round, amortized across accepted tokens.

The arena: measure, on real consumer WAN links, when draft-local/verify-remote beats (a) everything local, (b) everything remote, and (c) layer splitting. Variables: draft model size, acceptance rate by task type, round-trip time, batch-of-drafts size. The academic work simulates 0–50 ms RTT on capped links; a lab that owns real laptops, real VPSes, and real home internet can publish the numbers the papers can't.

This is the single best next experiment: it directly extends existing infrastructure, sits exactly on the lab's thesis, and the practitioner measurement gap is real.

### 2. The night shift: latency-tolerance as the routing dimension

The field's routing literature routes on difficulty. Almost nobody routes on **deadline**. Everyday devices are memory-bandwidth-starved for interactive decode but perfectly adequate for work that has hours of slack: summarizing, indexing, embedding, eval runs, wiki distillation, batch classification. The systems metaphor is the batch tier — the overnight cron job of inference.

The arena: build a taxonomy of personal/team inference workloads by latency tolerance, then measure what fraction of total daily tokens is actually deadline-insensitive. Run that fraction on idle laptop hours and measure cost displaced versus the frontier baseline. Hypothesis worth testing: the long tail of compute is more valuable as a *throughput* tier than a *latency* tier, and most measurements to date have asked the wrong question by benchmarking interactive chat.

This also composes with the wiki memory router: the write-back distillation step is itself a night-shift job.

### 3. Knowledge half-life: staleness as cache invalidation

The wiki router doc's open questions list staleness detection as unsolved, and the 2026 agent-memory literature (experience reuse, memory-as-asset) has the same hole: everyone writes to memory, almost nobody measures decay. Cached knowledge that has gone wrong is worse than a cache miss — the doc already says this; the arena is to make it measurable.

The arena: define and measure the **half-life of a wiki entry** — how long until a distilled answer stops matching a fresh frontier answer to the same question. Instrument entries with created-at and last-verified-at metadata, re-ask a sample of cached questions on the frontier path on a schedule, and diff. Then design invalidation policies (TTL by topic volatility, re-verify on retrieval count, dependency links between entries) and measure which policy keeps quality flat at lowest re-verification spend. This turns the wiki router from an architecture doc into the lab's flagship original research, and the human-reviewable-PR write-back is a genuinely distinctive twist no academic memory system has.

### 4. The energy tax: watts per token at the long tail

The lab measures the network tax; the unmeasured sibling is the energy tax. Data-center inference economics are covered exhaustively, but almost nobody publishes joules-per-token for a MacBook, a mini PC, a Pi with an NPU hat, or a VPS slice — measured at the wall, not from spec sheets.

The arena: a smart plug, a fixed eval workload, and a table of watts-per-token and cents-per-million-tokens across the device inventory (which the lab already has a probe experiment for). Then the interesting second-order question: does the local-versus-frontier cost comparison flip when local electricity is counted honestly, and does it flip back with off-peak or solar scheduling? This composes with the night shift arena — deadline-insensitive work can also be energy-price-aware.

### 5. Privacy-tiered routing: route on sensitivity, not just difficulty

The routing literature routes on question difficulty; the lab's own safety posture suggests a second axis it is unusually well positioned to explore: data sensitivity. Some questions should never leave the laptop regardless of how hard they are, which inverts the usual cascade — the tail question that is also private must be answered by the *best local* path, and the interesting measurement is how much quality that constraint costs.

The arena: extend the head/tail classifier with a sensitivity classifier (does the prompt contain private code, credentials-shaped strings, personal data), route accordingly, and measure the quality gap on the forced-local slice. This produces a number the field lacks: **the privacy premium** — the quality you pay for keeping a query local, as a function of local model size.

### 6. KV and prefix caches as shippable artifacts

One level below the wiki cache sits another cache with unexplored distribution semantics: the KV/prefix cache. Serving stacks reuse prefix caches within one server; nobody treats a precomputed KV cache as an artifact that can be built once on a strong machine and shipped to weak ones — a CDN for attention states.

The arena: for a stable system prompt plus wiki context, precompute the KV cache on the VPS, ship it to the laptop, and measure time-to-first-token versus recomputing the prefill locally. The systems questions write themselves: what does a KV cache cost on the wire versus the tokens it encodes, when does shipping beat recomputing (prefill is compute-bound, which is exactly where weak devices hurt), and what invalidates it (model version, quantization variant). This is the most technically speculative arena of the six — llama.cpp's cache serialization makes a first probe feasible, but cross-machine portability constraints may bite early. High novelty if it works.

## What to deprioritize

- **Generic device leaderboards.** Tier lists for edge boards and mobile LLM leaderboards are now well covered by others; the lab adds little by re-running them.
- **Pure difficulty-based routing.** RouteLLM-descendant work is crowded. Routing stays interesting here only when the lab adds an axis the literature lacks: deadline (arena 2), sensitivity (arena 5), or energy price (arena 4).
- **Building a general split-inference framework.** exo and Petals exist. The lab's edge is measurement and framing, not framework maintenance.

## Suggested sequence

1. **Knowledge half-life (arena 3)** — deepens the flagship experiment already in flight; cheapest to start since it is mostly instrumentation.
2. **Network tax on speculation (arena 1)** — the natural successor to the llama.cpp RPC experiment.
3. **Energy tax (arena 4)** — one smart plug away, and its numbers feed every other arena's cost model.
4. **Night shift (arena 2)** — once energy and routing data exist, the batch-tier claim can be tested honestly.
5. **Privacy premium (arena 5)** and **shippable KV caches (arena 6)** — as follow-ons once the measurement substrate exists.

## Pointers into the literature

- Distributed split speculative decoding: [DSSD (ICML 2025)](https://arxiv.org/pdf/2507.12000), [DiP-SD](https://arxiv.org/pdf/2604.20919), [privacy-aware split inference over WANs](https://arxiv.org/html/2602.16760)
- Routing and cascades: [decision-theoretic cascade characterization](https://arxiv.org/pdf/2605.06350), [LLMRouterBench](https://arxiv.org/html/2601.07206v1), [small models as front-door routers](https://arxiv.org/html/2604.02367), [privacy-preserving LLM routing](https://arxiv.org/pdf/2604.15728)
- Agent memory and experience reuse: [continual learning via memory in LLM agents](https://arxiv.org/html/2604.27003), [modular memory position paper](https://arxiv.org/pdf/2603.01761), [memory as asset](https://arxiv.org/pdf/2603.14212)
- State of on-device inference: [On-Device LLMs: State of the Union 2026](https://v-chandra.github.io/on-device-llms/), [edge LLM survey (ACM Computing Surveys)](https://dl.acm.org/doi/full/10.1145/3719664), [network edge inference survey](https://arxiv.org/html/2604.22906v1)
