# Measured pilot preregistration

**Frozen:** 2026-07-31, before the oracle/development check, M0 probes, or memory-build runs  
**Experiment:** Terminal Artifact Memory  
**Checkpoint:** three admitted pages (M0 baseline: zero pages; M2: three pages)  
**Family:** `environment_setup` — dependency-aware environment provisioning

## Question and analysis boundary

This pilot asks whether three verifier-passing, sanitized, human-approved pages improve the same fixed local model on three separate Terminal Bench 2.0 tasks that recur at the level of setup mechanism rather than task identity.

The primary outcome is the executable-verifier M2 pass rate minus the M0 pass rate across all three structural probes. Every pair is classified as positive transfer, negative transfer, stable success, or unresolved. Retrieval coverage, verified knowledge yield, latency, and wiki bytes are descriptive secondary outcomes.

With only three probes, this pilot cannot establish a population effect or a learning curve. A favorable pilot requires at least one positive transfer, no negative transfer, all six measured condition records to be valid, and no safety or contamination breach. Any other complete result is negative or inconclusive rather than evidence of benefit. If fewer than three pages pass every build, sanitizer, and review gate, checkpoint 3 is not run and no M0/M2 claim is made.

## Preregistered split

All six tasks are distinct public tasks. A probe can never contribute to memory used for its own evaluation.

| Role | Public Terminal Bench 2.0 task | Structural mechanism | Preregistered relevant page for each probe |
| --- | --- | --- | --- |
| Memory build | `sqlite-with-gcov` | Unpack a supplied source snapshot, install/build the native toolchain, compile with instrumentation, and expose the executable on `PATH` | `sqlite-source-build-gcov` |
| Memory build | `modernize-scientific-stack` | Reconcile a legacy Python program with current Python and explicitly declare compatible scientific dependencies | `modern-python-scientific-stack` |
| Memory build | `pypi-server` | Build a Python distribution, provision a localhost package service, and validate installation through its client interface | `local-python-package-service` |
| Structural probe | `build-pmars` | Obtain Debian source, perform a constrained native build without X11, install to a required path, and smoke-test the executable | `sqlite-source-build-gcov` |
| Structural probe | `build-cython-ext` | Repair source and native extensions for a current Python/NumPy environment, build, install, and exercise imports | `modern-python-scientific-stack` |
| Structural probe | `nginx-request-logging` | Install and configure a persistent localhost service, validate configuration, start it, and test through an HTTP client | `local-python-package-service` |

The mapping was chosen from the public instructions and task metadata only. It is intentionally structural: source project, required flags, dependency details, service, and target artifact differ between each build task and its probe. No exact task repeats are included.

A separate `hello-world@1.0` task is used only to check the oracle and Terminus-2 execution paths. It is development data, is excluded from every result, and can never enter memory.

## Immutable external pins

- Harbor: `0.20.0`; installed distribution `RECORD` SHA-256 `d6d7a0b6b6b1c4a34f85f09ba99fea1cc1a39beddf11147d150ac076f7e62225`.
- Harbor interface: `harbor run --include-task-name`, local `--path`, `--skill`, and `--extra-instruction-path` as exposed by Harbor 0.20.0 help.
- Terminal Bench dataset: `terminal-bench@2.0` from the Harbor legacy registry snapshot with SHA-256 `da1446bce05eabbd72a25eb9eef5a2f5db94645ce88c28e2497581433b3d2e60`.
- Terminal Bench task source revision: `69671fbaac6d67a7ef0dfec016cc38a64ef7a77c`.
- Terminus-2: Harbor 0.20.0 built-in agent; ATIF schema `ATIF-v1.7`.
- Docker: daemon `28.3.2`, client `24.0.4`, one trial at a time. Public pulls use a task-private credential-free Docker configuration because the desktop credential helper is nonresponsive; global Docker authentication is not changed.

