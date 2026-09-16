import os
from pathlib import Path
import pty
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import wave

from local_voice.core import (
    AnswerServer,
    Cancelled,
    LocalBackend,
    Settings,
    VoiceError,
    process,
    readiness,
    run_turn,
    validate_audio,
    validate_text,
)
from local_voice.device import Controller, SerialButton, record


def write_wav(path, *, rate=16000, frames=16000, channels=1, truncate=False):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x10" * frames * channels)
    if truncate:
        path.write_bytes(path.read_bytes()[:-500])


def wait_until(condition, timeout=3):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError("Condition did not become true")


class FakeBackend:
    def __init__(self):
        self.settings = Settings(Path("/unused"))
        self.calls = []
        self.closed = False
        self.block_answer = False
        self.block_play = False

    def transcribe(self, path, directory, cancel):
        self.calls.append("transcribe")
        return "Name a primary color."

    def answer(self, text, cancel):
        self.calls.append("answer")
        if self.block_answer:
            cancel.wait(4)
            if cancel.is_set():
                raise Cancelled("Operation cancelled.")
        return "Red is a primary color."

    def synthesize(self, text, path, cancel):
        self.calls.append("synthesize")
        write_wav(path)

    def play(self, path, cancel):
        self.calls.append("play")
        if self.block_play:
            cancel.wait(4)
            if cancel.is_set():
                raise Cancelled("Operation cancelled.")

    def close(self):
        self.closed = True


class InputTests(unittest.TestCase):
    def test_stdin_accepts_utf8_and_enforces_text_bound(self):
        from local_voice.cli import read_stdin_text

        for value in ("A café.", "x" * 1201):
            reader, writer = os.pipe()
            try:
                os.write(writer, value.encode())
                os.close(writer)
                if len(value) > 1200:
                    with self.assertRaises(VoiceError):
                        read_stdin_text(reader, threading.Event())
                else:
                    self.assertEqual(read_stdin_text(reader, threading.Event()), value)
            finally:
                os.close(reader)

    def test_stdin_cancellation_does_not_wait_for_eof(self):
        from local_voice.cli import read_stdin_text

        reader, writer = os.pipe()
        cancel = threading.Event()
        timer = threading.Timer(0.1, cancel.set)
        timer.start()
        try:
            with self.assertRaises(Cancelled):
                read_stdin_text(reader, cancel)
        finally:
            timer.cancel()
            os.close(reader)
            os.close(writer)

    def test_text_bounds(self):
        self.assertEqual(validate_text(" hello "), "hello")
        for value in (" ", "x" * 1201):
            with self.assertRaises(VoiceError):
                validate_text(value)

    def test_audio_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "input.wav"
            write_wav(p)
            self.assertEqual(validate_audio(p), 1)
            for kwargs in (
                {"rate": 22050},
                {"frames": 0},
                {"frames": 480001},
                {"channels": 2},
                {"truncate": True},
            ):
                write_wav(p, **kwargs)
                with self.assertRaises(VoiceError):
                    validate_audio(p)
            p.write_text("not audio")
            with self.assertRaises(VoiceError):
                validate_audio(p)

    def test_missing_assets_do_not_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            checks = readiness(Settings(Path(tmp)))
            self.assertFalse(checks["answer_model"])
            self.assertFalse(checks["llama-server"])
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_silent_wav_is_rejected_before_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "silence.wav"
            with wave.open(str(p), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                wav.writeframes(bytes(32000))
            with self.assertRaisesRegex(VoiceError, "silent"):
                validate_audio(p)

    def test_settings_reject_unbounded_generation(self):
        for kwargs in (
            {"threads": 0},
            {"max_tokens": 10000},
            {"answer_timeout": 0},
            {"answer_timeout": float("nan")},
            {"backend": "remote"},
            {"system_prompt": " "},
            {"system_prompt": "x" * 1201},
        ):
            with self.assertRaises(VoiceError):
                Settings(Path("/unused"), **kwargs)


class ProcessTests(unittest.TestCase):
    def test_timeout_terminates_child(self):
        start = time.monotonic()
        with self.assertRaises(VoiceError):
            process(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                threading.Event(),
                0.1,
            )
        self.assertLess(time.monotonic() - start, 2)

    def test_cancel_terminates_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "survived"
            child = (
                "import time,pathlib; time.sleep(1.5); pathlib.Path("
                + repr(str(marker))
                + ").touch()"
            )
            parent = (
                "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',"
                + repr(child)
                + "]); time.sleep(60)"
            )
            cancel = threading.Event()
            timer = threading.Timer(0.3, cancel.set)
            timer.start()
            try:
                with self.assertRaises(Cancelled):
                    process([sys.executable, "-c", parent], cancel, 5)
            finally:
                timer.cancel()
            time.sleep(1.6)
            self.assertFalse(marker.exists())

    def test_failure_is_sanitized(self):
        with self.assertRaises(VoiceError) as caught:
            process(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('PRIVATE EXAMPLE',file=sys.stderr); sys.exit(2)",
                ],
                threading.Event(),
                2,
            )
        self.assertNotIn("PRIVATE EXAMPLE", str(caught.exception))

    def test_pre_cancelled_does_not_execute(self):
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(Cancelled):
            process(["/does/not/exist"], cancel, 2)

    def test_exited_leader_does_not_leave_background_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "survived"
            child = (
                "import time,pathlib; time.sleep(0.5); pathlib.Path("
                + repr(str(marker))
                + ").touch()"
            )
            parent = (
                "import subprocess,sys; subprocess.Popen([sys.executable,'-c',"
                + repr(child)
                + "])"
            )
            process([sys.executable, "-c", parent], threading.Event(), 2)
            time.sleep(0.7)
            self.assertFalse(marker.exists())


