# Local run workspace

The paired runner creates `runs/<pair-id>/{M0,M2}/` on demand. Raw Harbor jobs, ATIF trajectories, verifier files, generated skills, manifests, retrieval records, and compact condition results remain local and are ignored by Git.

Nothing in this directory is a measured result merely because it exists. A measured run requires a complete measured manifest and all prerequisite checks. Generate reviewed compact summaries under `results/generated/`.
