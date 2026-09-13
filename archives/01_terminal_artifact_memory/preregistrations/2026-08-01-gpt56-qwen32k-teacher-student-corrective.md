# Corrective GPT-5.6-sol teacher / local Qwen 32K transfer preregistration

**Status:** Corrective freeze awaiting merge; no measured execution authorized before this preregistration lands
**Freeze date:** 2026-08-01
**Corrective freeze revision:** `docker-compose-preflight-correction-v2`
**Protocol:** `teacher-student-transfer-v1`
**Split:** `gpt56-qwen32k-qualified-transfer-v1`
**Checkpoint:** M0 = zero pages; M2 = exactly three approved pages
**Machine-readable freeze:** [`manifests/preregistration-freeze-2026-08-01.v2.json`](../manifests/preregistration-freeze-2026-08-01.v2.json)

This document is the immutable corrective preregistration for the first real cloud-teacher/local-student Terminal Artifact Memory experiment. The landed corrective merge revision, not this feature-branch revision or an earlier merge, becomes the measured code pin. Any change to a task, role, model, adapter, prompt, context policy, task pin, qualification hash, ordering, checkpoint, threshold, denominator, or stop rule requires another preregistration and a fresh attempt budget.

## Pre-measurement corrective refreeze

A dry post-merge preflight found that the earlier runtime manifest encoded Docker client/server/API and Docker Compose in one `docker_version` value, while its landed executable gate compared that value only with `docker version`, which cannot report the Compose plugin version. The gate therefore failed before execution even though every installed component matched its public pin.

The captain approved a new preregistration rather than a post-hoc reinterpretation. This corrective freeze changes only runtime-pin representation and validation: `docker version` must exactly equal `client=24.0.4 server=28.3.2 api=1.51`, and `docker compose version --short` must independently equal `2.39.1-desktop.1`. Fresh student records use `teacher-student-paired-run-manifest-v3`; fresh teacher-build records use `teacher-memory-build-manifest-v2`; pre-correction schemas are rejected. The model, task split, prompts, context, ordering, attempt budget, denominators, stop rules, and every scientific control remain unchanged.

At corrective freeze, measured actor attempts = `0`, execution-ledger slots consumed = `0`, and no execution ledger has been initialized. Preflight files and the stopped local endpoint are development-only operational artifacts, not measured evidence. Measurement requires fresh private manifests and authorizations bound to the corrective freeze and its exact landed revision.

The 2026-07-31 16,384-token pilot remains unchanged and halted. Its invalid `build-pmars` attempt is not reused, repaired, relabeled, or pooled here.

## Frozen question and decision

**Question:** Do three qualified verifier-passing public terminal solutions from fixed cloud teacher `gpt-5.6-sol`, distilled by a separate fresh session of the same model into three approved Markdown pages, improve the exact local Qwen student's executable-verifier pass rate on three disjoint qualified structural probes at a fixed three-page checkpoint?

Only held-out local-Qwen executable-verifier M0/M2 pairs score transfer. A teacher verifier pass establishes page provenance only.

Continue the compact transfer design only if all three pairs are valid, at least one changes from M0 fail to M2 pass, pass-rate lift is at least `1/3`, retrieval covers the preregistered relevant page for all three M2 probes, and there are zero negative transfers and zero unsafe errors. Otherwise the result is no-go or inconclusive, never evidence manufactured from teacher outcomes, missing pairs, development controls, or denominator shrinkage.

This pilot cannot establish a population effect, a learning curve, production safety, or generalization beyond these qualified public tasks and exact controls.

## Evidence state at freeze

No measured teacher build, cloud distillation, Qwen M0, Qwen M2, memory admission, or efficacy analysis has run. The only pre-freeze executions and checks are development controls:

1. private verifier qualification controls;
2. local-Qwen context-policy development on three separate development tasks;
3. a non-measured host-Codex adapter smoke on `hello-world`; and
4. a non-measured credential/isolation negative control; and
5. the dry runtime preflight that exposed the impossible combined Docker/Compose version comparison before ledger initialization.

These controls are excluded from every measured denominator and can never enter memory. Three earlier model-endpoint DNS failures are retained privately as invalid development records. Synthetic tests and plans remain non-measured.

Measured authorization additionally requires:

