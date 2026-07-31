# Teacher/student transfer operator guide

This guide prepares the **next planned** Terminal Artifact Memory experiment. It does not authorize a measured run without a new preregistration and complete local pins. No teacher/student measured result exists.

The [2026-07-31 halted 16K pilot](results/2026-07-31-measured-pilot/summary.md) is immutable. Never rerun, relabel, repair, or pool its consumed attempt.

## Non-negotiable authority

> **Do not claim success; the executable verifier alone determines whether the run is eligible for local sanitization and later distillation.**

Ignore model confidence, completion prose, command exit impressions, apparent files, distillation quality, and learned judges when deciding eligibility. If exactly one pinned task verifier artifact with exact reward `1.0` is not present, the build is ineligible. It is not a candidate for sanitization, distillation, approval, or memory.

## Upstream responsibility

Harbor/Terminal Bench supplies the task environment and task-specific executable-verifier semantics. This repository validates pins, result transport, hashes, eligibility, and admission links; it does not recreate or reveal verifier internals.

Use authoritative upstream documentation for Harbor installation, Docker-backed tasks, Terminus-2, ATIF, skills, llama.cpp server, and Gitleaks. Pin the chosen versions in the new preregistration. Do not assume that `gpt-5.6-sol` is available through an API. Select an operator-supplied or Harbor-compatible execution boundary only when current authoritative tooling establishes it, and record that adapter exactly.

## 1. Development checks

Run from this experiment directory:

```bash
uv sync --frozen
uv run python -m unittest discover -v
uv run python -m artifact_memory.sanitize --self-test
uv lock --check
```

Synthetic fixtures are deterministic controls, not experiment data.

## 2. Preregister roles, split, context, and thresholds

Before any measured action, publish a new protocol revision that freezes:

1. exact disjoint public memory-build and held-out task lists;
2. public task instructions and immutable task/container/verifier bundle pins;
3. teacher and distiller identity `gpt-5.6-sol`, operator adapters, and prompt hashes;
4. exact local Qwen identity/revision/Q4_K_M/hash and pinned llama.cpp;
5. a context policy demonstrated in development to reach executable verification;
6. hardware, decoding, tools, attempt/turn budgets, retrieval controls, and memory checkpoints;
7. success, negative-transfer, unsafe-error, and stop thresholds; and
8. the role-specific cloud transmission inventory.

Do not reuse the halted 16,384-token setting by implication. Choose and document the next context control explicitly.

Copy these templates only into ignored `config/local/` or `runs/` paths:

```text
manifests/measured-run-template.v2.json
manifests/teacher-memory-build-template.v1.json
manifests/verifier-qualification-template.v1.json
manifests/distillation-draft-template.v1.json
manifests/external-human-approval-template.v1.json
manifests/memory-admission-template.v2.json
```

`paired-run-manifest-v1` receives a controlled rejection for new measurement.

## 3. Qualify each task verifier privately

Qualification is required for every memory-build and held-out task before it is eligible for a measured split. Run qualification in clean containers as development-only work. Keep all jobs, verifier code, hidden tests, known-good artifacts, mutations, paths, commands, and detailed outputs private.

The compact qualification record must bind:

- task ID and Terminal Bench source revision;
- public instruction SHA-256;
- immutable task container digest; and
- verifier bundle SHA-256.

It records only public requirement-class identifiers and counts/outcomes for:

1. at least one accepted known-good positive control;
2. at least one rejected plausible-negative/mutation control for every public requirement class;
3. at least two consistent clean-container runs with the same strict pass reward; and
4. at least one rejected reward/test tamper attempt with isolation established.

Validate through the build or student preflight. Any missing pin, hash mismatch, uncovered requirement, false accept, false reject, nondeterminism, or failed isolation makes the task ineligible. Do not score it.

Qualification checks adequacy, while exactly-one reward transport and artifact hashes check integrity. Mutation controls raise confidence but cannot prove perfect coverage of task intent. Qualification remains development-only and never enters M0/M2 analysis or searchable memory.

## 4. Prepare local student controls

Copy `measured-run-template.v2.json` to `config/local/student-pair.json` and replace every uppercase marker. The manifest must keep:

- task role `held_out_student_evaluation` and actor `local_student`;
- exact `gpt-5.6-sol` teacher/distiller provenance roles, even though they do not execute the probe;
- exact Qwen student identity and sole-evaluation flag;
- a disjoint split revision;
- private qualification-record path and hash; and
- the exact transmission allow/deny inventory.

Set only the environment variables named by the local manifest:

- `ARTIFACT_MEMORY_MODEL_PATH`
- `ARTIFACT_MEMORY_LLAMA_API_BASE`
- `ARTIFACT_MEMORY_LLAMA_API_KEY`
- `ARTIFACT_MEMORY_PINNED_TASKS_PATH`

Credentials and model paths stay in environment values. Never put them in argv, manifests, logs, fixtures, or examples.

Validate and plan without execution:

```bash
uv run python -m artifact_memory.experiment validate \
  --manifest config/local/student-pair.json
uv run python -m artifact_memory.experiment plan \
  --manifest config/local/student-pair.json \
  --wiki-dir PRIVATE_MEMORY_WIKI \
  --memory-index PRIVATE_MEMORY_INDEX
```

`plan` is never a measured result.

## 5. Start and check the local Qwen endpoint

Print the pinned llama.cpp command:

```bash
uv run python -m artifact_memory.experiment llama-command \
  --manifest config/local/student-pair.json
```

Inspect it and start the server separately. The experiment does not manage model lifecycle. Then run:

```bash
uv run python -m artifact_memory.experiment check-prereqs \
  --manifest config/local/student-pair.json
```

Measured preflight checks the clean Git revision, external versions, exact Qwen file hash, student prompt hashes, public task instruction/container pins, and the private verifier qualification record.

## 6. Run all held-out Qwen M0 probes first

Before any memory page exists:

```bash
uv run python -m artifact_memory.experiment run-condition \
  --condition M0 \
  --manifest config/local/student-pair.json \
  --wiki-dir PRIVATE_MEMORY_WIKI \
  --memory-index PRIVATE_MEMORY_INDEX \
  --runs-dir PRIVATE_RUNS
```

M0 contains an empty retrieved-memory marker. Run every preregistered M0 probe before teacher memory construction. Do not let a held-out trajectory become memory.

## 7. Execute one cloud-teacher memory build

Use the selected authoritative operator boundary to send only:

1. the designated public memory-build task identity/instruction;
2. `prompts/teacher.v1.md`; and
3. task-environment observations plus teacher-selected tool inputs/outputs required for that public task.

The exact execution model must be `gpt-5.6-sol`. The coding worker that prepared this repository is not automatically the measured teacher.

Keep provider credentials environment-only. Do not place a key in an argument, manifest, shell history example, captured command, or log. Record the adapter name, timestamps, public task, model/prompt hashes, and local trajectory/verifier artifact hashes in a private copy of `teacher-memory-build-template.v1.json`.

The cloud teacher must not receive held-out probes, qualification internals, hidden tests, verifier code, reference solutions, local host details, or canaries.

## 8. Establish executable-verifier eligibility

Capture the operator's task result into the compact verifier artifact expected by the build manifest. It must attest:

```json
{
  "authoritative": "terminal-bench-executable",
  "passed": true,
  "reward": 1.0,
  "reward_artifact_count": 1,
  "source_sha256": "<sha256-of-the-single-pinned-reward-artifact>"
}
```

This compact example contains no verifier internals. If there are zero or multiple reward artifacts, a non-`1.0` reward, a hash mismatch, or an unqualified task, stop. Never infer pass from the teacher's response.

## 9. Sanitize locally before distillation

Keep the original raw capture locally. Create the local evidence export, append a preregistered non-solution canary locally **after** cloud teacher execution, and record that export as the build trajectory artifact. The canary must never be transmitted to the teacher.

```bash
uv run python -m artifact_memory.sanitize \
  --input runs/BUILD_ID/trajectory-export.txt \
  --output runs/BUILD_ID/sanitized.txt \
  --report runs/BUILD_ID/sanitizer.json \
  --artifact-id BUILD_ID \
  --canary-file config/local/canaries.txt \
  --blocked-terms-file config/local/private-terms.txt
```

