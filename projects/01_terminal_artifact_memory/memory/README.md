# Approved teacher-derived memory workspace

`wiki/` contains only Markdown pages admitted by `artifact_memory.memory`. `manifests/artifact_index.jsonl` records each page's teacher, verifier, sanitizer, distiller, source-evidence, external-approval, student, split, and page hashes.

Admission requires a qualified preregistered memory-build task executed by `gpt-5.6-sol`, exactly one executable-verifier pass, complete local sanitizer gates, a regenerated allowlisted distillation request, an exact `gpt-5.6-sol` structured Markdown draft, and external human approval scoped to the request/evidence/draft hashes.

Held-out Qwen evaluation tasks can never contribute pages. The M2 runner rejects unadmitted, changed, superseded, legacy, duplicate-build, wrong-split, or held-out-derived memory.

Do not place drafts, raw trajectories, hidden tests, verifier internals, reference solutions, credentials, private infrastructure, scanner details, or index pages in `wiki/`. Follow [`../OPERATOR.md`](../OPERATOR.md).
