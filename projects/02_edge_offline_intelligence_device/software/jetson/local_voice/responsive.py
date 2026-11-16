"""Resident speech workers and bounded phrase streaming for the physical device."""
import json
import os
from pathlib import Path
import queue
import re
import select
import subprocess
import threading
import time
import urllib.request
import wave

from .core import (AnswerServer, Cancelled, LocalBackend, MAX_OUTPUT_CHARS, Result, VoiceError,
                   check_cancel, private_workspace, stop_process, validate_audio, validate_text)


class CancelScope:
    """Internal failure can stop peers without misreporting it as user cancellation."""
    def __init__(self, parent):
        self.parent, self.local = parent, threading.Event()

    def is_set(self):
        return self.local.is_set() or self.parent.is_set()

    def set(self):
        self.local.set()

    def wait(self, timeout):
        deadline = time.monotonic() + timeout
        while not self.is_set() and time.monotonic() < deadline:
            self.local.wait(min(0.02, max(0, deadline - time.monotonic())))
        return self.is_set()


class SpeechWorker:
    """One owned subprocess and one in-flight request; cancellation reaps it."""
    def __init__(self, settings, role):
        self.settings, self.role = settings, role
        self.proc = None
        self.buffer = bytearray()
        self.lock = threading.RLock()

    def close(self):
        with self.lock:
            if self.proc is not None:
                stop_process(self.proc)
                self.proc.stdin.close()
                self.proc.stdout.close()
                self.proc = None
            self.buffer.clear()

    def _receive(self, cancel, timeout):
        deadline = time.monotonic() + timeout
        while True:
            check_cancel(cancel)
            if time.monotonic() > deadline:
                raise VoiceError('Local speech worker exceeded its time limit.')
            if b'\n' in self.buffer:
                line, _, rest = self.buffer.partition(b'\n')
                self.buffer = bytearray(rest)
                try:
                    result = json.loads(line)
                    if not isinstance(result, dict):
                        raise ValueError()
                    return result
                except (ValueError, UnicodeError) as exc:
                    raise VoiceError('Local speech worker returned invalid output.') from exc
            if not select.select([self.proc.stdout], [], [], 0.02)[0]:
                continue
            data = os.read(self.proc.stdout.fileno(), 4096)
            if not data:
                raise VoiceError('Local speech worker exited unexpectedly.')
            self.buffer.extend(data)
            if len(self.buffer) > 32768:
                raise VoiceError('Local speech worker exceeded its output bound.')

    def start(self, cancel):
        with self.lock:
            check_cancel(cancel)
            if self.proc is not None and self.proc.poll() is None:
                return
            self.close()
            args = [self.settings.root / 'tts-venv/bin/python',
                    Path(__file__).with_name('speech_worker.py'), self.role,
                    self.settings.root, self.settings.backend, str(self.settings.threads)]
            try:
                self.proc = subprocess.Popen([str(x) for x in args], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
                if self._receive(cancel, self.settings.startup_timeout) != {'ready': True}:
                    raise VoiceError('Local speech worker did not become ready.')
            except BaseException:
                self.close()
                raise

    def request(self, request, cancel, timeout):
        with self.lock:
            try:
                self.start(cancel)
                data = json.dumps(request).encode() + b'\n'
                if len(data) > 32768:
                    raise VoiceError('Local speech request exceeds its size limit.')
                self.proc.stdin.write(data)
                self.proc.stdin.flush()
                return self._receive(cancel, timeout)
            except BaseException:
                self.close()
                raise


def put_bounded(q, value, cancel):
    while True:
        check_cancel(cancel)
        try:
            q.put(value, timeout=0.02)
            return
        except queue.Full:
            pass


class StreamingAnswerServer(AnswerServer):
    cache_prompt = True

    def phrases(self, text, cancel):
        cancel = CancelScope(cancel)
        text = validate_text(text)
        self.start(cancel)
        messages = queue.Queue(maxsize=2)
        done = threading.Event()
        errors = []
        body = {'messages': [{'role': 'system', 'content': self.settings.system_prompt},
                             {'role': 'user', 'content': text}],
                'max_tokens': self.settings.max_tokens, 'temperature': 0, 'seed': 42,
                'stream': True, 'cache_prompt': self.cache_prompt,
                'chat_template_kwargs': {'enable_thinking': False}}

        def request():
            pending, total, finished, size = '', '', False, 0
            try:
                req = urllib.request.Request(self.url + '/v1/chat/completions',
                    data=json.dumps(body).encode(), headers={'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + self.key})
                with self.http.open(req, timeout=self.settings.answer_timeout) as response:
                    while True:
                        check_cancel(cancel)
                        line = response.readline(65537)
                        size += len(line)
                        if len(line) > 65536 or size > 1_000_000:
                            raise VoiceError('Local answer stream exceeded its size limit.')
                        if not line:
                            raise VoiceError('Local answer stream ended unexpectedly.')
                        if not line.startswith(b'data: '):
                            continue
                        payload = line[6:].strip()
                        if payload == b'[DONE]':
                            if not finished or not total.strip():
                                raise VoiceError('Local answer stream was incomplete.')
                            if pending.strip():
                                put_bounded(messages, pending.strip(), cancel)
                            return
                        event = json.loads(payload)
                        if not event.get('choices'):
                            continue
                        choice = event['choices'][0]
                        delta = choice.get('delta', {})
                        content = delta.get('content') or ''
                        if not isinstance(content, str) or delta.get('tool_calls'):
                            raise VoiceError('Local model returned unsupported control output.')
                        # Reject special markup before any part of it can be spoken,
                        # including control tokens split across successive SSE events.
                        if '<' in content or '\x00' in content:
                            raise VoiceError('Local model returned unsupported control output.')
                        total += content
                        if len(total) > MAX_OUTPUT_CHARS:
                            raise VoiceError('Local answer exceeds its output bound.')
                        pending += content
                        reason = choice.get('finish_reason')
                        if reason:
                            if reason != 'stop':
                                raise VoiceError('Answer reached its output limit; remaining speech was discarded.')
                            finished = True
                        # Only complete sentences/clauses, never individual tokens.
                        # A following space avoids splitting decimals across tokens.
                        while True:
                            match = re.search(r'[.!?;:]\s+', pending)
                            if not match:
                                break
                            end = match.end()
                            phrase, pending = pending[:end].strip(), pending[end:]
                            if phrase:
                                put_bounded(messages, phrase, cancel)
            except Exception as exc:
                errors.append(exc if isinstance(exc, VoiceError) else VoiceError('Local answer stream failed.'))
            finally:
                done.set()

        thread = threading.Thread(target=request, name='answer-stream', daemon=True)
        thread.start()
        deadline = time.monotonic() + self.settings.answer_timeout
        completed = False
        try:
            while not done.is_set() or not messages.empty():
                check_cancel(cancel)
                if errors:
                    raise errors[0]
                if time.monotonic() > deadline:
                    raise VoiceError('Local answer exceeded its time limit.')
                try:
                    yield messages.get(timeout=0.02)
                except queue.Empty:
                    pass
            if errors:
                raise errors[0]
            completed = True
        finally:
            if not completed:
                # Stop generation, including requests blocked behind phrase backpressure.
                cancel.set()
                if not done.is_set() or errors:
                    self.close()
            thread.join(2)


class ResponsiveBackend(LocalBackend):
    def __init__(self, settings):
        super().__init__(settings)
        self.server = StreamingAnswerServer(settings)
        self.asr = SpeechWorker(settings, 'asr')
        self.tts = SpeechWorker(settings, 'tts')
        self.prepared = None

    def close(self):
        self.server.close()
        self.asr.close()
        self.tts.close()

    def prepare(self, cancel):
        check_cancel(cancel)
        processes = (self.asr.proc, self.tts.proc, self.server.proc)
        if self.prepared == processes and all(p is not None and p.poll() is None for p in processes):
            return
        # Health alone does not warm GPU kernels. Use fixed, non-private fixtures.
        self.asr.start(cancel)
        self.tts.start(cancel)
        self.server.start(cancel)
        with private_workspace() as tmp:
            path = Path(tmp) / 'warm.wav'
            self.synthesize('Ready.', path, cancel)
            # Warm recognition kernels with bounded synthetic silence; ignore text.
            with wave.open(str(path), 'wb') as wav:
                wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                wav.writeframes(bytes(32000))
            self.asr.request({'path': str(path)}, cancel, self.settings.transcription_timeout)
        self.server.answer('Reply with the single word Ready.', cancel)
        self.prepared = (self.asr.proc, self.tts.proc, self.server.proc)

    def transcribe(self, wav, directory, cancel):
        validate_audio(wav)
        result = self.asr.request({'path': str(wav)}, cancel, self.settings.transcription_timeout)
        return validate_text(result.get('text', ''))

    def synthesize(self, text, destination, cancel):
        if not text.strip() or len(text) > MAX_OUTPUT_CHARS:
            raise VoiceError('Answer cannot be synthesized within the output bounds.')
        result = self.tts.request({'text': text, 'path': str(destination)}, cancel, 30)
        if result != {'ok': True}:
            raise VoiceError('Local speech worker returned invalid output.')
        with wave.open(str(destination), 'rb') as wav:
            if not 0 < wav.getnframes() / wav.getframerate() <= 120:
                raise VoiceError('Synthesized speech exceeds the playback limit.')

    def respond(self, text, cancel, state=lambda _: None):
        """Overlap generation, synthesis and playback; log durations only upstream."""
        cancel = CancelScope(cancel)
        text = validate_text(text)
        start = time.monotonic()
        audio_queue = queue.Queue(maxsize=2)
        done = threading.Event()
        errors, phrases = [], []
        times = {}
        with private_workspace() as tmp:
            directory = Path(tmp)
            state('answering')

            def produce():
                duration = 0
                stream = self.server.phrases(text, cancel)
                try:
                    for index, phrase in enumerate(stream):
                        check_cancel(cancel)
                        phrases.append(phrase)
                        times.setdefault('first_phrase', round(time.monotonic() - start, 3))
                        path = directory / ('phrase-%d.wav' % index)
                        self.synthesize(phrase, path, cancel)
                        with wave.open(str(path), 'rb') as wav:
                            duration += wav.getnframes() / wav.getframerate()
                        if duration > 120:
                            raise VoiceError('Synthesized speech exceeds the playback limit.')
                        put_bounded(audio_queue, path, cancel)
                except Exception as exc:
                    errors.append(exc if isinstance(exc, VoiceError) else VoiceError('Local speech generation failed.'))
                    cancel.set()
                finally:
                    stream.close()
                    done.set()

            worker = threading.Thread(target=produce, name='phrase-synthesis', daemon=True)
            worker.start()
            successful = False
            try:
                while not done.is_set() or not audio_queue.empty():
                    check_cancel(cancel)
                    if errors:
                        raise errors[0]
                    try:
                        path = audio_queue.get(timeout=0.02)
                    except queue.Empty:
                        continue
                    if 'first_playback_request' not in times:
                        times['first_playback_request'] = round(time.monotonic() - start, 3)
                        state('speaking')
                    self.play(path, cancel)
                    path.unlink(missing_ok=True)
                if errors:
                    raise errors[0]
                check_cancel(cancel)
                times['playback_complete'] = round(time.monotonic() - start, 3)
                successful = True
                return Result(text, ' '.join(phrases), times)
            except Cancelled:
                if errors:
                    raise errors[0]
                raise
            finally:
                if not successful:
                    cancel.set()
                worker.join(5)
                if worker.is_alive():
                    raise VoiceError('Speech processing did not stop cleanly.')


class LiveTranscription:
    """Provisional whole-prefix recognition; never answer from an unfinished prefix.

    Exact PCM matches may be reused. Any additional captured sample forces a full
    final pass, preserving quiet trailing words and negations without VAD guesses.
    """
    def __init__(self, backend, directory, cancel):
        self.backend, self.directory, self.cancel = backend, directory, cancel
        self.latest = None
        self.cached = None
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.last_submit = 0
        self.worker = threading.Thread(target=self._run, name='live-recognition', daemon=True)
        self.worker.start()

    def update(self, raw):
        now = time.monotonic()
        if now - self.last_submit < 0.75:
            return
        try:
            with raw.open('rb') as source:
                pcm = source.read(960001)
        except FileNotFoundError:
            return
        if not 16000 <= len(pcm) <= 960000:
            return
        pcm = pcm[:len(pcm) // 2 * 2]
        self.last_submit = now
        with self.lock:
            self.latest = pcm

    def _run(self):
        path = self.directory / 'provisional.wav'
        try:
            while not self.stop.wait(0.03) and not self.cancel.is_set():
                with self.lock:
                    pcm, self.latest = self.latest, None
                if pcm is None:
                    continue
                with wave.open(str(path), 'wb') as wav:
                    wav.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                    wav.writeframes(pcm)
                try:
                    text = self.backend.transcribe(path, self.directory, self.cancel)
                    self.cached = (pcm, text)
                except VoiceError:
                    # Silence or an incomplete fragment is not a final-turn error.
                    pass
        finally:
            path.unlink(missing_ok=True)

    def finish(self, wav):
        self.close()
        validate_audio(wav)
        with wave.open(str(wav), 'rb') as source:
            pcm = source.readframes(source.getnframes())
        if self.cached is not None and self.cached[0] == pcm:
            return self.cached[1]
        return self.backend.transcribe(wav, self.directory, self.cancel)

    def close(self):
        self.stop.set()
        self.worker.join(self.backend.settings.transcription_timeout + 2)
        if self.worker.is_alive():
            raise VoiceError('Live recognition did not stop cleanly.')
