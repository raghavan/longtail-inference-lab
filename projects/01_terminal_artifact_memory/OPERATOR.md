# Pilot operator guide

The pilot software is runnable. No measured baseline exists yet. Harbor, Terminal Bench tasks, the model, and their exact revisions still have to be selected and pinned locally before a measured run.

## Upstream interfaces used

The implementation delegates rather than recreates the external platforms:

- [Harbor getting started](https://www.harborframework.com/docs/getting-started) documents `uv tool install harbor`, `harbor run`, registered datasets, and local datasets.
- [Harbor evals](https://www.harborframework.com/docs/run-jobs/run-evals) documents Docker-backed jobs and the trial `agent/trajectory.json` and `verifier/reward.txt` artifacts.
- [Terminus-2](https://www.harborframework.com/docs/agents/terminus-2) documents `--agent terminus-2`, `api_base`, temperature, and turn controls.
- [Harbor skills](https://www.harborframework.com/docs/run-jobs/skills) documents local `SKILL.md` injection and content digests. The pilot uses the same skill mechanism in M0 and M2; only the retrieved-memory section differs.
- [ATIF RFC 0001](https://github.com/harbor-framework/harbor/blob/main/rfcs/0001-trajectory-format.md) defines the trajectory format Harbor preserves.
- [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) documents `llama-server`, its OpenAI-compatible routes, and the model, context, host, and port flags used here.
- [Gitleaks usage](https://github.com/gitleaks/gitleaks#usage) documents the current `gitleaks dir` file/directory scan. The older `detect` command is deprecated.

The command builders are isolated and covered by tests. `check-prereqs` also inspects the installed `harbor run --help` before a trial.

## Local prerequisites

Already present at pilot implementation intake: Docker and uv.

Not present at intake: Harbor, Gitleaks, and `llama-server`. Do not install them globally from an automated run. An operator should:

1. Install a chosen stable Harbor release with the upstream `uv tool install harbor` method, then record `harbor --version`.
2. Install a pinned llama.cpp build by following its official build/install documentation, then record `llama-server --version` and the exact source revision.
3. Install Gitleaks using an upstream-supported method (the project documents Homebrew and release binaries), then record `gitleaks version`.
4. Confirm the Docker daemon is available with `docker info`.
5. Select license-compatible Qwen-family 7B GGUF Q4 weights. Keep the file under the ignored local model storage, compute its SHA-256, and do not commit it.
6. Select and preregister the public environment-setup memory-build tasks and separate held-out probes. Pin the Harbor/Terminal Bench version and task container digest.

Do not use hidden tests, reference solutions, or verifier details as model or retrieval input.

## Development checks

Run from this experiment directory:

```bash
uv sync --frozen
uv run python -m unittest discover -v
uv run python -m lily.sanitize --self-test
uv lock --check
```

The self-test and end-to-end unittest smoke use synthetic fixtures and are not measured experiment data.

## Prepare a local manifest

Copy `manifests/measured-run-template.v1.json` to a local, uncommitted path under `config/local/`. Fill every `REQUIRED_...` value explicitly. The loader never infers measured provenance. It rejects an incomplete measured manifest.

Unresolved values are detected by the uppercase template convention only: `REQUIRED_...`, `TBD...`, `CHANGEME`, and `PLACEHOLDER`. Ordinary prose such as a task description containing "required" is accepted, so never leave a real value in that uppercase marker form.

Set the three environment variables named by the manifest:

- `LILY_MODEL_PATH`: local GGUF path.
- `LILY_LLAMA_API_BASE`: loopback OpenAI-compatible `/v1` endpoint.
- `LILY_LLAMA_API_KEY`: local endpoint credential or a non-secret local sentinel when the endpoint requires none.

Values are read at runtime and are not copied into the fixed-control manifest.

Validate without executing:

```bash
uv run python -m lily.experiment validate --manifest config/local/pilot.json
uv run python -m lily.experiment plan \
  --manifest config/local/pilot.json \
  --wiki-dir memory/wiki \
  --memory-index memory/manifests/artifact_index.jsonl
```

`plan` is planning output, never a measured result. Both `plan` and `run` recompute the memory state from the admitted-page index: every wiki page must be an admitted, unsuperseded page whose content still hashes to its admission record. `memory_contributions` and `memory_checkpoint` are both the verified contributions available, so each must equal that observed page count exactly; checkpoints are numbered by contribution count, not by run order.

## Start the local model endpoint

Print the source-backed llama.cpp command:

```bash
uv run python -m lily.experiment llama-command --manifest config/local/pilot.json
```

Inspect and execute that command in a separate terminal. The pilot does not manage the server lifecycle. Then check all pinned boundaries:

```bash
uv run python -m lily.experiment check-prereqs --manifest config/local/pilot.json
```

This checks tool availability and pins, Docker, Harbor's required flags, the loopback `/health` and `/v1/models` routes, a clean worktree at the declared Git revision, prompt and lock hashes, and the GGUF hash.

## Run a paired probe

```bash
uv run python -m lily.experiment run \
  --manifest config/local/pilot.json \
  --wiki-dir memory/wiki \
  --memory-index memory/manifests/artifact_index.jsonl \
  --runs-dir runs
```

Harbor owns Docker isolation, Terminus-2, ATIF capture, and the executable verifier. Each condition receives the same versioned skill template. M0 gets an empty memory marker; M2 gets deterministic retrieved pages. The runner records the fixed-control digest and rejects an overwrite.

Raw run directories are local and ignored because trajectories can contain sensitive data. A result is measured only when its input manifest says `measured`, contains complete provenance, and passes the checks above.

## Sanitize and admit one verified memory contribution

A memory-build artifact must contain at least one preregistered canary planted in task-visible, non-solution metadata before export. Put expected canary values and any known private host/repository terms in local files that are never committed.

```bash
uv run python -m lily.sanitize \
  --input runs/LOCAL_BUILD/trajectory.json \
  --output runs/LOCAL_BUILD/sanitized.txt \
  --report runs/LOCAL_BUILD/sanitizer.json \
  --artifact-id SAFE_ARTIFACT_ID \
  --canary-file config/local/canaries.txt \
  --blocked-terms-file config/local/private-terms.txt
```

The sanitizer runs Gitleaks on both the exported source and sanitized output, then deletes detailed local scan reports after recording value-free counts. It redacts private paths, workspace/mount paths, hosts, network addresses, remotes, configured private terms, and canaries. Credentials, hidden-test paths, reference solutions, verifier details, and contamination signals block admission even after removal. No unresolved Gitleaks finding, a printable-ASCII allowlist, a clean residual scan, and detection/removal of every canary are mandatory.

Copy `manifests/memory-admission-template.v1.json` to `config/local/`, fill its hashes and manually distilled summary, inspect the sanitized artifact, and record explicit review approval scoped to the sanitized artifact hash. Then run:

```bash
uv run python -m lily.memory admit \
  --request config/local/memory-admission.json \
  --wiki-dir memory/wiki \
  --index memory/manifests/artifact_index.jsonl
```

Admission requires the executable verifier pass, complete provenance, every sanitizer gate, and human approval. Resolution claims must cite safe evidence identifiers.

## Generate paired summaries

```bash
uv run python -m lily.analyze --runs-dir runs --output-dir results/generated
```

By default analysis refuses development and fixture data. `--include-non-measured` exists only for explicit smoke work and labels every output non-measured. The CSV and Markdown report verifier pass rates, transfer classes, unresolved tasks, retrieval coverage, and verified knowledge yield. Learned-judge fields are ignored.

Analysis reads only the records this runner writes, at `runs/<pair_id>/M0/result.json` and `runs/<pair_id>/M2/result.json`; Harbor's own job tree is never scanned. Within that layout the denominator never shrinks silently: an unreadable record stops the analysis, and any record that is not `paired-result-v1` is counted and listed in the summary's data-completeness section.

Review every compact measured output and run the repository safety scan before intentionally committing it.