class PipelineTests(unittest.TestCase):
    def test_order_and_opt_in_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = FakeBackend()
            output = Path(tmp) / "out.wav"
            states = []
            result = run_turn(
                b,
                threading.Event(),
                text="Hello",
                output=output,
                play=True,
                state=states.append,
            )
            self.assertEqual(b.calls, ["answer", "synthesize", "play"])
            self.assertEqual(states, ["answering", "synthesizing", "speaking", "ready"])
            self.assertEqual(result.answer, "Red is a primary color.")
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(validate_audio(output), 1)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.wav"
            output.write_bytes(b"keep existing")
            with self.assertRaises(FileExistsError):
                run_turn(FakeBackend(), threading.Event(), text="Hello", output=output)
            self.assertEqual(output.read_bytes(), b"keep existing")

    def test_input_modes_are_exclusive(self):
        for kwargs in ({}, {"text": "x", "audio": "x.wav"}):
            with self.assertRaises(VoiceError):
                run_turn(FakeBackend(), threading.Event(), **kwargs)

    def test_cancel_discards_late_answer(self):
        b = FakeBackend()
        cancel = threading.Event()

        def answer(*_):
            cancel.set()
            return "Late output"

        b.answer = answer
        before = set(Path("/dev/shm").glob("local-voice-*"))
        with self.assertRaises(Cancelled):
            run_turn(b, cancel, text="Hello")
        self.assertNotIn("synthesize", b.calls)
        self.assertEqual(set(Path("/dev/shm").glob("local-voice-*")), before)

    def test_failed_stage_cleans_temporary_audio(self):
        b = FakeBackend()

        def bad(*_):
            raise VoiceError("Deliberate test failure")

        b.synthesize = bad
        before = set(Path("/dev/shm").glob("local-voice-*"))
        with self.assertRaises(VoiceError):
            run_turn(b, threading.Event(), text="Hello")
        self.assertEqual(set(Path("/dev/shm").glob("local-voice-*")), before)


