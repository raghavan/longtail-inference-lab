# Terminal Artifact Memory Results

**Status:** No runs recorded

This folder will contain measured outputs for Experiment 01. Illustrative diagrams and synthetic planning data are not experiment results.

## Required outputs

1. Frozen model and runtime manifest.
2. Published benchmark subset and task family split.
3. No memory baseline.
4. Sanitized evidence baseline.
5. Distilled wiki baseline.
6. Evidence plus wiki baseline.
7. Learning curves at successive memory checkpoints.
8. Exact recurrence, structural recurrence, and novel control results.
9. Learned judge calibration and held out task family validation.
10. Latency, memory use, and artifact storage measurements.
11. Stress tests, removal tests, and failure analysis.
12. Operational conclusion.

## Primary result table

| Memory checkpoint | Memory condition | Exact recurrence pass rate | Structural recurrence pass rate | Novel control safe response rate | Unsafe confident error rate | Median latency |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | No memory | TBD | TBD | TBD | TBD | TBD |
| 3 | TBD | TBD | TBD | TBD | TBD | TBD |
| 6 | TBD | TBD | TBD | TBD | TBD | TBD |
| 9 | TBD | TBD | TBD | TBD | TBD | TBD |
| 12 | TBD | TBD | TBD | TBD | TBD | TBD |

## Evidence standard

Every published run must identify:

1. Code revision.
2. Benchmark task and task family.
3. Exact model identifier.
4. Quantization.
5. Runtime and version.
6. Device description.
7. Prompt template version.
8. Memory checkpoint.
9. Retrieval configuration.
10. Random seed where applicable.
11. Verifier outcome.
12. Timing and peak memory measurements.

No private session content, credentials, hostnames, local paths, or unsanitized terminal artifacts may be committed.
