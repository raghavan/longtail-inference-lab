# Ignored local run workspace

`runs/` holds cloud-teacher execution records, raw trajectory exports, compact verifier artifacts, local sanitizer outputs/reports, allowlisted distillation requests, GPT-5.6-sol drafts, external approval records, and local Qwen M0/M2 runs. Its contents are ignored by Git.

A file being stored locally does not mean its public teacher interaction was never transmitted. It does mean the raw local file is not authorized for upload to the distiller. Only a generated `cloud-distillation-request-v1` may cross that boundary.

Nothing here is measured merely because it exists. Teacher memory requires a qualified task, exactly one executable-verifier pass, sanitizer gates, exact distiller provenance, hash-scoped external approval, and admission. Student efficacy requires complete held-out Qwen M0/M2 executable-verifier pairs.

Never commit raw trajectories, private qualification details, local paths, credentials, canaries, scanner details, hidden tests, verifier internals, reference solutions, model files, or unrelated sessions.