class ControllerTests(unittest.TestCase):
    @staticmethod
    def recorder(settings, wav, finished, cancel):
        while not finished.wait(0.01):
            if cancel.is_set():
                raise Cancelled("Operation cancelled.")
        write_wav(wav)

    def test_two_presses_and_repeated_turn(self):
        b = FakeBackend()
        states = []
        c = Controller(b, states.append, self.recorder)
        try:
            for _ in range(2):
                c.press()
                self.assertEqual(c.state, "recording")
                c.press()
                c.worker.join(3)
                self.assertFalse(c.worker.is_alive())
                self.assertEqual(c.state, "ready")
            self.assertEqual(b.calls.count("play"), 2)
        finally:
            c.close()

    def test_cancel_recording(self):
        b = FakeBackend()
        c = Controller(b, recorder=self.recorder)
        c.press()
        c.cancel()
        c.worker.join(3)
        self.assertEqual(c.state, "ready")
        self.assertEqual(b.calls, [])
        c.close()

    def test_busy_press_cancels_and_recovers(self):
        for phase in ("answer", "play"):
            with self.subTest(phase=phase):
                b = FakeBackend()
                setattr(b, "block_" + phase, True)
                c = Controller(b, recorder=self.recorder)
                c.press()
                c.press()
                wait_until(lambda: phase in b.calls)
                c.press()
                c.worker.join(3)
                self.assertEqual(c.state, "ready")
                setattr(b, "block_" + phase, False)
                c.press()
                c.press()
                c.worker.join(3)
                self.assertEqual(c.state, "ready")
                c.close()

    def test_capture_failure_can_retry(self):
        b = FakeBackend()

        def fail(*_):
            raise VoiceError("Device unavailable")

        c = Controller(b, recorder=fail)
        c.press()
        c.worker.join(3)
        self.assertEqual(c.state, "error")
        c.recorder = self.recorder
        c.press()
        c.press()
        c.worker.join(3)
        self.assertEqual(c.state, "ready")
        c.close()

    def test_shutdown_cancels_and_prevents_restart(self):
        b = FakeBackend()
        c = Controller(b, recorder=self.recorder)
        c.press()
        c.close()
        self.assertFalse(c.worker.is_alive())
        self.assertTrue(b.closed)
        c.press()
        self.assertFalse(c.worker.is_alive())

    def test_unexpected_failure_is_sanitized(self):
        b = FakeBackend()

        def fail(*_):
            raise RuntimeError("PRIVATE CONTENT")

        b.answer = fail
        c = Controller(b, recorder=self.recorder)
        c.press()
        c.press()
        c.worker.join(3)
        self.assertEqual(c.state, "error")
        self.assertNotIn("PRIVATE CONTENT", c.error)
        c.close()


class SerialTests(unittest.TestCase):
    def setUp(self):
        self.master, self.slave = pty.openpty()
        self.button = SerialButton(os.ttyname(self.slave))

    def tearDown(self):
        self.button.close()
        os.close(self.master)
        os.close(self.slave)

    def test_fragmented_events_and_debounce(self):
        os.write(self.master, b"PRE")
        time.sleep(0.02)
        self.assertEqual(self.button.read_events(), [])
        os.write(self.master, b"SS\nPRESS\nnoise\nCANCEL\n")
        time.sleep(0.02)
        self.assertEqual(self.button.read_events(), ["press", "cancel"])

    def test_state_feedback(self):
        self.button.state("recording")
        self.assertEqual(os.read(self.master, 100), b"STATE recording\n")

    def test_oversized_frame_fails(self):
        os.write(self.master, b"x" * 5000)
        time.sleep(0.02)
        with self.assertRaises(VoiceError):
            for _ in range(6):
                self.button.read_events()


# A controlled local HTTP process tests process ownership and cancellation. It is
# exclusively a regression fixture; real-model smoke checks live in scripts/.
FAKE_SERVER = r"""#!/usr/bin/env python3
import http.server,json,sys,time
port=int(sys.argv[sys.argv.index('--port')+1])
class H(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_GET(self):
  self.send_response(200); self.end_headers(); self.wfile.write(b'{"status":"ok"}')
 def do_POST(self):
  b=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  text=b['messages'][-1]['content']
  if text=='slow': time.sleep(60)
  content='answer' if text!='empty' else ''
  reason='length' if text=='truncate' else 'stop'
  if text=='history': content=str(len(b['messages']))
  if text=='system': content=b['messages'][0]['content']
  if text=='invalid': data={}
  else: data={'choices':[{'message':{'content':content},'finish_reason':reason}]}
  self.send_response(200); self.end_headers(); self.wfile.write(json.dumps(data).encode())
http.server.HTTPServer(('127.0.0.1',port),H).serve_forever()
"""


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "models").mkdir()
        (root / "models/qwen2.5-1.5b-instruct-q4_k_m.gguf").touch()
        directory = root / "bin/cpu"
        directory.mkdir(parents=True)
        exe = directory / "llama-server"
        exe.write_text(FAKE_SERVER)
        exe.chmod(0o700)
        self.server = AnswerServer(
            Settings(root, answer_timeout=0.5, startup_timeout=3)
        )

    def tearDown(self):
        self.server.close()
        self.tmp.cleanup()

    def test_configured_system_prompt_is_used(self):
        self.server.settings = Settings(
            self.server.settings.root, system_prompt="Reply briefly."
        )
        self.assertEqual(
            self.server.answer("system", threading.Event()), "Reply briefly."
        )

    def test_real_local_http_and_no_history(self):
        with patch.dict(
            os.environ,
            {
                "http_proxy": "http://invalid.example:1",
                "HTTP_PROXY": "http://invalid.example:1",
                "no_proxy": "",
            },
        ):
            self.assertEqual(self.server.answer("hello", threading.Event()), "answer")
            self.assertEqual(self.server.answer("history", threading.Event()), "2")

    def test_rejects_partial_empty_and_malformed_output(self):
        for text in ("truncate", "empty", "invalid"):
            with self.assertRaises(VoiceError):
                self.server.answer(text, threading.Event())

    def test_timeout_reaps_server_and_can_restart(self):
        with self.assertRaises(VoiceError):
            self.server.answer("slow", threading.Event())
        self.assertIsNone(self.server.proc)
        self.assertEqual(self.server.answer("hello", threading.Event()), "answer")

    def test_cancel_reaps_server(self):
        cancel = threading.Event()
        self.server.start(cancel)
        proc = self.server.proc
        timer = threading.Timer(0.1, cancel.set)
        timer.start()
        try:
            with self.assertRaises(Cancelled):
                self.server.answer("slow", cancel)
            self.assertIsNotNone(proc.poll())
            self.assertIsNone(self.server.proc)
        finally:
            timer.cancel()

    def test_redirect_is_not_followed(self):
        from local_voice.core import NoRedirect

        with self.assertRaises(VoiceError):
            NoRedirect().redirect_request(
                None, None, 302, "", {}, "https://example.com"
            )

    def test_missing_model_fails_before_server_start(self):
        self.server.settings.model("answer").unlink()
        with self.assertRaisesRegex(VoiceError, "missing"):
            self.server.start(threading.Event())
        self.assertIsNone(self.server.proc)


