const stages = [
 {kicker:'01 / A question, out loud',title:'It starts with <em>you.</em>',description:'“What is the capital of France?” You speak to Local Voice. Its microphone captures the sound of your question.',handoff:'Your voice → recorded sound',detail:'The device receives audio, not written words. The next job is to work out what was said.',position:.12},
 {kicker:'02 / Speech recognition',title:'Whisper finds <em>the words.</em>',description:'Whisper reads the patterns in the recorded sound and turns them into a transcript: “What is the capital of France?”',handoff:'Recorded sound → “What is the capital of France?”',detail:'This is transcription. Whisper writes down the question; it does not answer it. The tape-and-typewriter is our illustration of that transformation.',position:.37},
 {kicker:'03 / Local inference',title:'A little text, <em>piece by piece.</em>',description:'The language model takes the transcript and a short instruction. Using patterns learned during training, it generates an answer one token at a time.',handoff:'Question + instruction → a completed answer',detail:'Qwen runs locally through llama.cpp. There is no web lookup. The tiles simplify tokens, which can be words or word-pieces; a generated answer can still be wrong.',position:.62},
 {kicker:'04 / Speech synthesis',title:'Give those words <em>a voice.</em>',description:'“The capital of France is Paris.” The completed answer goes into eSpeak NG, which converts written text into the sounds of speech.',handoff:'Completed answer → synthesized audio',detail:'Speech synthesis is a separate job from answering. In this baseline, eSpeak runs on the CPU; Whisper and Qwen use the Jetson’s GPU.',position:.87},
 {kicker:'05 / Back into the room',title:'And it comes <em>back to you.</em>',description:'The very same Local Voice device plays the answer through its speaker. A spoken question has made a round trip—from sound to text, and back to sound.',handoff:'Synthesized audio → speaker → you',detail:'All three software stages run on the Jetson after setup. The workshop is a visual metaphor, and this is an illustrative turn—not a live recording or live model response.',position:.12}
];
const narrowText = [
 ['You ask, “What is the capital of France?” The device records your voice.','Sound comes in. Next, Whisper works out what was said.'],
 ['Whisper turns your recorded speech into written words: “What is the capital of France?”','Whisper transcribes the question; it does not answer it.'],
 ['Qwen uses the transcript and a short instruction to generate an answer, one token at a time.','Local generation, no web lookup. Tokens may be words or word-pieces. Answers can be wrong.'],
 ['eSpeak NG converts “The capital of France is Paris” into speech audio.','The answer is completed before it is spoken. Synthesis runs on CPU.'],
 ['The same device speaks the answer back. Your question has gone from sound to text, and back to sound.','One local round trip. This is an illustration, not a live recording or model response.']
];
const narrow=matchMedia('(max-width: 600px)');
const story=document.querySelector('.inside-story'),pin=document.querySelector('.inside-pin'),workshop=document.querySelector('.workshop'),viewport=document.querySelector('.workshop-viewport');
const nodes=[...document.querySelectorAll('[data-flow]')],steps=[...document.querySelectorAll('[data-step]')],tokens=[...document.querySelectorAll('.answer-tokens span')];
const dot=document.querySelector('.signal-dot'),route=document.querySelector('.return-route');
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),compact=matchMedia('(max-height: 610px)');
let active=-1,top=0,travel=1,frame=0;
function pan(index){if(workshop.offsetWidth>viewport.clientWidth)viewport.scrollTo({left:Math.max(0,workshop.offsetWidth*stages[index].position-viewport.clientWidth/2+18),behavior:reduced.matches?'instant':'smooth'});}
function show(index,refresh=false){
 if(index===active&&!refresh)return;active=index;const stage=stages[index];
 for(const key of ['kicker','description','handoff','detail'])document.getElementById(`flow-${key}`).textContent=stage[key];
 if(narrow.matches){document.getElementById('flow-description').textContent=narrowText[index][0];document.getElementById('flow-detail').textContent=narrowText[index][1];}
 document.getElementById('flow-title').innerHTML=stage.title;document.getElementById('flow-count').textContent=`0${index+1} / 05`;workshop.dataset.scene=String(index);
 nodes.forEach((node,i)=>{if(i===(index===4?0:index))node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
 steps.forEach((node,i)=>{if(i===index)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
 document.querySelectorAll('.question-bubble,.transcript-slip,.answer-tokens,.speech-strip,.reply-bubble').forEach((el,i)=>el.setAttribute('aria-hidden',String(i!==index)));
 pan(index);
}
function paint(progress){
 const index=Math.min(4,Math.floor(progress*5)),phase=Math.min(1,progress*5-index);show(index);
 tokens.forEach((token,i)=>token.classList.toggle('is-written',i<Math.max(1,Math.ceil(phase*5))));
 let point;
 if(index===4)point=route.getPointAtLength(route.getTotalLength()*phase);
 else point={x:220+Math.min(1,(progress*5)/4)*860,y:240};
 dot.setAttribute('cx',point.x.toFixed(2));dot.setAttribute('cy',point.y.toFixed(2));
 dot.style.opacity=reduced.matches?'0':'1';
}
function render(){frame=0;if(compact.matches)return;paint(Math.max(0,Math.min(1,(scrollY-top)/travel)));}
function request(){if(!frame)frame=requestAnimationFrame(render);}
function measure(){top=story.getBoundingClientRect().top+scrollY;travel=Math.max(1,story.offsetHeight-pin.offsetHeight);request();if(active>=0)show(active,true);}
function select(i){const progress=(i+.96)/5;paint(progress);if(!compact.matches)window.scrollTo({top:top+travel*progress,behavior:'instant'});}
nodes.forEach((node,i)=>node.addEventListener('click',()=>select(i)));steps.forEach((node,i)=>node.addEventListener('click',()=>select(i)));
window.addEventListener('scroll',request,{passive:true});window.addEventListener('resize',measure,{passive:true});window.addEventListener('pageshow',measure);compact.addEventListener('change',measure);reduced.addEventListener('change',request);new ResizeObserver(measure).observe(pin);document.fonts.ready.then(measure);show(0);measure();
