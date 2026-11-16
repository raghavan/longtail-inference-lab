#!/usr/bin/env python3
"""Install the locked ARM64 neural voice runtime from verified local wheels only."""

import argparse
import hashlib
from pathlib import Path
import platform
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.home() / '.local/share/longtail-voice')
    parser.add_argument('--wheel-dir', type=Path, required=True)
    args = parser.parse_args()
    if (platform.system() != 'Linux' or platform.machine() != 'aarch64'
            or sys.version_info[:2] != (3, 10)):
        parser.error('Install these pinned wheels on Linux aarch64 with Python 3.10.')
    requirements = Path(__file__).resolve().parents[1] / 'piper-requirements.txt'
    expected = {}
    for line in requirements.read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            package, digest = line.split(' --hash=sha256:')
            expected[package] = digest
    wheels = {}
    for path in args.wheel_dir.expanduser().resolve().glob('*.whl'):
        wheels[hashlib.sha256(path.read_bytes()).hexdigest()] = path
    if set(expected.values()) - wheels.keys():
        raise RuntimeError('Required voice wheels are missing or failed hash verification.')
    bootstrap = wheels[expected['pip==25.3']]
    env = args.root.expanduser().resolve() / 'tts-venv'
    subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(env)], check=True)
    # Verify the bootstrap wheel before executing it. No package index is consulted.
    subprocess.run([
        str(env / 'bin/python3'), '-c',
        'import runpy,sys; sys.path.insert(0,sys.argv.pop(1)); runpy.run_module("pip",run_name="__main__")',
        str(bootstrap), 'install', '--no-index', '--disable-pip-version-check',
        '--find-links', str(args.wheel_dir.resolve()), '--require-hashes', '-r', str(requirements),
    ], check=True)
    subprocess.run([str(env / 'bin/python3'), '-m', 'pip', 'check'], check=True)
    print('Neural speech runtime installed from verified local wheels. No inference performed.')


if __name__ == '__main__':
    main()