1. this corrective preregistration PR to be merged;
2. a clean checkout at the exact landed revision;
3. a private task-specific authorization record tied to the freeze hash, actual model-visible instruction hash, immutable active-container digest, and qualification-record hash; and
4. every public and private pin to validate with no unresolved marker.

The host teacher adapter defaults to no authorization: it requires explicit `execution_mode=development` for the sole development task or a valid post-merge private authorization for a frozen memory-build task. Every measured teacher build, distillation, M0, and M2 manifest path invokes the shared landed gate: the clean checked-out revision must equal freshly fetched `origin/main` and `FETCH_HEAD`, and its first parent must not contain this freeze (binding the commit that landed the preregistration).

## Exact roles and execution identities

| Role | Exact identity | Fresh-session boundary | Receives | Never receives or decides |
| --- | --- | --- | --- | --- |
| Cloud teacher | `gpt-5.6-sol` through Codex CLI `0.146.0` | One host-side ephemeral Codex session per build task; no resume | One designated public build instruction, `teacher-v1`, and task-container observations/tool results | Held-out identities/content, qualification internals, hidden tests, reference solutions, host files, Qwen outcomes, or transfer score |
| Cloud distiller | `gpt-5.6-sol` through Codex CLI `0.146.0` | One separate ephemeral no-tools Codex session per generated request; no resume | Exactly one generated `cloud-distillation-request-v1` | Raw trajectory, verifier detail, scanner detail, canaries, held-out data, outside evidence, or admission authority |
| Local student | Exact Qwen GGUF pin below through llama.cpp | One fresh Terminus-2 attempt per condition | Public held-out task and either empty M0 marker or deterministic M2 retrieved block | Build trajectories, non-retrieved pages, teacher sessions, hidden verifier material, or cloud transmission |
| External reviewer | Recorded human identity external to teacher/distiller sessions | One hash-scoped review per draft | Public task, sanitized evidence, generated request, draft, citations, assumptions, hashes | Power to waive any failed gate |
| Executable verifier | Qualified pinned task bundle | One authoritative artifact per attempt | Task state after actor exits | Model confidence, narrative success, or learned-judge override |
| Operator/reviewer/implementation sessions | Explicitly non-measured | N/A | Development, orchestration, and review information allowed by role | Becoming a measured teacher/distiller or contributing an efficacy outcome |

### Teacher adapter boundary

The measured teacher adapter is exactly `host-codex-subscription-task-mcp-v1` in `artifact_memory.host_codex_harbor:HostCodexTeacherAgent`.

1. Codex CLI must report exactly `0.146.0`, login status must report the existing ChatGPT subscription, and the current catalog must contain exactly one `gpt-5.6-sol` entry.
2. Codex runs on the host with `--ephemeral`, so subscription OAuth remains in its existing host credential store. The adapter never copies, mounts, prints, hashes, archives, renames, or forwards an auth file or token.
3. The Codex working directory is `/`; user/project config and rules are ignored. Shell and unified-exec features are disabled. The host sandbox is read-only. Any host apply-patch/router attempt or non-task tool event invalidates the run before it can be admitted.
4. The sole approved model tool is `artifact_memory_task.task_shell`, served by a nonce-authenticated loopback-only bridge. Before cloud execution, the adapter verifies the running Harbor container's exact image ID against the digest-pinned configured image, rejects credential-like environment names, and requires exact Harbor trial-log bind sources. Model commands run only in a fresh zero-mount Docker snapshot sharing the task network, never in the verifier-visible container. The adapter stops that snapshot, stages only the complete `/app`, rejects devices/FIFOs/sockets and escaping links, durably persists exact-lifecycle ATIF plus matched private audit, then performs a rollback-capable `/app` swap as the final run operation. No snapshot change outside `/app` enters the verifier-visible container. Tool timeouts are clamped.
5. Raw credential-named environment values and Codex credential files are checked absent from the task container before any cloud request.
6. Model, CLI, login mode, explicit execution mode, task identity, post-merge authorization, clean code revision, private qualification record, and Docker isolation all fail closed before execution.
7. Credential-scanned Codex JSON events are converted to ATIF-v1.7 with exact model/adapter identity, task tool inputs, task observations, messages, and usage. Harbor independently runs and records the executable verifier afterward.

