# 2026-07-31 measured pilot: halted without a paired result

**Classification: HALTED PILOT — NO M0/M2 RESULT.**

The preregistered checkpoint did not produce measured evidence about memory transfer. The first M0 probe exhausted the fixed context before Harbor could run the executable verifier. The one-attempt budget was therefore consumed by an invalid record, and the protocol required the remaining measured runs to stop rather than rerun, replace, or selectively drop the probe.

## Run accounting

| Stage | Task | Condition | Status | Executable verifier |
| --- | --- | --- | --- | --- |
| Development | `hello-world@1.0` | Oracle | Passed; excluded from results | Passed |
| Development | `hello-world@1.0` | Terminus-2 M0 | Passed; excluded from results | Passed |
| Measured probe | `build-pmars` | M0 | Invalid: context limit exceeded | Not executed |
| Measured probe | `build-cython-ext` | M0 | Not run after stop boundary | Not executed |
| Measured probe | `nginx-request-logging` | M0 | Not run after stop boundary | Not executed |
| Memory builds | Three preregistered tasks | M0 | Not run after stop boundary | Not executed |
| Measured probes | Three preregistered tasks | M2 | Not run | Not executed |

The development checks established that Docker isolation, the oracle path, Terminus-2, ATIF-v1.7 capture, the fixed local endpoint, and executable verification could work together. They are development records and are not included in any metric below.

## Exact measured limitation

The `build-pmars` M0 attempt used the preregistered Qwen 7B Q4_K_M model, 16,384-token context, temperature 0, seed 42, 40-turn limit, disabled summarization, and empty memory. After 11 agent episodes, the next request contained 16,616 tokens, exceeding the fixed 16,384-token context. Harbor recorded `ContextLengthExceededError`, preserved an ATIF-v1.7 trajectory, and did not enter the verifier phase. There is no `reward.txt` and the experiment runner correctly did not write a `paired-result-v1` record.

Changing context size, enabling summarization, shortening the prompt, rerunning the attempt, substituting another probe, or scoring the partial trajectory would violate frozen controls or the one-attempt budget. The attempt is retained only as an invalid-run accounting record; it is not a verifier failure and is not an unresolved-task classification.

## Preregistered metrics

| Metric | Result |
| --- | --- |
| Complete paired probes | 0 of 3 |
| M0 structural pass rate | N/A |
| M2 structural pass rate | N/A |
| Structural memory lift | N/A |
| Positive transfer | N/A |
| Negative transfer | N/A |
| Stable success | N/A |
| Unresolved tasks | N/A |
| Retrieval coverage | N/A |
| Verified memory contributions | 0 |
| Verified knowledge yield | N/A |
| Searchable memory size | 0 bytes |

No transfer class is assigned because each class requires two verifier outcomes. In particular, the invalid M0 attempt is not counted as a failure to manufacture a complete denominator.

## Latency and storage observations

- Development Terminus-2 check latency: 44.742 seconds; excluded from measured results.
- Invalid `build-pmars` attempt wall time recorded by Harbor: 575.006 seconds.
- Invalid attempt aggregate model usage: 103,308 input tokens and 3,541 output tokens across 11 episodes. These are aggregate call totals, not context occupancy.
- Invalid ATIF trajectory size: 60,295 bytes.
- Searchable wiki: 0 pages and 0 bytes.
- Private pilot directory at halt: approximately 74 MB, excluding the separately stored model weights.

Peak host memory was not captured, so no peak-memory observation is reported.

## Safety and completeness review

- No memory-build trajectory ran, so there were no memory candidates and no admission decision to request.
- No page was sanitized, approved, admitted, or retrieved.
- Hidden tests, verifier internals, and reference solutions were not placed in model or retrieval context.
- Raw jobs, trajectories, local manifests, canaries, paths, server logs, and scanner details remain private and uncommitted.
- One invalid measured attempt is present in private storage; five preregistered measured conditions and all build runs are explicitly listed as not run.
- The task-owned model server was stopped by its exact recorded PID.

## Conclusion

This pilot is inconclusive about Terminal Artifact Memory. It provides no evidence for positive transfer, negative transfer, or stable performance because no paired verifier outcome exists.

The immediate limiting factor was not retrieval or memory quality; memory construction never began. It was the incompatibility between the frozen 16,384-token context, disabled summarization, and the Terminus-2 interaction trajectory on the first structural probe.

A future protocol revision should be preregistered as a new run rather than retroactively applied here. Candidate changes include a larger fixed context, an explicitly bounded compaction policy, or a lower turn budget, followed by a fresh baseline from attempt one. This halted pilot must remain visible and must not be pooled with that future protocol as though controls were unchanged.
