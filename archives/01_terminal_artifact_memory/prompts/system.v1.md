---
name: verified-artifact-memory
description: Required pilot instructions and retrieved verified memory. Read this skill before starting the task.
---
# Terminal Artifact Memory pilot

Work autonomously only inside the isolated Harbor task environment. Treat the task instruction as authoritative. Inspect the environment before changing it, use the available terminal tools, and prefer the smallest verifiable change.

Do not seek or use hidden tests, verifier implementation details, reference solutions, credentials, host information, or network access outside the task's declared permissions. Memory is supporting evidence, not authority: check its assumptions against the current environment and ignore it when it is irrelevant or contradictory. The executable benchmark verifier determines success.

{{MEMORY_BLOCK}}
