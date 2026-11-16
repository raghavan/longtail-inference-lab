"""Streaming failure, cancellation, lifetime and final-audio correctness contracts."""
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import wave

from local_voice.core import Cancelled, Settings, VoiceError, private_workspace
from local_voice.responsive import (LiveTranscription, ResponsiveBackend, SpeechWorker,
                                    StreamingAnswerServer)
from local_voice.device import Controller
from test_voice import FakeBackend, write_wav

STREAM_SERVER = r'''#!/usr/bin/env python3
import http.server,json,sys,time
port=int(sys.argv[sys.argv.index('--port')+1])
class H(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(b'{"status":"ok"}')
 def do_POST(self):
  b=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  text=b['messages'][-1]['content']
  assert len(b['messages'])==2 and b['cache_prompt'] is True
  self.send_response(200);self.end_headers()
  def send(delta,reason=None):
   data={'choices':[{'delta':delta,'finish_reason':reason}]}
   self.wfile.write(('data: '+json.dumps(data)+'\n\n').encode());self.wfile.flush()
  if text=='slow':time.sleep(60)
  if text=='control':
   send({'content':'<'});send({'content':'|channel>private'})
  elif text=='reasoning':
   send({'reasoning_content':'UNSPOKEN'});send({'content':'Answer.'})
  elif text=='tool':send({'tool_calls':[{'function':{'name':'x'}}]})
  elif text=='oversize':send({'content':'x'*4001})
  elif text=='decimal':
   for c in ['It costs 3.','14 dollars. ','That is all.']:send({'content':c})
  else:
   send({'content':'First sentence. '});time.sleep(.1);send({'content':'Second sentence.'})
  if text=='disconnect':return
  send({},'length' if text=='truncate' else 'stop')
  self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()
http.server.HTTPServer(('127.0.0.1',port),H).serve_forever()
'''


class StreamingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root/'models').mkdir()
        Settings(root).model('answer').touch()
        exe = root/'bin/cpu/llama-server'
        exe.parent.mkdir(parents=True)
        exe.write_text(STREAM_SERVER); exe.chmod(0o700)
        self.server = StreamingAnswerServer(Settings(root, answer_timeout=1, startup_timeout=3))

    def tearDown(self):
        self.server.close(); self.tmp.cleanup()

    def test_phrases_arrive_before_completion_and_no_reasoning(self):
        stream = self.server.phrases('hello', threading.Event())
        self.assertEqual(next(stream), 'First sentence.')
        self.assertEqual(list(stream), ['Second sentence.'])
        self.assertEqual(list(self.server.phrases('reasoning', threading.Event())), ['Answer.'])

    def test_decimal_is_not_split(self):
        self.assertEqual(list(self.server.phrases('decimal', threading.Event())),
                         ['It costs 3.14 dollars.', 'That is all.'])

    def test_failure_does_not_become_user_cancel_and_reaps_server(self):
        for mode in ('truncate','disconnect','control','tool','oversize'):
            with self.subTest(mode=mode):
                cancel=threading.Event()
                with self.assertRaises(VoiceError) as caught:
                    list(self.server.phrases(mode,cancel))
                self.assertNotIsInstance(caught.exception,Cancelled)
                self.assertFalse(cancel.is_set())
                self.assertIsNone(self.server.proc)

    def test_finished_generation_survives_later_playback_cancel(self):
        stream=self.server.phrases('hello',threading.Event())
        self.assertEqual(next(stream),'First sentence.')
        owned=self.server.proc
        time.sleep(.3)
        stream.close()
        self.assertIs(self.server.proc,owned)
        self.assertIsNone(owned.poll())

    def test_stream_cancel_and_recovery(self):
        cancel=threading.Event()
        self.server.start(cancel)
        timer=threading.Timer(.1,cancel.set);timer.start()
        try:
            with self.assertRaises(Cancelled):list(self.server.phrases('slow',cancel))
        finally:timer.cancel()
        self.assertIsNone(self.server.proc)
        self.assertEqual(len(list(self.server.phrases('hello',threading.Event()))),2)


WORKER = r'''
import json,sys,time,os
print('{"ready":true}',flush=True)
for line in sys.stdin:
 r=json.loads(line)
 if r.get('slow'):time.sleep(60)
 if r.get('fail'):sys.exit(2)
 if r.get('oversize'):print('x'*33000,flush=True)
 else:print(json.dumps({'pid':os.getpid()}),flush=True)
'''


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name)
        exe=root/'tts-venv/bin/python';exe.parent.mkdir(parents=True)
        # A controlled subprocess exercises the real pipe, timeout and reaping logic.
        exe.write_text('#!'+sys.executable+'\n'+WORKER);exe.chmod(0o700)
        self.worker=SpeechWorker(Settings(root,startup_timeout=2),'tts')
    def tearDown(self):self.worker.close();self.tmp.cleanup()
    def test_reuses_process_and_recovers_after_failure(self):
        first=self.worker.request({},threading.Event(),1)
        self.assertEqual(first,self.worker.request({},threading.Event(),1))
        old=self.worker.proc
        with self.assertRaises(VoiceError):self.worker.request({'fail':True},threading.Event(),1)
        self.assertIsNotNone(old.poll())
        self.assertNotEqual(first,self.worker.request({},threading.Event(),1))
    def test_cancel_timeout_and_bounded_output(self):
        for mode in ('cancel','timeout','oversize'):
            cancel=threading.Event();self.worker.start(cancel);old=self.worker.proc
            timer=threading.Timer(.1,cancel.set)
            if mode=='cancel':timer.start()
            try:
                with self.assertRaises(VoiceError):
                    self.worker.request({'oversize':True} if mode=='oversize' else {'slow':True},cancel,.2)
            finally:
                if mode=='cancel':timer.cancel()
            self.assertIsNotNone(old.poll());self.assertIsNone(self.worker.proc)