After independent-review hardening replaced command-text denial with the zero-mount snapshot boundary, a final fresh non-measured `hello-world` smoke on the pinned source produced exactly one qualified task-scoped tool call, an ATIF-v1.7 trajectory, no exception, and executable-verifier reward `1.0`. A separate final snapshot control made one qualified task-tool call that changed `/app` and attempted a forged verifier-log write; the protected write did not enter verifier output and the unsolved control scored `0.0`. Active-container preflight accepted only the closed log-mount and environment-name inventories, and a host-side synchronization control confirmed normal task state crossed while verifier state did not. No credential material pattern appeared. The source, trajectory, audit, control, and final independent-review hashes are frozen in `manifests/host-codex-adapter-qualification-attestation-2026-08-01.v1.json`. These controls never become experiment data.

Harbor's built-in Pi adapter is not used: its current implementation installs an unpinned upstream package and did not establish the required Codex subscription/trajectory boundary. Harbor's built-in Codex OAuth path is also not used because it copies `auth.json` into the task environment. No unsupported provider API is claimed.

### Distiller adapter boundary

The distiller adapter is `host-codex-subscription-no-tools-v1` in `artifact_memory.host_codex_distiller`: Codex CLI `0.146.0`, exact model selection `gpt-5.6-sol`, fresh ephemeral session, read-only host sandbox, no shell/unified-exec/MCP/browser/web tools, and no resume. It locally regenerates and byte-compares the allowlisted request before launch, sends that request as the sole user evidence packet over stdin, rejects every completed tool event, requires one unwrapped JSON draft, and revalidates all request/model/adapter/evidence hashes. Tool use, non-JSON event output, model mismatch, or any additional evidence invalidates the draft. Distillation is not exercised before this preregistration lands.

Teacher and distiller sessions are always separate. The operator captures session start/end, exact command policy, model, adapter, safe event stream, request/response hashes, and absence of resume. The implementation worker and independent design reviewer are never measured roles.

## Preregistered disjoint split

Selection used public Terminal Bench 2.0 instructions and public metadata only. Qualification internals and task solutions did not inform structural pairing. Every build, held-out, and context-development identity is disjoint.

| Order | Role | Public task | Structural family | Preregistered page / probe relationship |
| --- | --- | --- | --- | --- |
| 1 | Memory build | `openssl-selfsigned-cert` | server configuration | Produces `self-signed-server-certificate`; relevant to the separate Git/web-server probe's certificate, file-permission, configuration, and validation mechanics |
| 2 | Memory build | `sqlite-with-gcov` | source build | Produces `instrumented-native-source-build`; relevant to the separate dual-toolchain source-compilation probe |
| 3 | Memory build | `train-fasttext` | model execution | Produces `bounded-local-model-artifact`; relevant to the separate local model-artifact inference CLI probe |
| 1 | Held-out Qwen probe | `configure-git-webserver` | server configuration | Expected relevant page: `self-signed-server-certificate` |
| 2 | Held-out Qwen probe | `polyglot-rust-c` | source build | Expected relevant page: `instrumented-native-source-build` |
| 3 | Held-out Qwen probe | `pytorch-model-cli` | model execution | Expected relevant page: `bounded-local-model-artifact` |

Development-only context tasks are `hello-world`, `modernize-scientific-stack`, and `nginx-request-logging`. They cannot enter either measured split or memory.

Neither measured teacher nor distiller session receives held-out identities, instructions, files, trajectories, retrieval queries, outcomes, or verifier data. Each teacher process starts at `/`, ignores repository context, and receives only its one public build packet and isolated task tool. Qwen held-out sessions receive no teacher trajectory; M2 receives only deterministically retrieved approved Markdown.

## Private verifier qualification and public attestations

Terminal Bench source revision is `69671fbaac6d67a7ef0dfec016cc38a64ef7a77c`; registry snapshot SHA-256 is `da1446bce05eabbd72a25eb9eef5a2f5db94645ce88c28e2497581433b3d2e60`.

Every selected task completed the merged `verifier-qualification-v1` contract privately:

- two accepted known-good runs in clean containers with the same strict reward `1.0`;
- one rejected targeted negative for every public requirement class;
- one rejected reward/test tamper attempt with verifier isolation preserved; and
- exact instruction, task bundle, immutable container, verifier bundle, and compact qualification-record hashes.

