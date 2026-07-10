# Experiment: <short name>

> **Status:** 💡 Proposed | 📝 Designed | 🔬 Running | ✅ Completed | 🧊 Parked
> **Teaches:** <the two or three concepts a reader learns by following this experiment>

One paragraph: what this experiment asks and why it matters to the lab thesis.

## Hypothesis

What you expect to be true, stated so that a result can prove it wrong.

## Method

How the experiment runs: hardware, models, workloads, and what gets measured. Keep it reproducible — someone with similar hardware should be able to repeat it from this section alone.

## Results

Filled in while the experiment is 🔬 Running. Tables and charts live here; raw data and scripts live in this folder next to the writeup.

## Learnings

Filled in when the experiment is ✅ Completed. What turned out to be true, what didn't, and what the next experiment should be. Write this for a reader using the lab to learn — the surprise is usually the lesson.

---

Checklist for a new experiment:

1. Copy this file to `experiments/<experiment-name>/README.md`.
2. Add the experiment to the index in [experiments/README.md](README.md) under its status.
3. Keep the status line and the index in sync as the experiment moves through the lifecycle.
4. Run `python3 scripts/safety_scan.py` before committing — no private hostnames, IPs, keys, or local paths.
