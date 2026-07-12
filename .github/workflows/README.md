# Workflows

This folder contains GitHub Actions workflows for the lab.

## Safety scan

`safety-scan.yml` runs the repository safety scanner for pull requests and pushes to `main`.

The scanner implementation and documentation live under [`areas/lab_operations/`](../../areas/lab_operations/README.md).

## Website deployment

`pages.yml` publishes [`areas/public_website/`](../../areas/public_website/README.md) through GitHub Pages when the website Area changes on `main`.

The workflow lives here because GitHub requires workflows under `.github/workflows/`. The website content remains in its PARA Area.
