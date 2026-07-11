# Safety Scan

This Area includes a lightweight safety scan that can run locally and in continuous integration.

The scanner looks for common mistakes that should not be committed to a public research repository:

1. Private key blocks.
2. API tokens and common provider keys.
3. Secret like assignments.
4. Public IP addresses.
5. SSH hostnames and direct SSH commands.
6. WireGuard and Tailscale authentication key hints.
7. Personal machine paths.

It is intentionally simple and dependency free. It is not a replacement for GitHub secret scanning or a dedicated secret scanning product.

## Run locally

```bash
python3 areas/lab_operations/safety_scan.py
```

## Install the pre commit hook

```bash
python3 -m pip install pre-commit
pre-commit install
```

After installation, the scanner runs on changed text files before each commit.

You can also run it manually across the repository:

```bash
pre-commit run --all-files
```

## Continuous integration behavior

The GitHub Actions workflow runs the same scanner on every push to `main` and on every pull request.

## Handling false positives

Prefer replacing real values with placeholders, for example:

```text
VPS_HOST=<your-vps-host>
SSH_USER=<your-ssh-user>
PUBLIC_IP=<redacted>
```

Do not commit allowlists for real secrets. Remove any exposed value and rotate the credential when necessary.
