# Public Website

This Area owns the public entry point for Lily, the Longtail Inference Laboratory.

The site is published at <https://raghavan.github.io/longtail-inference-lab/>.

## Why this is an Area

The website is an ongoing responsibility rather than a bounded research project. It remains active as the laboratory evolves and keeps the public presentation aligned with the current research record.

## Contents

1. [`index.html`](index.html) contains the single page website.
2. [`styles.css`](styles.css) contains the shared visual system and responsive behavior.
3. [`experiment.css`](experiment.css) contains styles for the current experiment method and archive note.

## Responsibilities

1. Keep claims aligned with published research.
2. Present the single active experiment clearly.
3. Label archived explorations as archived rather than active evidence.
4. Keep experiment and archive links current.
5. Preserve accessibility and responsive behavior.
6. Maintain the luxury minimalist design language: warm ivory paper, soft black ink, a single bronze accent, fine hairline rules, and generous white space.
7. Avoid analytics, trackers, credentials, and private infrastructure details.
8. Keep deployment reproducible.

## Publishing

[`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) publishes this directory through GitHub Pages whenever website content changes on `main`.

The workflow remains under `.github/workflows/` because GitHub requires that location. The website itself belongs here because it is part of the laboratory ongoing public communication responsibility.

## Change discipline

Before publishing a change:

1. Confirm that every research claim is supported by the repository.
2. Confirm that active and archived work are distinguished clearly.
3. Confirm that links point to current Projects, Archives, or Resources.
4. Preview desktop and mobile layouts.
5. Preserve keyboard focus and reduced motion behavior.
6. Run `python3 areas/lab_operations/safety_scan.py`.
