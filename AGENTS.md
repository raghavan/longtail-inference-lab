# Agent Instructions

These instructions are for all AI coding assistants working in this repository, regardless of model or tool.

## Shared project memory

1. Use this file (`AGENTS.md`) for repository level agent guidance.
2. Do not create model specific instruction files such as `CLAUDE.md`, `CODEX.md`, or similar unless the user explicitly asks for one.
3. Add tool or model specific guidance here under a clearly labeled section.

## Repository intent

Long Tail Inference Lab explores how everyday devices, local models, durable memory, session state, and selective frontier escalation can absorb long tail inference work.

## Repository organization

Research content must live under one of the PARA folders:

1. `projects/` for active experiments.
2. `areas/` for ongoing lab responsibilities and shared tooling.
3. `resources/` for reusable learning material, proposals, templates, and media.
4. `archives/` for completed, paused, or superseded work.

GitHub configuration remains under `.github/` because the platform requires that location.

## Safety and privacy

Do not commit private hostnames, IP addresses, SSH details, API keys, tunnel configuration, private prompts, session content, or local machine paths.

Run the safety scan before committing changes that may include configuration or documentation:

```bash
python3 areas/lab_operations/safety_scan.py
```

## Working conventions

1. Keep experiments reproducible.
2. Prefer small, reviewable changes.
3. Preserve the PARA structure.
4. Ensure benchmark outputs are intentional and safe to commit.
