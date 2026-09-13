"""End-to-end local server for the offline voice loop.

The browser captures speech, this server runs the same pipeline the device
experiment tests — local speech recognition, a four-bit compact instruct model,
local speech synthesis — and returns the spoken answer as audio.

Everything runs on this machine. The only network traffic is between the
browser and localhost, plus the local Ollama server on the same host.

    python3 app/server.py --stub          # no models, verifies the whole path
    python3 app/server.py                 # real models

This is a demo of the loop, not Experiment 02.1. See README.md in this folder
for exactly which of its numbers mean anything.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import threading
import time
import uuid
import wave
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SOFTWARE_DIR = APP_DIR.parent
STATIC_DIR = APP_DIR / "static"
sys.path.insert(0, str(SOFTWARE_DIR))

from controller import backends as backends_module  # noqa: E402
from controller.ledger import Interaction, LedgerWriter  # noqa: E402
from controller.pipeline import PipelineConfig, ensure_resident, run_interaction  # noqa: E402

MAX_UPLOAD_BYTES = 25 * 1024 * 1024

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".json": "application/json",
}


class CollectingPlayer:
    """Stands in for the speaker: the browser does the playing."""

    def __init__(self) -> None:
        self.paths: list[Path] = []

    def play(self, wav_path: Path) -> None:
        self.paths.append(Path(wav_path))

    def wait(self) -> None:
        return


def concat_wavs(paths: list[Path], out_path: Path) -> Path | None:
    """Join synthesized chunks into one file for delivery."""
    real = [p for p in paths if p.exists()]
    if not real:
        return None
    with wave.open(str(real[0]), "rb") as first:
        params = first.getparams()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as out:
        out.setparams(params)
        for path in real:
            with wave.open(str(path), "rb") as chunk:
                if chunk.getnchannels() != params.nchannels or \
                   chunk.getframerate() != params.framerate:
                    continue
                out.writeframes(chunk.readframes(chunk.getnframes()))
    return out_path


class Engine:
    """Owns the backends and serializes access to them."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.stub = args.stub
        self.lock = threading.Lock()
        self.config = PipelineConfig(
            residency=args.residency,
            # The browser receives one finished audio file, so sentence
            # streaming would be invisible here. Held fixed and declared.
            synthesis="whole",
        )
        self.run_id = uuid.uuid4().hex[:8]
        self.index = 0
        self.scratch = backends_module.scratch_dir()
        self.scratch.mkdir(parents=True, exist_ok=True)

        if self.stub:
            timings = backends_module.StubTimings()
            self.stt = backends_module.StubSpeechToText(
                "What is a tide?", timings
            )
            self.llm = backends_module.StubLanguageModel(timings)
            self.tts = backends_module.StubTextToSpeech(timings)
        else:
            self.stt = backends_module.FasterWhisperSpeechToText(
                model_name=args.stt_model, device=args.stt_device
            )
            self.llm = backends_module.OllamaLanguageModel(
                model=args.llm_model,
                system_prompt=self.config.system_prompt,
                max_tokens=args.max_tokens,
            )
            self.tts = backends_module.PiperTextToSpeech(voice_path=Path(args.piper_voice))

        self.ledger = LedgerWriter(
            Path(args.out),
            {
                "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "surface": "browser app",
                "stub": self.stub,
                "condition": self.config.condition,
                "models": {
                    "stt": "stub" if self.stub else args.stt_model,
                    "llm": "stub" if self.stub else args.llm_model,
                    "tts": "stub" if self.stub else args.piper_voice,
                },
                "is_measurement": False,
                "note": (
                    "Browser demo on general-purpose hardware. Capture, upload and "
                    "playback happen outside these timings, so this is not a "
                    "first-word latency measurement and is never pooled with "
                    "Experiment 02.1."
                ),
            },
        )

    def warm(self) -> None:
        if self.config.residency == "resident":
            ensure_resident(self.stt, self.llm, self.tts)

    def ask(self, wav_bytes: bytes) -> dict:
        with self.lock:
            self.index += 1
            index = self.index
            upload = self.scratch / f"{self.run_id}-{index}-in.wav"
            upload.write_bytes(wav_bytes)

            interaction = Interaction(
                run_id=self.run_id,
                index=index,
                condition=self.config.condition,
                question_id=f"web-{index}",
                meta={"surface": "browser app", "stub": self.stub},
            )
            interaction.durations_ms["capture"] = 0.0
            player = CollectingPlayer()

            started = time.perf_counter()
            turn = run_interaction(
                interaction,
                lambda: upload,
                self.stt,
                self.llm,
                self.tts,
                self.config,
                player,
            )
            server_ms = (time.perf_counter() - started) * 1000.0

            answer_path = concat_wavs(
                player.paths, self.scratch / f"{self.run_id}-{index}-out.wav"
            )
            audio_b64 = ""
            if answer_path is not None:
                audio_b64 = base64.b64encode(answer_path.read_bytes()).decode("ascii")

            interaction.meta.update(
                {
                    "transcript": turn.transcript,
                    "answer_chars": len(turn.answer),
                    "server_ms": round(server_ms, 3),
                }
            )
            self.ledger.write(interaction)

            return {
                "transcript": turn.transcript,
                "answer": turn.answer,
                "audio": audio_b64,
                "server_ms": round(server_ms, 1),
                "stages_ms": {k: round(v, 1) for k, v in interaction.durations_ms.items()},
                "stub": self.stub,
            }


