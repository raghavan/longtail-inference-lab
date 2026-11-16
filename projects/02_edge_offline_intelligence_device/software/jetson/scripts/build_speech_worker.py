#!/usr/bin/env python3
"""Build the small persistent-ASR adapter against an existing pinned native build."""
import argparse
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, required=True)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--backend', choices=['cpu', 'cuda'], default='cuda')
a = p.parse_args()
app = Path(__file__).resolve().parents[1]
lock = json.loads((app / 'runtime-lock.json').read_text())
# The source checkout must match the same version used to build libwhisper.
revision = subprocess.check_output(['git', '-C', str(a.source), 'rev-parse', 'HEAD'], text=True).strip()
expected = lock['whisper_cpp']['commit']
if revision != expected:
    raise SystemExit('Whisper source revision does not match runtime lock.')
build = a.source / ('build-' + a.backend)
lib = build / 'bin'
out = a.root / 'bin' / a.backend / 'local-voice-whisper.so'
subprocess.run(['c++', '-std=c++17', '-O2', '-shared', '-fPIC',
                str(app / 'native/whisper_worker.cpp'), '-I' + str(a.source / 'include'),
                '-I' + str(a.source / 'ggml/include'), '-L' + str(lib), '-lwhisper',
                '-Wl,-rpath,' + str(lib.resolve()), '-o', str(out)], check=True)
print('Persistent recognition adapter built.')