| Task | Role | Public requirement classes | Known-good | Targeted negatives | Clean runs | Tamper | Eligible |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `openssl-selfsigned-cert` | Build | 6 | 2/2 accepted | 6/6 rejected | 2 consistent | 1 rejected | Yes |
| `sqlite-with-gcov` | Build | 4 | 2/2 accepted | 4/4 rejected | 2 consistent | 1 rejected | Yes |
| `train-fasttext` | Build | 3 | 2/2 accepted | 3/3 rejected | 2 consistent | 1 rejected | Yes |
| `configure-git-webserver` | Held-out | 4 | 2/2 accepted | 4/4 rejected | 2 consistent | 1 rejected | Yes |
| `polyglot-rust-c` | Held-out | 4 | 2/2 accepted | 4/4 rejected | 2 consistent | 1 rejected | Yes |
| `pytorch-model-cli` | Held-out | 5 | 2/2 accepted | 5/5 rejected | 2 consistent | 1 rejected | Yes |

Safe exact hashes are in [`verifier-qualification-attestations-2026-08-01.v1.json`](../manifests/verifier-qualification-attestations-2026-08-01.v1.json). Verifier code, hidden tests, known-good solutions, mutation details, commands, paths, canaries, and detailed output remain only in approved private storage. Qualification is development evidence about eligibility, not a measured result or shadow score. The executable verifier remains the sole authority for each later run.

Any later pin mismatch, false accept, false reject, nondeterminism, failed isolation, or uncovered requirement makes the task and protocol ineligible; no post-freeze replacement is allowed.

## Frozen local student and context policy

- Model: official Apache-2.0 `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`.
- Hugging Face revision: `13fb94bfda8c8cf22497dc57b78f391a9acb426a`.
- Quantization: Q4_K_M (`GGUF-Q4_K_M`).
- Model SHA-256: `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` (locally reverified before freeze).
- Runtime: Homebrew llama.cpp build `10200`, source revision `5f55650a7`.
- Hardware: Apple M2 Pro MacBook Pro, 16 GB; no machine identifier.
- OS: macOS 26.6 arm64; task containers use pinned linux/amd64 images under Docker Desktop.
- Context: exactly **32,768 tokens**.
- Turn cap: exactly **24**.
- Summarization: disabled.
- Decoding: temperature `0`, seed `42`; other options remain pinned Terminus-2/llama.cpp defaults.
- Tools: terminal and task-container filesystem only.
- Attempts: one per condition, zero retries, one concurrent trial, timeout multiplier `1.0`.
- Student prompt: `system-v1+memory-v1` with exact hashes in the machine-readable freeze.

### Development-only context decision

The valid host-local endpoint development runs all reached executable verification with 32K, no summarization, and a 24-turn cap:

| Development task | Reached verifier | Maximum observed context tokens |
| --- | --- | ---: |
| `hello-world` | Yes | 1,145 |
| `modernize-scientific-stack` | Yes | 13,765 |
| `nginx-request-logging` | Yes | 5,446 |

The maximum observed occupancy leaves `17,203` tokens after additionally reserving the frozen 1,800-token M2 retrieval budget. The 24-turn cap therefore supplies substantially more headroom than required without lossy summarization. Development rewards are irrelevant; reaching the verifier and context occupancy are the policy evidence. No held-out measured task was run to select or tune this policy.

## Frozen memory and retrieval controls

- Representation: approved distilled Markdown only.
- M0 checkpoint: zero pages and an empty retrieved-memory marker.
- M2 checkpoint: exactly three active pages from three distinct frozen build tasks.
- Retrieval: `direct-markdown-lexical-v1`.
- Retrieval config SHA-256: `46d2e64f1f52438014787abd86a802d829dee9eb73c3b2596f9ad5e9470dfffb`.
- Top K: 3.
- Lexical token budget: 1,800.
- Sanitizer: `artifact_memory-sanitizer-v1`, Gitleaks 8.30.1, one private post-execution non-solution canary per build, private blocked terms, printable-ASCII allowlist, and residual scan.
- Admission: exact verifier passage, qualification, provenance, generated request, `gpt-5.6-sol` draft, every local safety gate, and external human approval scoped to request/evidence/draft/page hashes.

M2 does not run unless all three exact pages are approved and admitted. The page index rejects edits, supersession, legacy records, duplicate build contributions, wrong split/role, or held-out-derived memory.

## Cloud transmission inventory

Local retention and cloud disclosure are separate facts.

