# Safety scan

This repo includes a lightweight safety scan that can run locally and in CI.

The scanner looks for common mistakes that should not be committed to a public research repo:

- private key blocks
- API tokens and common provider keys
- secret like assignments
- public IP addresses
- SSH hostnames and direct SSH commands
- WireGuard and Tailscale auth key hints
- personal machine paths

It is intentionally simple and dependency free. It is not a replacement for GitHub secret scanning or a dedicated tool such as gitleaks.

## Run locally

```bash
python3 scripts/safety_scan.py
```

## Install the pre commit hook

```bash
python3 -m pip install pre-commit
pre-commit install
```

After installation, the scanner runs on changed text files before each commit.

You can also run it manually across the repo:

```bash
pre-commit run --all-files
```

## CI behavior

The GitHub Actions workflow runs the same scanner on every push to `main` and on every pull request.

## Handling false positives

Prefer replacing real values with placeholders, for example:

```text
VPS_HOST=<your-vps-host>
SSH_USER=<your-ssh-user>
PUBLIC_IP=<redacted>
```

Do not commit allowlists for real secrets. If the scanner flags something real, remove the value and rotate the credential if it was already pushed.
