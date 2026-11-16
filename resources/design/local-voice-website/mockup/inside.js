const examples = {
 france:{question:'What is the capital of France?',answer:'The capital of France is Paris.'},
 plants:{question:'Why do plants need sunlight?',answer:'Plants use sunlight to make food through photosynthesis.'},
 walk:{question:'What should I bring for a short walk?',answer:'Bring water and comfortable shoes.'}
};
const stages = [
 {kicker:'01 / A question, out loud',title:'It starts with <em>you.</em>',description:'Speak to the prototype. The microphone records your voice as audio, ready for local recognition.',detail:'The same device will speak the reply. The enlarged cutaway shows the software running inside its Jetson.',tech:'Microphone → mono 16 kHz PCM audio. Recording is bounded to 30 seconds. Audio is temporary; there is no cloud speech service.',handoff:'Your voice → recorded sound',position:.12},
 {kicker:'02 / Whisper tiny.en',title:'Sound becomes <em>words.</em>',description:'Whisper turns a sound pattern into a transcript. The colored grid is a spectrogram: a picture of how frequencies change over time.',detail:'Audio features pass through the recognition model to produce text. Whisper transcribes the question; it does not answer it.',tech:'Whisper tiny.en · F16 · whisper.cpp · CUDA profile. Log-Mel audio features feed the model. The picture is schematic, not a measured recording.',handoff:'Audio → spectrogram → transcript',position:.35},
 {kicker:'03 / Gemma 4 E2B',title:'Gemma builds <em>an answer.</em>',description:'The transcript and a short instruction enter Gemma. Its learned weights turn that context into an answer, one token at a time.',detail:'The purple sheets represent model processing, not separate chips. This path uses text input, with no web search or conversation history.',tech:'Gemma 4 E2B instruction model · Q4_K_M · llama.cpp · CUDA profile. 2,048-token context; 128-token default answer cap. Thinking output disabled.',handoff:'Transcript + instruction → answer tokens',position:.60},
 {kicker:'04 / Piper neural speech',title:'Piper creates <em>speech.</em>',description:'Piper converts the completed answer into pronunciation units, then its neural voice model generates a speech waveform.',detail:'The coral network represents the voice model. It creates the sound of the reply; it does not decide what the answer should say.',tech:'Piper 1.8.0 · en_US-ljspeech-medium · ONNX voice on CPU · 22,050 Hz output. Piper embeds eSpeak for phonemization, then uses its neural model to synthesize audio.',handoff:'Answer → pronunciation units → waveform',position:.85},
 {kicker:'05 / Back into the room',title:'One device. <em>A round trip.</em>',description:'The reply returns through the same device’s speaker. Sound became text, Gemma generated an answer, and Piper turned it back into sound.',detail:'These are authored examples, not live model responses. The artwork, token pieces, and animation timing explain the process; they are not measurements.',tech:'Synthesized WAV → ALSA playback → USB speaker. One question at a time. No retrieval or cloud fallback. Physical acceptance of the selected upgrade is tracked separately.',handoff:'Synthesized audio → speaker → you',position:.12}
];
const mobileDescriptions=[
 'You speak to Local Voice. Its microphone captures audio for recognition.',
 'Whisper reads a spectrogram—a picture of sound frequencies over time—and produces written words.',
 'Gemma uses the transcript and an instruction to generate an answer, one token at a time.',
 'Pronunciation units enter Piper’s voice model. A speech waveform comes out.',
 'The same device speaks the reply: sound became text, then text became sound.'
];
const mobileTech=['16 kHz mono PCM · 30-second recording cap · temporary audio.','Whisper tiny.en F16 · whisper.cpp · CUDA profile · log-Mel audio features.','Gemma 4 E2B Q4_K_M · llama.cpp · CUDA profile · 2,048 context tokens · 128-token default answer cap.','Piper 1.8.0 · LJ Speech medium ONNX voice · CPU · 22,050 Hz speech.','WAV → ALSA → USB speaker. Local single-turn flow; upgrade acceptance is tracked separately.'];
const mobileDetails=[
 'The cutaway shows software inside one Jetson. The same device will speak the reply.',
 'Whisper transcribes the question. It does not answer it.',
 'Learned weights produce tokens. No web lookup; answers can still be wrong.',
 'Selected voice: LJ Speech medium. Neural synthesis runs locally on CPU.',
 'Authored example, not live inference. Animation timing is not device latency.'
];
const story=document.querySelector('.inside-story'),pin=document.querySelector('.inside-pin'),workshop=document.querySelector('.workshop'),viewport=document.querySelector('.workshop-viewport');
const nodes=[...document.querySelectorAll('[data-flow]')],steps=[...document.querySelectorAll('[data-step]')];
const dot=document.querySelector('.signal-dot'),route=document.querySelector('.return-route'),scrub=document.getElementById('journey-scrub'),playButton=document.getElementById('animate-turn'),lensButton=document.getElementById('detail-lens');
const narrow=matchMedia('(max-width:600px)'),reduced=matchMedia('(prefers-reduced-motion:reduce)'),compact=matchMedia('(max-height:610px)');
let active=-1,top=0,travel=1,renderFrame=0,playFrame=0,progress=0,playing=false,detailMode=false,selected='france',playStart=0,playOrigin=0;
let tokens=[];
function populate(){
 const example=examples[selected];
 document.getElementById('question-example').textContent=example.question;
 document.getElementById('speech-example').textContent=example.answer;
 document.getElementById('reply-example').textContent=example.answer;
 const answer=document.getElementById('answer-example');answer.replaceChildren();
 for(const word of example.answer.split(' ')){const piece=document.createElement('span');piece.textContent=word;answer.append(piece,document.createTextNode(" "));}
 tokens=[...answer.children];
}
function pan(index){if(workshop.offsetWidth>viewport.clientWidth)viewport.scrollTo({left:Math.max(0,workshop.offsetWidth*stages[index].position-viewport.clientWidth/2+18),behavior:reduced.matches?'instant':'smooth'});}
function show(index,refresh=false){
 if(index===active&&!refresh)return;
 const changed=index!==active;active=index;const stage=stages[index];
 document.getElementById('flow-kicker').textContent=stage.kicker;
 document.getElementById('flow-title').innerHTML=stage.title;
 document.getElementById('flow-description').textContent=narrow.matches?mobileDescriptions[index]:stage.description;
 document.getElementById('flow-handoff').textContent=stage.handoff;
 document.getElementById('flow-detail').textContent=detailMode?(narrow.matches?mobileTech[index]:stage.tech):(narrow.matches?mobileDetails[index]:stage.detail);
 document.getElementById('flow-count').textContent=`0${index+1} / 05`;
 workshop.dataset.scene=String(index);
 nodes.forEach((node,i)=>{if(i===(index===4?0:index))node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
 steps.forEach((node,i)=>{if(i===index)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
 document.querySelectorAll('.question-bubble,.transcript-slip,.answer-tokens,.speech-strip,.reply-bubble').forEach((el,i)=>el.setAttribute('aria-hidden',String(i!==index)));
 if(changed)pan(index);
}
function paint(value){
 progress=Math.max(0,Math.min(1,value));const index=Math.min(4,Math.floor(progress*5)),phase=Math.min(1,progress*5-index);show(index);
 scrub.value=String(Math.round(progress*1000));scrub.setAttribute('aria-valuetext',`${index+1} of 5: ${stages[index].kicker.split(' / ')[1]}`);
 const words=examples[selected].question.split(' ');
 document.getElementById('transcript-example').textContent=words.slice(0,Math.max(1,Math.ceil(phase*words.length))).join(' ');
 tokens.forEach((token,i)=>token.classList.toggle('is-written',i<Math.max(1,Math.ceil(phase*tokens.length))));
 workshop.style.setProperty('--phase',phase.toFixed(3));
 document.querySelectorAll('.gemma-activation i').forEach((el,i)=>el.style.opacity=String(index===2&&Math.floor(phase*12)%4===i?.9:.12));
 document.querySelectorAll('.piper-wave i').forEach((el,i)=>el.style.height=`${8+Math.abs(Math.sin(i*.8+phase*9))*43*(.25+Math.sin(i/16*Math.PI))}%`);
 const point=index===4?route.getPointAtLength(route.getTotalLength()*phase):{x:220+Math.min(1,progress*5/4)*860,y:240};
 dot.setAttribute('cx',point.x.toFixed(2));dot.setAttribute('cy',point.y.toFixed(2));dot.style.opacity=reduced.matches?'0':'1';
}
function stop(){playing=false;cancelAnimationFrame(playFrame);playFrame=0;playButton.textContent='▶ Animate a turn';playButton.setAttribute('aria-pressed','false');}
function syncScroll(){if(!compact.matches)window.scrollTo({top:top+travel*progress,behavior:'instant'});}
function seek(value){stop();paint(value);syncScroll();}
function render(){renderFrame=0;if(!compact.matches&&!playing)paint((scrollY-top)/travel);}
function request(){if(!renderFrame&&!playing)renderFrame=requestAnimationFrame(render);}
function measure(){top=story.getBoundingClientRect().top+scrollY;travel=Math.max(1,story.offsetHeight-pin.offsetHeight);request();if(active>=0){show(active,true);pan(active);}}
function tick(now){if(!playing)return;paint(playOrigin+(now-playStart)/20000);syncScroll();if(progress>=1){stop();return;}playFrame=requestAnimationFrame(tick);}
playButton.addEventListener('click',()=>{
 if(playing){stop();return;}
 if(progress>=.98)paint(0);
 playOrigin=progress;playStart=performance.now();playing=true;playButton.textContent='Ⅱ Pause animation';playButton.setAttribute('aria-pressed','true');playFrame=requestAnimationFrame(tick);
});
lensButton.addEventListener('click',()=>{detailMode=!detailMode;lensButton.setAttribute('aria-pressed',String(detailMode));lensButton.textContent=detailMode?'Close the details −':'Under the hood +';story.classList.toggle('show-model-details',detailMode);show(active,true);});
scrub.addEventListener('input',()=>seek(Number(scrub.value)/1000));
document.getElementById('example-question').addEventListener('change',event=>{selected=event.target.value;populate();seek(0);});
nodes.forEach((node,i)=>node.addEventListener('click',()=>seek((i+.94)/5)));steps.forEach((node,i)=>node.addEventListener('click',()=>seek((i+.94)/5)));
window.addEventListener('scroll',request,{passive:true});window.addEventListener('resize',measure,{passive:true});window.addEventListener('pageshow',measure);
window.addEventListener('wheel',()=>{if(playing)stop();},{passive:true});window.addEventListener('touchstart',()=>{if(playing)stop();},{passive:true});
window.addEventListener('keydown',event=>{if(['Escape','PageUp','PageDown','Home','End','ArrowUp','ArrowDown',' '].includes(event.key)&&playing)stop();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});compact.addEventListener('change',()=>{stop();measure();});reduced.addEventListener('change',()=>{stop();paint(progress);});new ResizeObserver(measure).observe(pin);
document.fonts.ready.then(measure);populate();paint(0);measure();