class CaptureTests(unittest.TestCase):
    def test_real_alsa_missing_device_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                Path(tmp), capture_device="nonexistent-local-voice-test-device"
            )
            with self.assertRaises(VoiceError):
                record(
                    settings,
                    Path(tmp) / "input.wav",
                    threading.Event(),
                    threading.Event(),
                )

    def test_recording_subprocess_cancels_and_finalizes_on_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exe = root / "arecord"
            exe.write_text("""#!/usr/bin/env python3
import signal,sys,time,wave
running=True
def stop(*_):
 global running
 running=False
signal.signal(signal.SIGINT,stop)
with wave.open(sys.argv[-1],'wb') as wav:
 wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(16000)
 while running:
  wav.writeframes(b'\\x00\\x10'*1600)
  time.sleep(0.1)
""")
            exe.chmod(0o700)
            with patch.dict(
                os.environ, {"PATH": str(root) + os.pathsep + os.environ["PATH"]}
            ):
                for cancelled in (False, True):
                    cancel, finish = threading.Event(), threading.Event()
                    timer = threading.Timer(0.25, (cancel if cancelled else finish).set)
                    timer.start()
                    try:
                        if cancelled:
                            with self.assertRaises(Cancelled):
                                record(
                                    Settings(root), root / "input.wav", finish, cancel
                                )
                        else:
                            record(Settings(root), root / "input.wav", finish, cancel)
                            self.assertGreater(validate_audio(root / "input.wav"), 0)
                    finally:
                        timer.cancel()

    def test_real_alsa_null_playback_accepts_wav(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "output.wav"
            write_wav(path)
            b = LocalBackend(Settings(Path(tmp), playback_device="null"))
            b.play(path, threading.Event())


class ServiceTests(unittest.TestCase):
    def test_service_uses_local_network_and_content_safe_logs(self):
        from scripts.service_unit import unit

        text = unit(
            Path("/opt/voice app"), Path("/opt/runtime"), "voiceuser", "/dev/ttyACM0"
        )
        self.assertIn("WorkingDirectory=/opt/voice app", text)
        self.assertIn("PrivateNetwork=true", text)
        self.assertIn("KillMode=control-group", text)
        self.assertNotIn("--show-text", text)

    def test_unit_rejects_line_injection_and_escapes_expansion(self):
        from scripts.service_unit import quoted, unit

        with self.assertRaises(ValueError):
            quoted("x\nExecStart=bad")
        with self.assertRaises(ValueError):
            unit(Path("/tmp"), Path("/tmp"), "root\nBad", "/dev/ttyACM0")
        self.assertEqual(quoted("a%h$b"), '"a%%h$$b"')


if __name__ == "__main__":
    unittest.main()
