# Experiment 02.1 — Spoken response latency and residency policy

**Status:** Specified — hardware not ordered, zero measurements taken
**Track:** Edge inference and device systems
**Difficulty:** Advanced
**Owner:** Long Tail Inference Lab
**Last updated:** August 9 2026

## One minute summary

**Question:** On a fixed Jetson Orin NX 16 GB running a fixed modular voice pipeline, what is the distribution of button-release-to-first-spoken-word latency, and does keeping all three models resident reduce it enough to justify the complexity compared with sequential load and unload?

**Decision:** whether the shipped device keeps models resident, whether 16 GB is actually required, and which pipeline stage receives engineering effort next.

**Workload:** forty scripted spoken questions of the kind the device is meant for — definitions, explanations, comparisons, short reasoning, general recall — spoken by the operator at close range in a quiet room.

**Success boundary:** the best condition reaches p95 first-word latency at or below 8.0 s with no outbound network packet and no thermal or memory failure.

**Stop boundary:** no condition reaches p95 at or below 12.0 s. That result says the modular pipeline is the wrong architecture on this hardware, and no enclosure, battery, or audio work should proceed until the architecture question is reopened.

## Research question

On a fixed Jetson Orin NX 16 GB device running a fixed modular pipeline of local speech recognition, a four-bit quantized compact instruct model, and local speech synthesis, under scripted close-range spoken questions with all network interfaces disabled:

**How is button-release-to-first-spoken-word latency distributed, and how does that distribution change across model residency policy and speech synthesis granularity?**

1. **System:** the complete local voice loop, measured end to end rather than per model.
2. **Workload:** forty scripted spoken questions representative of brief personal assistant use.
3. **Outcome:** first-word latency distribution, plus peak memory, energy per interaction, thermal behavior, and offline integrity.
4. **Comparison:** sequential model loading against full residency, crossed with whole-answer against sentence-streamed synthesis.
5. **Conditions:** mains power, quiet room, ambient 20–25 °C, a single fixed power mode, reference USB audio.

## Why this belongs in the lab

The lab studies where local inference is useful, insufficient, fragile, or unnecessarily complex. This experiment targets the last two directly.

A voice appliance is one of the few systems where latency is not a metric that a user tolerates in the background: it is the product. A person holding a small object and waiting in silence experiences a delay far more sharply than the same delay in a text interface. So the tail matters more than the mean, and the honest measurement is p95, not the demo run that went well.

The experiment also tests whether a capability the lab paid for — the extra memory — actually changes anything. That is exactly the kind of question the removal test in the lab template exists to ask, and answering it against our own hardware purchase keeps the method honest.

## Practical context

1. **Who experiences the problem:** a person away from connectivity who wants a spoken answer without a phone, an account, or a network.
2. **What they are trying to accomplish:** a brief, useful exchange — one question, one concise spoken answer, in a few seconds.
3. **The constraint that matters:** perceived delay first, then energy and heat, because those bound portable use.
4. **What happens today:** every mainstream voice assistant is a terminal for remote infrastructure and degrades to useless without network. There is no baseline in this lab for what a fully local loop actually costs in seconds and joules on this class of hardware.
5. **Why now:** the compute tier has been chosen and is about to be purchased. Measuring the loop before designing power, enclosure, and audio prevents building an object around an unusable interaction.

## Decision being informed

1. **If the evidence supports residency:** the device keeps all three models resident, 16 GB is justified and retained in the refined design, and the controller carries the memory-management complexity that residency implies.
2. **If the evidence does not support residency:** the device loads sequentially, the controller stays simpler, and the project records that the 8 GB part would have been sufficient — including the cost consequence of having bought otherwise.
3. **If the evidence is mixed or incomplete:** publish the per-stage latency ledger and target the single stage that dominates p95 before making any residency commitment.
4. **This experiment will not justify:** any claim about answer quality, factual accuracy, speech recognition accuracy across speakers or accents, battery life, enclosure thermals, or the viability of the tiny audio module. It measures one speaker, one room, one reference audio path, and one power mode.

## What you will learn

1. What a complete local voice loop actually costs in seconds, watts, and gigabytes on current compact edge hardware.
2. How to decompose an interactive pipeline into a per-stage latency ledger so that a slow system names its own bottleneck.
3. How to test an offline claim as an assertion with evidence rather than as a marketing label.

## Hypothesis

**H1 (residency):** full residency reduces p95 first-word latency by at least 1.5 s compared with sequential loading, holding synthesis policy fixed.