### Teacher may receive

1. One preregistered public memory-build task identity and instruction.
2. The `teacher-v1` prompt and adapter task-tool boundary prompt.
3. Task-visible observations from that task's isolated public container.
4. Teacher-selected task-shell inputs and returned task output required to solve that task.

### Distiller may receive

Only the generated `cloud-distillation-request-v1`, including:

1. public build task identity, split revision, instruction, and instruction hash;
2. `distillation-v1` content/revision/hash;
3. sanitized evidence identifier, hash, media type, and text;
4. aggregate executable-verifier and sanitizer pass attestations;
5. safe teacher model/adapter/prompt and artifact hashes; and
6. the request's exact allow/deny inventory.

### Local student cloud disclosure

None. Held-out identities, prompts, retrieval, trajectories, tool calls, outcomes, and verifier records remain local and are not transmitted to teacher or distiller roles.

### Denied from cloud roles and commits

- raw host auth/token/API-key material or credential files;
- raw private trajectory uploads after execution;
- private paths, hosts, repositories, machine identifiers, or infrastructure details;
- hidden tests, verifier implementation/detail/output, reference solutions, or qualification internals;
- canary values/metadata, blocked-term lists, or detailed Gitleaks/scanner findings;
- held-out identities/content in teacher or distiller sessions;
- unrelated sessions, prompts, terminal content, or conversations; and
- model paths, private manifests, jobs, commands, or local storage paths.

The teacher's original public interaction crosses the cloud boundary and is captured locally. Retaining it locally does not authorize retransmitting it to the distiller.

## Exact ordering and one-attempt budget

1. Merge this corrective preregistration and pin the exact landed clean revision.
2. Resolve every private manifest marker; validate the freeze, tools, model bytes, task copies, container digests, verifier hashes, and private qualification records.
3. Start one pinned loopback llama.cpp endpoint and complete measured preflight.
4. Run all Qwen M0 attempts, in order: `configure-git-webserver`, `polyglot-rust-c`, `pytorch-model-cli`.
5. Only after all three valid M0 verifier artifacts exist, run one fresh teacher attempt each, in order: `openssl-selfsigned-cert`, `sqlite-with-gcov`, `train-fasttext`.
6. For each exact teacher verifier pass, sanitize locally and generate the sole allowlisted request.
7. Run one fresh no-tools distiller session per generated request in build order. No retries.
8. Obtain one external hash-scoped approval and admit each page in build order.
9. Require the exact three-page checkpoint and recompute every page/index hash.
10. Run all Qwen M2 attempts in the same held-out order.
11. Analyze all preregistered denominators and publish missing/invalid/ineligible accounting.

Budget maxima: three M0 attempts, three teacher attempts, three distiller attempts, and three M2 attempts. Each task or packet gets one attempt and zero retries. After merge, one mode-0600 private `terminal-artifact-memory-execution-ledger-v1` is initialized at the fixed private experiment root and its canonical-path identity is anchored once in the checkout's uncommitted Git-common metadata. Every measured actor reserves the next one of the 12 frozen phase/task slots under a separate exclusive lock immediately before its external execution and completes it only after authoritative local artifacts validate. Updates use a fully written and fsynced same-directory temporary file, atomic replacement, and directory fsync. A started, failed, or interrupted slot blocks every retry and later phase; measured combined-pair execution is disabled. No task replacement, alternate runs directory, rerun, repair, selective omission, or denominator substitution is allowed after freeze.

## Outcomes, thresholds, and denominators

Primary metric:

```text
(M2 executable-verifier passes / 3) - (M0 executable-verifier passes / 3)
```

Transfer classes retain their existing definitions: positive transfer, negative transfer, stable success, and unresolved task.

Success requires all of:

1. three valid complete Qwen pairs;
2. at least one positive transfer;
3. pass-rate lift of at least `1/3`;
4. zero negative transfers;
5. zero unsafe errors; and
6. retrieval coverage `3/3` for the preregistered page mappings.

Each of the six student condition records must also carry a hashed `student-unsafe-error-audit-v1` object proving zero Harbor exceptions, no credential-material match, and exactly one trajectory and executable-reward artifact. The result's `unsafe_error` is derived from that object, revalidated before ledger completion, and revalidated again during frozen analysis.

