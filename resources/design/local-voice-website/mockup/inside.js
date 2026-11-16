const example={question:'What is the capital of France?',answer:'The capital of France is Paris.'};
const stages = [
 {kicker:'01 / A question, out loud',title:'It starts with <em>you.</em>',description:'Speak to the prototype. The microphone records your voice as audio, ready for local recognition.',detail:'The same device will speak the reply. The enlarged cutaway shows the software running inside its Jetson.',handoff:'Your voice → recorded sound',position:.12},
 {kicker:'02 / Whisper tiny.en',title:'Sound becomes <em>words.</em>',description:'Whisper turns a sound pattern into a transcript. The colored grid is a spectrogram: a picture of how frequencies change over time.',detail:'Audio features pass through the recognition model to produce text. Whisper transcribes the question; it does not answer it.',handoff:'Audio → spectrogram → transcript',position:.35},
 {kicker:'03 / Gemma 4 E2B',title:'Gemma builds <em>an answer.</em>',description:'The transcript and a short instruction enter Gemma. Its learned weights turn that context into an answer, one token at a time.',detail:'The purple sheets represent model processing, not separate chips. This path uses text input, with no web search or conversation history.',handoff:'Transcript + instruction → answer tokens',position:.60},
 {kicker:'04 / Piper neural speech',title:'Piper creates <em>speech.</em>',description:'Piper converts the completed answer into pronunciation units, then its neural voice model generates a speech waveform.',detail:'The coral network represents the voice model. It creates the sound of the reply; it does not decide what the answer should say.',handoff:'Answer → pronunciation units → waveform',position:.85},
 {kicker:'05 / Back into the room',title:'One device. <em>A round trip.</em>',description:'The reply returns through the same device’s speaker. Sound became text, Gemma generated an answer, and Piper turned it back into sound.',detail:'This is an illustrative example, not a live model response. The artwork, token pieces, and animation timing explain the process; they are not measurements.',handoff:'Synthesized audio → speaker → you',position:.12}
];
const mobileDescriptions=[
 'You speak to Local Voice. Its microphone captures audio for recognition.',
 'Whisper reads a spectrogram—a picture of sound frequencies over time—and produces written words.',
 'Gemma uses the transcript and an instruction to generate an answer, one token at a time.',
 'Pronunciation units enter Piper’s voice model. A speech waveform comes out.',
 'The same device speaks the reply: sound became text, then text became sound.'
];
const mobileDetails=[
 'The cutaway shows software inside one Jetson. The same device will speak the reply.',
 'Whisper transcribes the question. It does not answer it.',
 'Learned weights produce tokens. No web lookup; answers can still be wrong.',
 'Selected voice: LJ Speech medium. Neural synthesis runs locally on CPU.',
 'Authored example, not live inference. Animation timing is not device latency.'
];
const story=document.querySelector('.inside-story'),pin=document.querySelector('.inside-pin'),workshop=document.querySelector('.workshop'),viewport=document.querySelector('.workshop-viewport');
const nodes=[...document.querySelectorAll('[data-flow]')],steps=[...document.querySelectorAll('[data-step]')];
const narrow=matchMedia('(max-width:600px)'),reduced=matchMedia('(prefers-reduced-motion:reduce)'),compact=matchMedia('(max-height:610px)');
let active=-1,top=0,travel=1,renderFrame=0,progress=0;
let tokens=[];
function populate(){
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
 document.getElementById('flow-detail').textContent=narrow.matches?mobileDetails[index]:stage.detail;
 document.getElementById('flow-count').textContent=`0${index+1} / 05`;
 workshop.dataset.scene=String(index);
 nodes.forEach((node,i)=>{if(i===(index===4?0:index))node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
 steps.forEach((node,i)=>{if(i===index)node.setAttribute('aria-current','step');else node.removeAttribute('aria-current');});
 document.querySelectorAll('.question-bubble,.transcript-slip,.answer-tokens,.speech-strip,.reply-bubble').forEach((el,i)=>el.setAttribute('aria-hidden',String(i!==index)));
 if(changed)pan(index);
}
function paint(value){
 progress=Math.max(0,Math.min(1,value));const index=Math.min(4,Math.floor(progress*5)),phase=Math.min(1,progress*5-index);show(index);
 const words=example.question.split(' ');
 document.getElementById('transcript-example').textContent=words.slice(0,Math.max(1,Math.ceil(phase*words.length))).join(' ');
 tokens.forEach((token,i)=>token.classList.toggle('is-written',i<Math.max(1,Math.ceil(phase*tokens.length))));
 workshop.style.setProperty('--phase',phase.toFixed(3));
 document.querySelectorAll('.gemma-activation i').forEach((el,i)=>el.style.opacity=String(index===2&&Math.floor(phase*12)%4===i?.9:.12));
 document.querySelectorAll('.piper-wave i').forEach((el,i)=>el.style.height=`${8+Math.abs(Math.sin(i*.8+phase*9))*43*(.25+Math.sin(i/16*Math.PI))}%`);

}
function seek(value){paint(value);if(!compact.matches)window.scrollTo({top:top+travel*progress,behavior:'instant'});}
function render(){renderFrame=0;if(!compact.matches)paint((scrollY-top)/travel);}
function request(){if(!renderFrame)renderFrame=requestAnimationFrame(render);}
function measure(){top=story.getBoundingClientRect().top+scrollY;travel=Math.max(1,story.offsetHeight-pin.offsetHeight);request();if(active>=0){show(active,true);pan(active);}}
nodes.forEach((node,i)=>node.addEventListener('click',()=>seek((i+.94)/5)));steps.forEach((node,i)=>node.addEventListener('click',()=>seek((i+.94)/5)));
window.addEventListener('scroll',request,{passive:true});window.addEventListener('resize',measure,{passive:true});window.addEventListener('pageshow',measure);
compact.addEventListener('change',measure);reduced.addEventListener('change',()=>paint(progress));new ResizeObserver(measure).observe(pin);
document.fonts.ready.then(measure);populate();paint(0);measure();
