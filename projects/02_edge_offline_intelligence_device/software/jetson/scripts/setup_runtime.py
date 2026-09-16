#!/usr/bin/env python3
"""Explicit online setup only. Inference never imports or invokes this script."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import urllib.request


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--root", type=Path, default=Path.home() / ".local/share/longtail-voice"
    )
    p.add_argument("--backend", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--jobs", type=int, default=4)
    a = p.parse_args()
    if platform.system() != "Linux":
        p.error("Build inside Linux, not macOS.")
    if not 1 <= a.jobs <= 16:
        p.error("jobs must be between 1 and 16")
    if a.backend == "cuda" and not shutil.which("nvcc"):
        p.error(
            "Install the CUDA toolkit supplied by the target JetPack release first."
        )
    root = a.root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = json.loads(
        (Path(__file__).resolve().parents[1] / "runtime-lock.json").read_text()
    )
    for key, target in (("llama_cpp", "llama-server"), ("whisper_cpp", "whisper-cli")):
        spec = lock[key]
        src = root / "sources" / key
        if not (src / ".git").exists():
            src.mkdir(parents=True, exist_ok=True)
            run("git", "init", src)
            run("git", "-C", src, "remote", "add", "origin", spec["repository"])
        run("git", "-C", src, "fetch", "--depth=1", "origin", spec["commit"])
        run("git", "-C", src, "checkout", "--detach", spec["commit"])
        build = src / ("build-" + a.backend)
        flags = [
            "-DCMAKE_BUILD_TYPE=Release",
            "-DGGML_NATIVE=OFF",
            "-DGGML_METAL=OFF",
            "-DGGML_CUDA=" + ("ON" if a.backend == "cuda" else "OFF"),
        ]
        if key == "llama_cpp":
            flags += ["-DLLAMA_CURL=OFF", "-DLLAMA_BUILD_TESTS=OFF"]
        if a.backend == "cuda":
            flags += ["-DCMAKE_CUDA_ARCHITECTURES=87"]
        run("cmake", "-S", src, "-B", build, *flags)
        run("cmake", "--build", build, "--target", target, "-j", a.jobs)
        bindir = root / "bin" / a.backend
        bindir.mkdir(parents=True, exist_ok=True)
        link = bindir / target
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            raise RuntimeError("Refusing to replace a non-symlink runtime executable")
        link.symlink_to(build / "bin" / target)
    models = root / "models"
    models.mkdir(exist_ok=True)
    for key in ("answer_model", "speech_model"):
        spec = lock[key]
        dest = models / spec["file"]
        if dest.exists() and sha256(dest) == spec["sha256"]:
            print("Verified", spec["file"], flush=True)
            continue
        url = "https://huggingface.co/{repository}/resolve/{revision}/{file}".format(
            **spec
        )
        part = dest.with_suffix(dest.suffix + ".part")
        print("Downloading", spec["file"], flush=True)
        try:
            with (
                urllib.request.urlopen(url, timeout=60) as response,
                part.open("wb") as out,
            ):
                shutil.copyfileobj(response, out, 1024 * 1024)
            if part.stat().st_size != spec["bytes"] or sha256(part) != spec["sha256"]:
                raise RuntimeError("Model checksum mismatch; installation stopped")
            os.replace(part, dest)
        finally:
            part.unlink(missing_ok=True)
    installed = {"backend": a.backend, "architecture": platform.machine(), "lock": lock}
    (root / ("installed-" + a.backend + ".json")).write_text(
        json.dumps(installed, indent=2) + "\n"
    )
    print("Runtime ready. No inference was performed.")


if __name__ == "__main__":
    main()