The negative-transfer threshold and unsafe-error threshold are both zero. A negative transfer does not permit stopping early or hiding later M2 outcomes; all valid preregistered M2 attempts still run so the denominator remains three. Safety/privacy/contamination failures do stop immediately.

Frozen denominators:

| Quantity | Denominator |
| --- | ---: |
| M0 pass rate | 3 held-out tasks |
| M2 pass rate | 3 held-out tasks |
| Transfer classification | 3 pairs |
| Retrieval coverage | 3 M2 probes |
| Student condition attempts | 6 |
| Unsafe-error audit | 6 student attempts |
| Teacher eligibility (descriptive only) | 3 build tasks |
| Verified knowledge yield | 3 admitted build contributions |

A missing, invalid, ineligible, or not-run record remains visible and never shrinks a denominator. It prevents a success claim rather than being silently scored as a verifier failure. Teacher passes never enter Qwen pass-rate or transfer numerators.

Required descriptive metrics are positive/negative/stable/unresolved counts, invalid/ineligible/not-run counts, retrieval coverage, verified knowledge yield, wiki bytes, latency, retrieval latency, prompt/output tokens, and unsafe-error accounting. With three observations, quantiles are not inferential; report each task and maximum rather than presenting unstable p95/p99 estimates as population evidence.

## Stop boundaries

Stop immediately and preserve accounting if any of the following occurs:

1. this corrective PR is not merged or the checkout is not the exact clean landed revision;
2. a model, prompt, adapter, task, container, verifier, qualification, code, lock, tool, context, retrieval, sanitizer, or checkpoint pin is missing or mismatched;
3. a task becomes ineligible, nondeterministic, contaminated, or replaced;
4. a one-attempt M0 condition is invalid or lacks exactly one executable-verifier artifact;
5. a teacher session is not fresh/ephemeral/task-scoped, model/adapter/ATIF provenance differs, or exact reward `1.0` is absent;
6. any sanitizer, Gitleaks, canary, blocked-term, printable-ASCII, residual, or disclosure gate fails;
7. a distillation session is not fresh and tool-free, or its input differs from the generated packet;
8. approval is missing or does not cover every exact request/evidence/draft/page hash;
9. admitted memory is not exactly the frozen three-page checkpoint;
10. an M2 control or memory provenance differs outside the rendered retrieved-memory block;
11. privacy, credential exposure, hidden-test access, split contamination, provenance, or unsafe-error boundaries are crossed; or
12. a one-attempt actor/runtime failure would require rerun, repair, or replacement.

A task-level verifier reward below `1.0` is an observed run outcome. Qualification failure, missing transport, or protocol mismatch is ineligible/invalid. These categories are never conflated.

## Tool and source pins

- Harbor `0.20.0`; distribution `RECORD` SHA-256 `d6d7a0b6b6b1c4a34f85f09ba99fea1cc1a39beddf11147d150ac076f7e62225`.
- Host Codex CLI `0.146.0`; exact catalog slug `gpt-5.6-sol`, context window 272,000 at freeze.
- Docker client `24.0.4`, server `28.3.2`, and API `1.51` are validated together through exact `docker version` output; Compose `2.39.1-desktop.1` is validated separately through exact `docker compose version --short` output.
- Public pulls use a task-private credential-free Docker config with the trusted Docker Desktop Compose plugin directory; global Docker credentials are untouched.
- Terminal Bench `2.0`, source revision and registry hash above.
- ATIF `ATIF-v1.7`.
- Gitleaks `8.30.1`.
- uv `0.10.4`; `uv.lock` SHA-256 `c3366e15a5706a4e497eebe344a9be45e7947ae8ababe8408dae239d2888f8ac`.
- llama.cpp and model pins as specified above.

Exact per-task instruction, task-bundle, container, verifier-bundle, and compact qualification hashes are in the safe attestation manifest. Runtime manifests additionally bind the exact landed Git revision and private record paths/hashes.

## Analysis and interpretation boundary

The executable verifier alone establishes each individual outcome. Model prose, tool exits, artifact appearance, teacher confidence, distillation quality, human preference, learned judges, and development controls cannot override it.

A positive result would support continuing this compact design only for the frozen qualified workload and controls. A negative result would support simpler retrieval or direct cloud inference. A mixed or incomplete result should identify whether the limit was retrieval, page quality, local capability, context, verifier eligibility, or protocol execution; it cannot support a broad efficacy claim.
