const stages = [
  {kicker:'01 / Capture', title:'Your voice.<br> <em>Your cue.</em>', description:'The AtomS3-Lite sends a button press over USB. The Python controller starts the microphone; a second press ends the recording. Listening stops automatically at 30 seconds.',spec:'ALSA · mono 16 kHz audio · temporary WAV',example:'“What is the capital of France?”',handoff:'Sound → recorded audio',state:'Recording',color:'#e49779'},
  {kicker:'02 / Transcribe',title:'From sound<br> to <em>words.</em>',description:'Whisper tiny.en reads the recorded audio and produces an English transcript. whisper.cpp runs recognition locally, using the Jetson GPU in the CUDA profile. It passes text—not audio—to the answer model.',spec:'Whisper tiny.en · F16 · whisper.cpp · CUDA',example:'What is the capital of France?',handoff:'Recorded audio → transcript',state:'Transcribing',color:'#d0af79'},
  {kicker:'03 / Answer',title:'Words become<br> an <em>answer.</em>',description:'Qwen2.5 1.5B Instruct receives the transcript and a fixed prompt asking for a brief English response. llama.cpp runs the model with all 29 layers on the GPU. Each question begins a fresh turn, without history or retrieval.',spec:'Q4_K_M · 2,048-token context · 128-token default output',example:'“The capital of France is Paris.”',handoff:'Transcript + system prompt → completed answer',state:'Answering',color:'#d0af79'},
  {kicker:'04 / Synthesize',title:'An answer<br> finds <em>its voice.</em>',description:'eSpeak NG turns the completed answer into a temporary speech file on the CPU. This is a functional English voice baseline; its mechanical sound is a known limitation, and voice naturalness remains to be evaluated.',spec:'eSpeak NG · en-us · 165 words per minute · CPU',example:'Text becomes a speech waveform.',handoff:'Completed answer → synthesized audio',state:'Synthesizing',color:'#d0af79'},
  {kicker:'05 / Speak',title:'Back into<br> <em>the room.</em>',description:'ALSA plays the synthesized speech through the USB speaker automatically. The light turns cyan while speaking. A button press can cancel playback; after completion, temporary files are cleaned up and the controller returns to ready.',spec:'ALSA playback · USB speaker · automatic spoken reply',example:'One turn ends. The next starts fresh.',handoff:'Synthesized audio → speaker → ready',state:'Speaking',color:'#83c7c4'}
];
const story=document.querySelector('.inside-story');
const pin=document.querySelector('.inside-pin');
const nodes=[...document.querySelectorAll('[data-flow]')];
const steps=[...document.querySelectorAll('[data-step]')];
const lines=[...document.querySelectorAll('.signal-line')];
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const compact=matchMedia('(max-height: 600px)');
let active=-1, top=0, travel=1, frame=0;
function show(index){
 if(index===active)return;active=index;const stage=stages[index];
 for(const key of ['kicker','description','spec','example','handoff']) document.getElementById(`flow-${key}`).textContent=stage[key];
 document.getElementById('flow-title').innerHTML=stage.title;
 document.getElementById('controller-state').textContent=stage.state;
 document.getElementById('state-light').style.background=stage.color;
 document.getElementById('flow-count').textContent=`0${index+1} / 05`;
 for(const [i,node]of nodes.entries()){
  node.classList.toggle('is-lit',i===index);node.classList.toggle('is-passed',i<index);
  if(i===index)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');
 }
 steps.forEach((node,i)=>{if(i===index)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
 lines.forEach((line,i)=>line.classList.toggle('is-passed',i<index));
}
function render(){frame=0;if(compact.matches)return;const progress=Math.max(0,Math.min(1,(scrollY-top)/travel));show(Math.min(4,Math.floor(progress*5)));}
function request(){if(!frame)frame=requestAnimationFrame(render);}
function measure(){top=story.getBoundingClientRect().top+scrollY;travel=Math.max(1,story.offsetHeight-pin.offsetHeight);request();}
function select(i){show(i);if(!compact.matches)window.scrollTo({top:top+travel*(i+.35)/5,behavior:'instant'});}
nodes.forEach((node,i)=>node.addEventListener('click',()=>select(i)));
steps.forEach((node,i)=>node.addEventListener('click',()=>select(i)));
window.addEventListener('scroll',request,{passive:true});window.addEventListener('resize',measure,{passive:true});window.addEventListener('pageshow',measure);compact.addEventListener('change',measure);reduced.addEventListener('change',request);new ResizeObserver(measure).observe(pin);document.fonts.ready.then(measure);show(0);measure();
