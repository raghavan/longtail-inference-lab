# Agent Instructions

These instructions are for all AI coding assistants working in this repository, regardless of model or tool.

## Shared project memory

- Use this file (`AGENTS.md`) for repository-level agent guidance.
- Do not create model-specific instruction files such as `CLAUDE.md`, `CODEX.md`, or similar unless the user explicitly asks for one.
- If guidance is specific to a tool or model, still add it here under a clearly labeled section instead of creating a separate model-specific file.

## Repository intent

Long Tail Inference Lab explores edge LLM inference, open-weight model serving, laptop/VPS split inference, routing, benchmarking, and long-tail compute across everyday devices.

## Safety and privacy

- Do not commit private hostnames, IP addresses, SSH details, API keys, tunnel configuration, private prompts, or local machine paths.
- Run the safety scan before committing changes that may include configuration or docs:

```bash
python3 scripts/safety_scan.py
```

## Working conventions

- Keep docs and experiments reproducible.
- Prefer small, reviewable changes.
- Preserve the repository's simple structure unless the user asks for a larger scaffold.
- When adding benchmark outputs, ensure they are intentional and safe to commit.
