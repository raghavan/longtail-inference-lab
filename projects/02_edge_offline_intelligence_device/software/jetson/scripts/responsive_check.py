#!/usr/bin/env python3
"""Authored same-device comparison; no microphone input or private speech retained."""
import argparse
import audioop
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_voice.core import LocalBackend, Settings, private_workspace, run_turn
from local_voice.responsive import ResponsiveBackend

CASES = ['What is the capital of France?', 'Why do plants need sunlight?',
         'Name two things to pack for a short walk.']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--playback-device',default='null')
    p.add_argument('--responsive-only',action='store_true')
    p.add_argument('--no-prefix-cache',action='store_true',help='Reproduce the resident-only intermediate condition')
    a=p.parse_args()
    if not 1 <= a.repeats <= 10:p.error('repeats must be 1..10')
    if a.output.exists():p.error('output already exists')
    s=Settings(a.root.expanduser().resolve(),backend='cuda',playback_device=a.playback_device)
    report={'scope':'Authored WAV to software playback request; no microphone or acoustic-onset measurement',
            'order':['resident_streaming'] if a.responsive_only else ['previous_sequential','resident_streaming'],
            'responsive_prompt_cache':not a.no_prefix_cache,
            'threads':s.threads,'context_tokens':2048,'output_token_limit':s.max_tokens,
            'temperature':0,'seed':42,'conversation_history':False,
            'repeats':a.repeats,'playback':'null' if a.playback_device=='null' else 'physical',
            'recognition_change':'Resident context, no timestamp tokens; beam size 5 and English retained',
            'system_prompt_sha256':hashlib.sha256(s.system_prompt.encode()).hexdigest(),
            'lock':json.loads((Path(__file__).resolve().parents[1]/'runtime-lock.json').read_text()),
            'fixtures':[], 'runs':[]}
    with private_workspace() as tmp:
        d=Path(tmp)
        for i,text in enumerate(CASES):
            path=d/('fixture%d.wav'%i)
            subprocess.run([shutil.which('espeak-ng'),'-s','145','-w',str(path),text],check=True,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            with wave.open(str(path),'rb') as w:pcm=w.readframes(w.getnframes());rate=w.getframerate()
            pcm,_=audioop.ratecv(pcm,2,1,rate,16000,None)
            with wave.open(str(path),'wb') as w:w.setparams((1,2,16000,0,'NONE','not compressed'));w.writeframes(pcm)
            report['fixtures'].append({'text':text,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                       'seconds':len(pcm)/32000})
        for profile in report['order']:
            b=ResponsiveBackend(s) if profile=='resident_streaming' else LocalBackend(s)
            cancel=threading.Event()
            if isinstance(b,ResponsiveBackend):b.server.cache_prompt=not a.no_prefix_cache
            try:
                t=time.monotonic()
                if isinstance(b,ResponsiveBackend):b.prepare(cancel)
                else:b.server.answer('Reply with the single word Ready.',cancel)
                report['runs'].append({'profile':profile,'startup_seconds':round(time.monotonic()-t,3)})
                for repetition in range(a.repeats):
                    for i,text in enumerate(CASES):
                        wav=d/('fixture%d.wav'%i); timings={}
                        start=time.monotonic()
                        def state(name):
                            if name=='speaking':timings.setdefault('first_playback_request',round(time.monotonic()-start,3))
                        if isinstance(b,ResponsiveBackend):
                            transcript=b.transcribe(wav,d,cancel)
                            timings['transcription']=round(time.monotonic()-start,3)
                            result=b.respond(transcript,cancel,state)
                            timings['answer_to_first_phrase']=result.seconds['first_phrase']
                        else:result=run_turn(b,cancel,audio=wav,play=True,state=state)
                        timings['playback_complete']=round(time.monotonic()-start,3)
                        trial={'profile':profile,'repetition':repetition+1,'case':i+1,
                               'transcript':result.transcript,'answer':result.answer,
                               'timings':timings,'stage_seconds':result.seconds}
                        report['runs'].append(trial)
                        print(json.dumps({'profile':profile,'repetition':repetition+1,'case':i+1,'timings':timings}),flush=True)
            finally:b.close()
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')

if __name__=='__main__':main()