The sanitizer runs Gitleaks on input and output, removes detailed temporary scanner reports, detects/removes every canary, redacts configured privacy classes, rejects credentials and contamination even after removal, enforces printable ASCII, and runs a residual scan. Do not weaken these gates to admit an artifact.

Validate the teacher build only after the executable verifier and sanitizer pass:

```bash
uv run python -m artifact_memory.transfer validate-build \
  --manifest runs/BUILD_ID/teacher-build.json
```

## 10. Generate the sole uploadable distillation packet

```bash
uv run python -m artifact_memory.transfer prepare-distillation \
  --manifest runs/BUILD_ID/teacher-build.json \
  --output runs/BUILD_ID/distillation-request.json
```

Inspect the generated request. It is the entire cloud-distiller upload. It contains public task fields, the distillation prompt, sanitized evidence text and hashes, aggregate verifier/sanitizer pass attestations, safe teacher provenance, and its own exact inventory.

Do **not** add raw trajectories, verifier detail, scanner reports, findings, blocked terms, canaries, private paths, credentials, or unrelated context. “Stored locally” never means that earlier public teacher interactions were not transmitted, and it never grants permission to retransmit local raw files.

Send this packet to `gpt-5.6-sol` through the selected operator adapter. Capture the response locally using `distillation-draft-template.v1.json`; do not invent a provider API.

Validate the response:

```bash
uv run python -m artifact_memory.transfer validate-draft \
  --manifest runs/BUILD_ID/teacher-build.json \
  --request runs/BUILD_ID/distillation-request.json \
  --draft runs/BUILD_ID/distillation-draft.json
```

The validator requires exact distiller identity, adapter, prompt hash, request hash, source evidence hashes, sanitizer revision, safe evidence IDs, and structured Markdown.

## 11. Obtain external hash-scoped approval and admit

A human external to the teacher/distiller execution must inspect the public task, sanitized evidence, draft, citations, assumptions, and limitations. Copy `external-human-approval-template.v1.json` locally. Set `approved: true` only after recording exact hashes for:

- distillation request;
- sanitized evidence and source evidence list;
- distillation draft; and
- intended page/build/task identifiers.

Then create a local `memory-admission-template.v2.json` request and run:

```bash
uv run python -m artifact_memory.memory admit \
  --request runs/BUILD_ID/memory-admission.json \
  --wiki-dir PRIVATE_MEMORY_WIKI \
  --index PRIVATE_MEMORY_INDEX
```

Admission independently revalidates the qualified teacher build, exact distiller provenance, generated request, structured evidence citations, sanitizer gates, and approval scopes. Only then does it add deterministic provenance and write the page/index hashes. Approval cannot waive any earlier failure.

Repeat only for preregistered memory-build tasks. Stop if the approved page count does not equal the checkpoint.

## 12. Run held-out Qwen M2

```bash
uv run python -m artifact_memory.experiment run-condition \
  --condition M2 \
  --manifest config/local/student-pair.json \
  --wiki-dir PRIVATE_MEMORY_WIKI \
  --memory-index PRIVATE_MEMORY_INDEX \
  --runs-dir PRIVATE_RUNS
```

Before M2, the runner recomputes page hashes and rejects unadmitted, edited, superseded, legacy, duplicate-build, wrong-split, wrong-role, or held-out-derived pages. The local Qwen model is the sole evaluation actor. The generated retrieved-memory block is the only student-context difference from M0.

The cloud teacher and distiller do not receive the held-out task, Qwen trajectory, retrieval result, or verifier output.

## 13. Analyze student pairs only

```bash
uv run python -m artifact_memory.analyze \
  --runs-dir PRIVATE_RUNS \
  --output-dir results/generated
```

The analyzer accepts only exact-student `student-paired-result-v2` records and executable-verifier booleans. It rejects cloud-teacher/distiller scores and non-student actors. A teacher task pass is page provenance; it is never an M0/M2 efficacy outcome.

Review compact outputs and run the repository safety scan before intentionally committing any result. Never commit raw jobs, trajectories, qualification internals, manifests with local paths, credentials, scanner details, canaries, model weights, or fabricated measurements.