**H2 (streaming):** sentence-streamed synthesis reduces p95 first-word latency by at least 1.0 s compared with whole-answer synthesis, holding residency policy fixed.

**H3 (interaction, directional):** the two effects are not additive. Streaming captures most of the available improvement, because it removes a wait proportional to answer length, while residency removes a fixed one-time cost. If H3 holds, the resident and sequential conditions converge once streaming is enabled, and residency is not worth its complexity.

H3 is the hypothesis the project most wants to be true, which is precisely why it must be stated in advance and tested with the same rigor as the others.

## Assumptions and model error

1. **What makes the measurement valid:** stage timestamps come from one monotonic clock in one process; the audio path adds a constant, separately measured offset; the question set is fixed and spoken consistently.
2. **What would invalidate it:** speech recognition failing often enough that retries dominate; the answer model producing wildly varying answer lengths that correlate with condition; USB audio buffer underruns; thermal throttling changing behavior partway through a run.
3. **Variables that are not observable:** internal runtime scheduling, memory fragmentation across long runs, and any firmware-level audio buffering inside the USB device.
4. **Sensitivity to measurement error:** the software-to-acoustic offset is expected to be tens to low hundreds of milliseconds. Against an 8.0 s target that is tolerable, but it must be measured once and reported rather than assumed. Differences smaller than the measured offset are not claims.
5. **Where not to generalize:** a different speaker, a noisy room, a different audio device, a different power mode, or a different model family. Nothing here transfers to the tiny audio module.
6. **What we may be pretending to know:** that scripted questions spoken by the person who wrote them resemble real use. They almost certainly do not, in a direction that flatters the device — the operator articulates clearly and asks answerable questions. The daily use pilot exists to correct this, and this experiment must not be described as evidence of daily usability.
7. **Proxy measurements that could be mistaken for the real outcome:** first-word latency is a proxy for perceived responsiveness, but a fast first word followed by a stall reads as broken. Time to the first complete sentence is therefore recorded alongside it, and a run with a mid-answer gap above 700 ms is flagged even when its first-word latency is good.

## Tail characteristics

### Demand tail

Questions that are long to speak, ambiguous enough to produce a long answer, or contain proper nouns that stress speech recognition. These are the interactions where the device feels slowest, and they are underrepresented in any hand-written question set. The set therefore includes a deliberate long-question stratum.

### Resource tail

Long answers dominate energy and total time. Report the share of total energy consumed by the longest decile of interactions. If a small fraction of answers consumes a large share of the energy budget, capping answer length becomes a power decision and not only a style decision.

### Failure tail

1. Out-of-memory termination requiring a reboot.
2. Thermal throttling mid-interaction.
3. USB audio dropout producing unintelligible or truncated speech.
4. Runaway generation that never terminates.
5. Answer audio from a previous interaction leaking into the current one.

Report median, p95, p99, and maximum for every latency and energy metric. Averages alone are not acceptable output for this experiment.

## Ruin boundary

Outcomes unacceptable regardless of average performance:

1. **Any outbound network packet during a measured interaction.** The offline claim is the product. Detection: an interface-level packet counter sampled before and after each interaction, with a full capture retained for any nonzero delta. A single nonzero delta invalidates the run and blocks publication until explained.
2. **Raw audio persisting after transcription outside development mode.** Detection: a post-run filesystem scan of the audio scratch path.
3. **Sustained surface temperature above 45 °C on any user-touched face.** Detection: an infrared reading at the end of the sustained-load stress block.
4. **Answer audio bleeding between interactions.** Detection: a per-interaction nonce in the answer log compared against the played transcript.
5. **A crash that requires physical intervention.** Detection: watchdog log plus reboot count.

None of these may be traded for lower latency. A condition that wins on latency and crosses a ruin boundary is recorded as a failure of that condition, not as a win with a caveat.

## Path dependence

Earlier events can change the result, so the protocol controls for them:

1. **Cold versus warm start:** the first interaction after boot is recorded separately and excluded from the primary distribution, and reported as its own statistic.
2. **Interaction order:** the question set is run in a fixed order for one repeat and a shuffled order for another, so ordering effects are visible.
3. **Thermal history:** each condition begins from a defined idle-temperature window, and the block order across conditions is rotated so no condition is always measured on a hot device.
4. **Memory history:** for sequential conditions, the runtime is restarted between blocks so fragmentation does not accumulate asymmetrically.
5. **Conversation history:** the primary measurement is single turn with no carried context. Multi-turn appears only in the stress phase.

## Variables and controls

### Changes between runs

