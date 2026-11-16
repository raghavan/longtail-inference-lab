#!/usr/bin/env python3
"""Real-model cancellation checks and authored capture replay; offline inference only."""
import argparse,audioop,json,shutil,subprocess,sys,threading,time,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from local_voice.core import Settings,Cancelled,private_workspace,check_cancel
from local_voice.responsive import ResponsiveBackend
from local_voice.device import Controller
parser=argparse.ArgumentParser(description='Authored worker cancellation, capture replay and physical output check; never opens the microphone.')
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--playback-device',default='null')
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if args.output.exists():parser.error('output exists')
b=ResponsiveBackend(Settings(args.root.expanduser().resolve(),backend='cuda',playback_device=args.playback_device))
c=None
report={'scope':'Authored physical playback and owned-worker failure checks; no live microphone recording','checks':[]}
try:
 b.prepare(threading.Event())
 with private_workspace() as tmp:
  d=Path(tmp);fixture=d/'fixture.wav'
  subprocess.run([shutil.which('espeak-ng'),'-s','145','-w',str(fixture),'What is the capital of France?'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  with wave.open(str(fixture),'rb') as w:pcm=w.readframes(w.getnframes());rate=w.getframerate()
  pcm,_=audioop.ratecv(pcm,2,1,rate,16000,None)
  with wave.open(str(fixture),'wb') as w:w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(pcm)
  before=set(Path('/dev/shm').glob('local-voice-*'))
  for role in ('asr','tts'):
   cancel=threading.Event();worker=getattr(b,role);owned=worker.proc
   timer=threading.Timer(.02,cancel.set);timer.start();t=time.monotonic()
   try:
    if role=='asr':b.transcribe(fixture,d,cancel)
    else:b.synthesize('This is a bounded authored cancellation test. '*30,d/'cancel.wav',cancel)
    raise AssertionError('cancellation not observed')
   except Cancelled:
    assert owned.poll() is not None and worker.proc is None
    report['checks'].append({'check':role+'_cancellation','passed':True,'seconds':round(time.monotonic()-t,3)})
   finally:timer.cancel()
   (d/'cancel.wav').unlink(missing_ok=True)
   b.prepare(threading.Event())
  cancel=threading.Event();owned=b.server.proc
  timer=threading.Timer(.1,cancel.set);timer.start();t=time.monotonic()
  try:
   list(b.server.phrases('Explain photosynthesis in two sentences.',cancel));raise AssertionError('cancellation not observed')
  except Cancelled:
   assert owned.poll() is not None and b.server.proc is None
   report['checks'].append({'check':'generation_cancellation','passed':True,'seconds':round(time.monotonic()-t,3)})
  finally:timer.cancel()
  b.prepare(threading.Event())
  # Exercise recording observer + real resident ASR + full streaming speaker path.
  def recorder(settings,path,finished,cancel,observer=None):
   raw=path.with_suffix('.pcm')
   try:
    with raw.open('wb') as f:
     for off in range(0,len(pcm),3200):
      check_cancel(cancel);f.write(pcm[off:off+3200]);f.flush()
      if observer:observer(raw)
      cancel.wait(.1)
    c.press()  # equivalent to the second physical button event
    with wave.open(str(path),'wb') as w:w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(pcm)
   finally:raw.unlink(missing_ok=True)
  stats=[];states=[];c=Controller(b,states.append,recorder,stats.append)
  for n in range(2):
   c.press();c.worker.join(60)
   assert not c.worker.is_alive() and c.state=='ready',(c.state,c.error)
  report['checks'].append({'check':'authored_capture_stream_physical_playback','passed':True,'turns':stats,'states':states})
  # Cancel actual ALSA playback and recover without leaving transient files.
  cancel=threading.Event();fired=[]
  def state(name):
   if name=='speaking':
    timer=threading.Timer(.15,cancel.set);fired.append(timer);timer.start()
  try:
   b.respond('Explain why plants need sunlight in two sentences.',cancel,state);raise AssertionError('playback did not cancel')
  except Cancelled:report['checks'].append({'check':'physical_playback_cancellation','passed':True})
  finally:
   for timer in fired:timer.cancel()
  b.prepare(threading.Event())
  assert set(Path('/dev/shm').glob('local-voice-*'))==before
  report['checks'].append({'check':'transient_workspace_cleanup','passed':True})
 print(json.dumps(report,indent=2),flush=True)
 with args.output.open('x') as output:output.write(json.dumps(report,indent=2)+'\n')
finally:
 if c is not None:c.close()
 else:b.close()
