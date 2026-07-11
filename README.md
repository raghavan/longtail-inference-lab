<p align="center">
  <img src="resources/assets/longtail-inference-lab-hero.png" alt="Long Tail Inference Lab system diagram" width="100%">
</p>

# Long Tail Inference Lab

A research lab for discovering where everyday devices, local models, durable memory, and portable session state can absorb the long tail of inference work.

## Thesis

Frontier models are valuable, but not every request needs frontier compute. A large portion of useful inference may be handled by smaller models, cached knowledge, existing session context, and the machines people already own.

This lab studies the boundary between those paths. Each experiment starts with a measurable question, records what happened, and publishes useful negative results as carefully as positive ones.

## Current experiments

### [01 Memory Wiki](projects/01_memory_wiki/README.md)

**Status:** Specified

**Question:** Can a human readable knowledge cache help a local model answer more recurring questions while preserving quality and reducing frontier model usage?

### [02 Session Capsule Analysis](projects/02_session_capsule_analysis/README.md)

**Status:** Specified

**Question:** What does a real coding agent session contain, how does it grow, and when might replay, compression, or portable state become worthwhile?

## PARA organization

```text
projects/
  01_memory_wiki/
  02_session_capsule_analysis/

areas/
  lab_operations/
  public_website/

resources/
  assets/
  experiment_template/
  learning/
  project_proposals/

archives/
```

### Projects

Projects are active experiments with a bounded research question and a clear completion condition. This folder intentionally contains only work receiving active attention.

### Areas

Areas are ongoing responsibilities that keep the lab trustworthy, including reproducibility, safety, experiment discipline, result quality, repository maintenance, and public communication.

The [public website](areas/public_website/README.md) is an Area because it remains active as the laboratory evolves rather than ending with a single experiment.

### Resources

Resources are reusable learning material, references, concepts, proposals, templates, and media. They support many experiments but do not have a completion date.

### Archives

Archives hold completed, paused, or superseded experiments. A negative result belongs here once the experiment is complete because it still narrows the search space.

GitHub requires workflow configuration to remain under `.github/`. That folder is repository plumbing rather than research content, and it includes its own README.

## Experiment lifecycle

```text
Idea → Specified → Running → Analyzing → Complete → Archive
```

An experiment is complete only when its results, interpretation, and limitations are published. A merged design document does not make an experiment complete.

## Learn through the lab

Every project is designed to work as a learning module:

1. Read the research question and background.
2. Understand the hypothesis and measurements.
3. Reproduce a run on available hardware.
4. Inspect the results and limitations.
5. Propose the next measurable question.

Start with the [field guide to learning LLM inference](resources/learning/field_guide.md).

## Safety posture

This repository avoids committing private hostnames, IP addresses, SSH details, API keys, tunnel configuration, private prompts, session content, and local machine paths.

Run the safety scan locally:

```bash
python3 areas/lab_operations/safety_scan.py
```

Or run it through pre commit:

```bash
pre-commit run --all-files
```
