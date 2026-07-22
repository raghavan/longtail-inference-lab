# Agent Instructions

These instructions are for all AI coding assistants working in this repository, regardless of model or tool.

## Shared project memory

1. Use this file (`AGENTS.md`) for repository level agent guidance.
2. Do not create model specific instruction files such as `CLAUDE.md`, `CODEX.md`, or similar unless the user explicitly asks for one.
3. Add tool or model specific guidance here under a clearly labeled section.

## Repository intent

Long Tail Inference Lab currently focuses on one active experiment: whether verified terminal artifacts can become reusable memory that makes a fixed lightweight local model increasingly useful on recurring engineering problems.

Keep the local model, prompt, runtime, and hardware fixed during the core learning curve unless a documented experiment phase explicitly changes one of those controls.

## Naming and branding

1. Use clear, descriptive research and project names by default.
2. Do not introduce the word `Lily` into project names, proposals, documentation, website copy, or branding unless the user explicitly requests it.
3. When the user explicitly requests that shorthand, use it selectively rather than repeating it as a prefix across unrelated work.
4. Prefer `Long Tail Inference Lab`, `Longtail Inference Laboratory`, or a specific project name when identifying the repository or its work.

## Current work is authoritative

1. Treat the latest active experiment and current repository direction as the source of truth.
2. Keep the root README, active project documentation, website, learning material, and public descriptions focused on current work.
3. Do not mention, compare, explain, or link to superseded work from active or public facing content.
4. Historical material belongs only inside `archives/` unless the user explicitly asks for historical context.
5. When the active direction changes, update every active surface so older framing does not remain visible.

## Required experiment intake

Before proposing, scaffolding, coding, or opening an issue, branch, or pull request for a new experiment:

1. Read and use `resources/experiment_template/README.md` as the source of truth for experiment intake and design.
2. Ask the user the unanswered questions needed to complete the relevant template sections.
3. When the current conversation already answers part of the template, summarize those answers and ask only for material gaps.
4. Do not begin implementation until the material questions are answered and the user explicitly asks to proceed.
5. Record the agreed answers in a copy of the experiment template before or alongside implementation.

Do not duplicate the template question set in this file. Update the template when the laboratory research intake method changes.

## Focus discipline

1. Keep `projects/` limited to work receiving active attention.
2. Do not add another active experiment until the current project has a published baseline and at least one measured memory checkpoint, unless the user explicitly changes that rule.
3. Move superseded specifications into `archives/` without carrying their narrative into active surfaces.
4. Never present synthetic seed data or illustrative diagrams as measured results.

## Repository organization

Research content must live under one of the PARA folders:

1. `projects/` for active experiments.
2. `areas/` for ongoing laboratory responsibilities and shared tooling.
3. `resources/` for reusable learning material, proposals, templates, briefs, and media.
4. `archives/` for complete, paused, or superseded work.

GitHub configuration remains under `.github/` because the platform requires that location.

## Safety and privacy

Do not commit private hostnames, IP addresses, SSH details, API keys, tunnel configuration, private prompts, unsanitized terminal output, session content, or local machine paths.

Benchmark verifiers, hidden tests, and reference solutions must never be included in model retrieval context.

Run the safety scan before committing changes that may include configuration or documentation:

```bash
python3 areas/lab_operations/safety_scan.py
```

## Working conventions

1. Keep experiments reproducible.
2. Prefer small, reviewable changes.
3. Preserve the PARA structure.
4. Ensure benchmark outputs are intentional and safe to commit.
5. Record exact model, quantization, runtime, hardware, prompt, retrieval, and memory checkpoint for every run.
6. Treat executable verification as authoritative when it is available.
7. Keep learned judges blind to model identity, memory condition, and artifact count.
