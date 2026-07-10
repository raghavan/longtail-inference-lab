# Lab Operations

This Area contains the practices that apply to every Long Tail Inference Lab project.

## Experiment discipline

Every active experiment must define:

1. A bounded research question.
2. A hypothesis or explicit measurement objective.
3. The variables and controls.
4. The metrics to record.
5. A reproducible procedure.
6. A completion condition.
7. Results, limitations, and interpretation.

A design document is not a completed experiment.

## Status discipline

Use these statuses consistently:

```text
Idea
Specified
Running
Analyzing
Complete
Paused
```

Only Specified, Running, and Analyzing work belongs in `projects/`. Complete and Paused work moves to `archives/`.

## Issue discipline

GitHub Issues are execution trackers, not the permanent experiment record.

Each active experiment should have one primary issue. The project folder remains the source of truth for its question, method, and results.

Avoid creating a large speculative backlog. Add a new project only when the current experiments produce a clear next question.

## Reproducibility

Every published run should record:

1. Code revision.
2. Model and quantization.
3. Runtime and version.
4. Device description.
5. Configuration.
6. Input dataset or prompt set.
7. Timestamp.
8. Raw measurements.
9. Analysis method.

## Safety and privacy

Never commit credentials, private network details, session text, private prompts, local file paths, or identifying machine information.

Run:

```bash
python3 scripts/safety_scan.py
```

The safety scan is a guardrail, not a replacement for reviewing the actual diff.

## Publishing results

Negative and inconclusive findings are valid results. Publish enough detail for another person to reproduce the observation and understand its limits.