| Task | Public instruction SHA-256 | Immutable container digest |
| --- | --- | --- |
| `sqlite-with-gcov` | `b6ba9acf62292bc2a0bab40d4805b3abceededbb0ccd4477a1ce9ccc42c14dd9` | `sha256:f986820b00c74ce75db7288719d364df313fde7c7917bea6eb6352a08431a89f` |
| `modernize-scientific-stack` | `666b8ac370ae81b0e3780a36e722c91b0f986fccbdc6ed36ab3bd17e6943da0f` | `sha256:64e69cee13bf6b0b9016e735b51891bce996a60f1e2d1a005bf12c949e221d71` |
| `pypi-server` | `1c537e4a311a8e71155e121f57bfc03f742fbfb99d05314cd03e433996a28a31` | `sha256:d18bb30f47c7dcaa3acdbc31ac7413c98eadca2ea16540bbd380f2f063b95276` |
| `build-pmars` | `1606850579342a8b8f2189de0e499fae6be21198150d8dd1e4d18c2efbcf3b82` | `sha256:57a82706f7491e0b2d1ff7e927e97ae5339892dd09c47ac43290b4ba1f5abc6f` |
| `build-cython-ext` | `7e52874e45f88505bd21540229719de6639a401477557d814489981d472f0e34` | `sha256:3612a38fadb89a96f74a1a951fb0b0af734198fd160571eeaba6401593234594` |
| `nginx-request-logging` | `26a7ac98aced6107f147206790ada77bbf8ed3c25fb360cf323d5fc6889edf99` | `sha256:693e64431a0dbf45952e8b91a298d54fd60247e501c6623fb8fa3ebc07fc3d3d` |

The private runtime copies replace image tags with these repository digests. The measured preflight checks both the instruction hash and digest reference. The run-time manifests bind all conditions to the same full clean Git revision created after this preregistration and runner update.

## Fixed model and runtime controls

- Model: official Apache-2.0 `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`, Hugging Face revision `13fb94bfda8c8cf22497dc57b78f391a9acb426a`, Q4_K_M file, SHA-256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`.
- Runtime: Homebrew llama.cpp build `10200`, source revision `5f55650a7`; one task-owned loopback `llama-server` for the full pilot.
- Hardware class: M2 Pro MacBook Pro, 16 GB memory. No machine identifier is recorded.
- Host OS class: macOS 26.6 arm64. Terminal Bench containers are the pinned linux/amd64 images under Docker Desktop emulation.
- Model context: 16,384 tokens.
- Prompt: `system-v1+memory-v1`; system SHA-256 `7c21baeb6445e013972bdd6bbb941d2b367cb6b5d2e9a9b0e4c8bbef1bb5b015`; memory SHA-256 `a274f71dc6aae550995c6ce801fc15d9420bce50e82ccd66ead93631697abd6d`.
- Decoding: temperature `0`, random seed `42`; other sampling options are omitted and therefore use the pinned Terminus-2/llama.cpp defaults.
- Harbor model name: `openai/fixed-qwen-7b-q4`.
- Tools: terminal and task-container filesystem only. No host filesystem or unrestricted external-network permission is added by the experiment.
- Budget: 40 turns, timeout multiplier `1.0`, one attempt, one concurrent task, Harbor default zero retries, summarization disabled.
- Local endpoint credential: a non-secret sentinel passed only through process environment, never argv or a manifest.

## Fixed memory controls

- Representation: M2 distilled Markdown pages only.
- Retriever: `direct-markdown-lexical-v1`.
- Top K: 3.
- Retrieval budget: 1,800 retriever lexical tokens.
- Search fields and scoring rule: `config/retrieval.v1.json` at the frozen run revision.
- Sanitizer: `artifact_memory-sanitizer-v1` with Gitleaks 8.30.1, a private non-solution canary for every build trajectory, blocked-term redaction, printable-ASCII allowlist, and residual scan.
- Admission: executable verifier pass, complete provenance, all automated gates, manual inspection, and explicit external human approval scoped to each sanitized artifact hash.

M0 and M2 use the same task, task image, model server, model, prompts, runtime, hardware, decoding, tools, budget, and run revision. M0 is run before memory construction with zero admitted pages. M2 is run only after three approved pages are admitted. The rendered retrieved-memory block is the only model-context difference.

## Ordering and contamination controls

1. Commit this preregistration and the runner compatibility update; freeze its full Git revision.
2. Start and verify one bounded loopback model server.
3. Run the development-only oracle/Terminus check.
4. Run all three M0 probes before any build task or memory page exists.
5. Run each memory-build task once with the same local model and empty memory.
6. Sanitize only verifier-passing trajectories. Do not inspect or export hidden tests, verifier implementation, or reference solutions into model/retrieval context.
7. Stop for external human review before admission.
8. Admit exactly the approved pages. If the admitted count is not three, stop without M2.
9. Run the same three probes once under M2 and analyze every preregistered pair.

Raw Harbor jobs, trajectories, model paths, local configuration, canary values, and detailed scanner output remain private and uncommitted. Only reviewed pages, compact verifier-authoritative results, safe hashes/provenance, and the interpretation may be published.