class Handler(BaseHTTPRequestHandler):
    engine: Engine

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("  %s\n" % (fmt % args))

    # ------------------------------------------------------------------ send

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload).encode("utf-8"), "application/json")

    # ------------------------------------------------------------------- get

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/static/index.html"
        if path == "/api/health":
            engine = self.engine
            self._send_json(200, {
                "ok": True,
                "stub": engine.stub,
                "residency": engine.config.residency,
                "synthesis": engine.config.synthesis,
                "models": {
                    "stt": "stub" if engine.stub else engine.args.stt_model,
                    "llm": "stub" if engine.stub else engine.args.llm_model,
                },
            })
            return

        if path.startswith("/static/"):
            target = (STATIC_DIR / path[len("/static/"):]).resolve()
            if STATIC_DIR.resolve() in target.parents and target.is_file():
                self._send(200, target.read_bytes(),
                           CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
                return

        self._send_json(404, {"error": "not found"})

    # ------------------------------------------------------------------ post

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/ask":
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "bad Content-Length"})
            return
        if length <= 44:
            self._send_json(400, {"error": "no audio received"})
            return
        if length > MAX_UPLOAD_BYTES:
            self._send_json(413, {"error": "recording too long"})
            return

        wav_bytes = self.rfile.read(length)
        try:
            payload = self.engine.ask(wav_bytes)
        except backends_module.BackendError as exc:
            self._send_json(503, {"error": str(exc)})
            return
        except Exception as exc:  # surfaced in the browser rather than swallowed
            self._send_json(500, {"error": f"{type(exc).__name__}: {exc}"})
            return

        self._send_json(200, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--stub", action="store_true",
                        help="run without any model, to verify the full path")
    parser.add_argument("--residency", choices=("sequential", "resident"), default="resident")
    parser.add_argument("--stt-model", default="small.en")
    parser.add_argument("--stt-device", default="auto")
    parser.add_argument("--llm-model", default="qwen3:4b")
    parser.add_argument("--piper-voice", default="voices/en_US-lessac-medium.onnx")
    parser.add_argument("--max-tokens", type=int, default=160)
    parser.add_argument("--out", default=str(SOFTWARE_DIR / "runs" / "app.jsonl"))
    args = parser.parse_args(argv)

    if not args.stub:
        voice = Path(args.piper_voice)
        if not voice.is_absolute():
            voice = SOFTWARE_DIR / voice
        args.piper_voice = str(voice)

    engine = Engine(args)
    Handler.engine = engine

    print("Longtail Model One — local end-to-end server")
    print(f"  mode      {'STUB (no models)' if args.stub else 'real models'}")
    if not args.stub:
        print(f"  speech    {args.stt_model}")
        print(f"  answers   {args.llm_model} via Ollama")
        print(f"  voice     {args.piper_voice}")
    print(f"  residency {args.residency}")
    print(f"  ledger    {args.out}")

    if not args.stub:
        print("\nLoading models. First run downloads the speech model, so give it a minute...")
    try:
        engine.warm()
    except backends_module.BackendError as exc:
        print(f"\nCould not start: {exc}", file=sys.stderr)
        return 1

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"\n  ready →  http://{args.host}:{args.port}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