1. Residency policy: sequential load and unload, or all three models resident.
2. Speech synthesis policy: whole answer synthesized before playback, or first sentence synthesized and played while the rest generates.

### Held fixed

1. Exact hardware, including compute module, carrier, storage, and audio device.
2. JetPack version and power mode, both recorded.
3. Fan profile.
4. Exact model identities, quantizations, and file hashes for speech recognition, answer generation, and speech synthesis.
5. Runtime versions, pinned.
6. System prompt text, decoding parameters, and maximum answer token cap.
7. Question set, speaker, microphone distance, room, and ambient temperature window.
8. Mains power throughout. No battery in this experiment.

### External factors that may influence the result

Ambient temperature drift, background acoustic noise, speaker vocal variation across a long session, and USB power delivery stability.

### Uncontrolled variation

Human speech differs on every utterance. This is addressed with repeats rather than eliminated.

### Repeats

Forty questions × three repeats × four conditions = 480 measured interactions, plus a discarded warm-up block per condition. Three repeats is the minimum that shows run-to-run spread; if the interquartile range within a question exceeds 1.5 s, repeats increase to five before any conclusion is drawn.

## Workload and evidence source

1. **Origin:** forty questions written for this experiment, drawn from the day-to-day uses in the design direction — explain, define, compare, decide, rephrase, recall.
2. **Representativeness:** they match the intended use in shape and length, but not in spontaneity. See the assumption above.
3. **Privacy transformation:** none needed. The questions are public and synthetic, contain no personal content, and are spoken by the operator.
4. **Missing cases:** other speakers, accents, non-English speech, noisy environments, interrupted speech, and questions the model cannot answer.
5. **Role of synthetic input:** the question set is the primary evidence for latency. It is not evidence for recognition accuracy in the field.

The question set is committed as `evaluations/question_set.jsonl` with four strata — short, medium, long, and proper-noun-heavy — ten questions each.

## Instrumentation

### The latency ledger

Every interaction emits one JSON line with monotonic timestamps at each boundary:

| Stage | From | To |
| --- | --- | --- |
| `capture` | button press | button release |
| `endpoint` | button release | recording finalized |
| `stt_load` | recognition model load start | load complete (zero when resident) |
| `stt_compute` | transcription start | transcript available |
| `prompt` | transcript available | prompt constructed |
| `llm_load` | answer model load start | load complete (zero when resident) |
| `llm_prefill` | generation request | first token |
| `llm_first_sentence` | first token | first sentence boundary |
| `tts_load` | synthesis model load start | load complete (zero when resident) |
| `tts_first_chunk` | synthesis start | first audio chunk ready |
| `audio_out` | first chunk queued | first sample submitted to the audio device |

**Primary metric** `t_first_word` is the sum from button release to first sample submitted, plus the measured acoustic offset.

This decomposition is the point of the experiment. A single end-to-end number tells the project that it is slow; the ledger tells it what to fix.

### Acoustic offset calibration

Once per hardware configuration, record an interaction with an external recorder capturing both a mechanical click on button release and the first spoken word. The difference between the acoustic interval and the logged software interval is the offset. Report it with its standard deviation across ten calibration interactions, and add it to every reported latency.

### Resource sampling

Sample at 100 ms throughout each interaction and for 2 s after: total memory used, swap, per-process resident memory, SoC and module temperatures, clock states, and input power in milliwatts. Energy per interaction is the integral of input power over the interaction window, reported in joules.

### Offline assertion

Before the block: disconnect Ethernet, disable the wireless radio at the hardware level, and remove all name resolution. During the block: read interface packet counters before and after every interaction and record the delta. A nonzero delta triggers a full packet capture and blocks publication of that block.

## Experiment sequence

### Phase 1: observe the current system

Build the loop in its simplest honest form — sequential loading, whole-answer synthesis, reference USB audio — and measure it offline. This is the baseline a practitioner would get by wiring together the obvious parts, and it is the number every later claim is compared against.

### Phase 2: test the smallest useful intervention

Enable residency and sentence streaming independently, then together. Four conditions, block-rotated, same question set, same day where possible.

### Phase 3: stress and fragility tests

Worsen realistic conditions one at a time and record whether performance degrades gradually or collapses:

1. **Sustained load:** twenty interactions in ten minutes, watching for thermal throttling and creeping latency.
2. **Long questions:** thirty-second utterances.
3. **Long answers:** raise the token cap and observe the effect on first-word latency, which should be flat under streaming and rise without it.
4. **Multi-turn context:** three-turn conversations with carried context.
5. **Acoustic noise:** measured background noise at a defined level.
6. **Power mode:** repeat the winning condition at a lower power mode to expose the latency-versus-energy trade.
7. **Cold start:** first interaction after boot, measured separately.