class PipelineTests(unittest.TestCase):
    def test_generation_synthesis_playback_overlap_and_cleanup(self):
        b=ResponsiveBackend(Settings(Path('/unused')))
        playing=threading.Event();second=threading.Event();calls=[]
        def phrases(text,cancel):
            yield 'First.'
            self.assertTrue(playing.wait(2))
            yield 'Second.'
        b.server.phrases=phrases
        def synth(text,path,cancel):
            write_wav(path);calls.append(text)
            if text=='Second.':second.set()
        b.synthesize=synth
        def play(path,cancel):
            playing.set();self.assertTrue(second.wait(2))
        b.play=play
        before=set(Path('/dev/shm').glob('local-voice-*'))
        result=b.respond('Hello',threading.Event())
        self.assertEqual(result.answer,'First. Second.')
        self.assertEqual(calls,['First.','Second.'])
        self.assertIn('first_playback_request',result.seconds)
        self.assertEqual(before,set(Path('/dev/shm').glob('local-voice-*')))

    def test_synthesis_failure_sanitized_and_cleans_up(self):
        b=ResponsiveBackend(Settings(Path('/unused')))
        def phrases(*_):yield 'First.'
        b.server.phrases=phrases
        def fail(*_):raise RuntimeError('PRIVATE')
        b.synthesize=fail
        cancel=threading.Event()
        before=set(Path('/dev/shm').glob('local-voice-*'))
        with self.assertRaises(VoiceError) as caught:b.respond('Hello',cancel)
        self.assertNotIn('PRIVATE',str(caught.exception));self.assertFalse(cancel.is_set())
        self.assertEqual(before,set(Path('/dev/shm').glob('local-voice-*')))

    def test_final_audio_with_trailing_correction_is_not_cached(self):
        b=FakeBackend()
        with private_workspace() as tmp:
            d=Path(tmp);wav=d/'input.wav';write_wav(wav,frames=16000)
            live=LiveTranscription(b,d,threading.Event())
            live.cached=(b'\x00\x10'*8000,'Do it')
            self.assertEqual(live.finish(wav),'Name a primary color.')
            self.assertEqual(b.calls,['transcribe'])
            live.close()

    def test_startup_ignores_recording_presses(self):
        b=FakeBackend();gate=threading.Event()
        b.prepare=lambda cancel:gate.wait(2)
        c=Controller(b)
        try:
            c.initialize();self.assertEqual(c.state,'starting')
            c.press();self.assertEqual(c.state,'starting')
            gate.set();c.worker.join(2);self.assertEqual(c.state,'ready')
        finally:gate.set();c.close()



class ResponsiveControllerTests(unittest.TestCase):
    def test_metrics_and_provisional_input_cleanup(self):
        from local_voice.core import Result
        b=FakeBackend()
        b.prepare=lambda cancel:None
        def respond(text,cancel,state):
            state('speaking')
            return Result(text,'Answer.',{'first_phrase':.01,'first_playback_request':.02,'playback_complete':.03})
        b.respond=respond
        def recorder(settings,wav,finish,cancel,observer=None):
            while not finish.wait(.01):
                if cancel.is_set():raise Cancelled('Operation cancelled.')
            write_wav(wav)
        metrics=[];c=Controller(b,recorder=recorder,metrics=metrics.append)
        try:
            c.initialize();c.worker.join(2)
            c.press()
            end=time.monotonic()+2
            while c.state=='starting' and time.monotonic()<end:time.sleep(.01)
            c.press();c.worker.join(3)
            self.assertEqual(c.state,'ready');self.assertEqual(len(metrics),1)
            self.assertIn('finish_to_playback_request',metrics[0])
            self.assertNotIn('Answer.',json.dumps(metrics))
        finally:c.close()

    def test_startup_cancel_has_retryable_state(self):
        b=FakeBackend()
        def prepare(cancel):
            cancel.wait(2)
            if cancel.is_set():raise Cancelled('Operation cancelled.')
        b.prepare=prepare;c=Controller(b)
        try:
            c.initialize();c.cancel();c.worker.join(3)
            self.assertEqual(c.state,'error')
        finally:c.close()
