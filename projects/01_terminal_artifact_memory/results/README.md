# Terminal Artifact Memory Results

**Status:** No measured runs recorded

This workspace will contain measured outputs for Experiment 01. The primary chart currently uses illustrative planning data and must never be presented as an experiment result.

## Primary result

![Illustrative learning curve showing a fixed local model improving as verified memory grows](../../../resources/assets/terminal_artifact_memory_learning_curve.svg)

The final version of this chart will plot structural recurrence verifier pass rate against the number of verified memory contributions while the model and all core controls remain fixed.

## Required outputs

1. Frozen model and runtime manifest.
2. Published benchmark subset and task family split.
3. No memory baseline.
4. Sanitized evidence baseline.
5. Distilled wiki baseline.
6. Evidence plus wiki baseline.
7. Learning curves at successive memory checkpoints.
8. Exact recurrence, structural recurrence, and novel control results.
9. Verified knowledge yield.
10. Positive and negative transfer counts.
11. Task family memory lift and regressions.
12. Retrieval coverage and model use diagnosis.
13. Learned judge calibration and held out task family validation.
14. Latency, memory use, and artifact storage measurements.
15. Stress tests, removal tests, and failure analysis.
16. Operational conclusion.

## Primary result table

<table>
<thead>
<tr><th>Memory checkpoint</th><th>Memory condition</th><th>Exact recurrence pass rate</th><th>Structural recurrence pass rate</th><th>Novel control safe response rate</th><th>Unsafe confident error rate</th><th>Median latency</th></tr>
</thead>
<tbody>
<tr><td>0</td><td>No memory</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>3</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>6</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>9</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>12</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
</tbody>
</table>

## Paired transfer table

<table>
<thead>
<tr><th>Checkpoint</th><th>Positive transfer</th><th>Negative transfer</th><th>Stable success</th><th>Unresolved</th><th>Net memory benefit</th></tr>
</thead>
<tbody>
<tr><td>3</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>6</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>9</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>12</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
</tbody>
</table>

## Verified knowledge yield

```text
verified knowledge yield
=
additional structural probes passed because of memory
/
verified memory contributions
```

Report both contribution normalized and storage normalized yield at every checkpoint.

## Task family result table

<table>
<thead>
<tr><th>Task family</th><th>M0 pass rate</th><th>M2 pass rate</th><th>Memory lift</th><th>Positive transfer</th><th>Negative transfer</th><th>Retrieval coverage</th></tr>
</thead>
<tbody>
<tr><td>Dependency conflicts</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>Build failures</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
<tr><td>Environment setup</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td><td>TBD</td></tr>
</tbody>
</table>

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
13. Relevant memory pages expected before retrieval.
14. Retrieved memory pages and ranks.
15. Paired M0 and M2 outcome classification.

No private session content, credentials, hostnames, local paths, or unsanitized terminal artifacts may be committed.