### Phase 4: removal test

1. Does sentence streaming alone, without residency, reach the target? If yes, residency is unjustified complexity.
2. Does a smaller recognition model make residency irrelevant by shrinking load cost?
3. Which single stage dominates p95, and would fixing only that stage meet the target without either intervention?
4. Would doing nothing be reasonable — that is, does the naive baseline already pass?

### Phase 5: analysis and decision

Compare all conditions on the full distribution, not the mean. Report the per-stage ledger for the median and the p95 interaction of every condition, so the tail is explained rather than merely reported.

## Metrics

| Metric | Unit | Direction | Threshold | Expected error | Tail risk |
| --- | --- | --- | --- | --- | --- |
| `t_first_word` | s | lower | p95 ≤ 8.0 target, ≤ 12.0 stop | acoustic offset, tens of ms | primary; report p50/p95/p99/max |
| `t_first_sentence` | s | lower | p95 ≤ 10.0 | as above | guards against a fast word then a stall |
| `t_complete` | s | lower | p95 ≤ 20.0 | as above | correlates with answer length |
| `gap_max` | ms | lower | ≤ 700 within an answer | buffer granularity | a mid-answer gap reads as a fault |
| `peak_memory` | GB | lower | must not reach the out-of-memory boundary | sampling misses sub-100 ms spikes | decides whether 16 GB is required |
| `energy_per_interaction` | J | lower | recorded, no threshold in this experiment | rail sensing accuracy | sizes the future battery |
| `idle_power` | W | lower | recorded | as above | dominates standby life |
| `soc_temp_max` | °C | lower | below the throttle point | sensor placement | drives enclosure design |
| `surface_temp_max` | °C | lower | ≤ 45 ruin boundary | IR emissivity | user safety |
| `stt_success_rate` | fraction | higher | ≥ 0.90 validity gate | operator judgement | below this, latency data is not interpretable |
| `offline_packet_delta` | packets | zero | exactly 0, ruin boundary | none | absolute |

`stt_success_rate` is a validity gate rather than a result. If recognition fails on more than one question in ten, the latency distribution is measuring retries and the run is void.

## Reproduce

Recorded for every run: hardware identifiers by model name, JetPack version, power mode, fan profile, kernel version, runtime versions and commits, model repository identities with revision and file hashes, quantization, system prompt file hash, decoding parameters, token cap, question set file hash, ambient temperature, microphone distance, condition, block order, repeat index, and random seed where the runtime accepts one.

Commands, configuration files, and the analysis script are committed with the experiment when implementation begins. Private paths, hostnames, and device serial numbers are replaced with placeholders before commit, and `python3 areas/lab_operations/safety_scan.py` runs before every commit.

## Results

No results exist. This section will link raw per-interaction ledger lines, the derived distribution tables, per-stage breakdowns at p50 and p95, stress curves, the removal analysis, the offline assertion log, and any discarded blocks with the reason for discarding them.

Negative and inconvenient results are published. If the device is unusably slow, that is the result.

## Operational conclusion

To be completed after measurement, as a decision record covering evidence observed, decision supported, decision not supported, safe operating region, escalation conditions, and confidence.

The conclusion must explicitly state whether the 16 GB purchase was justified by the measurement, including when it was not.

## Limitations and open evidence

1. One speaker, one room, one language, one audio path.
2. Latency only. No claim about answer quality, factuality, or recognition accuracy in the field.
3. Mains power. Nothing here predicts battery behavior under peak load.
4. No enclosure, so thermal results will not transfer to the finished object.
5. A scripted question set flatters the device relative to spontaneous speech.
6. Results are specific to the chosen model versions and runtimes, both of which move quickly.

## Completion condition

1. A published baseline for the naive sequential, whole-answer condition.
2. All four conditions measured with full distributions.
3. Tail and failure analysis including p95 stage breakdowns.
4. At least one stress block and the removal test.
5. An operational conclusion including the residency and memory-tier verdict.
6. Limitations and open questions.
7. A clear statement of what happens next.

## Next smallest question

If the target is met, the next question is the tiny audio module: does the Atom VoiceS3R reach word error rate and intelligibility within a defined margin of the reference path, and what does attaching it actually require?

If the target is missed, the next question is whichever stage dominates p95 — most plausibly recognition compute or answer prefill — measured on its own before any further device work.
