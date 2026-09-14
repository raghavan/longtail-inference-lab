import { END, STAGES, PARTS, clamp, smoothstep, poseAt } from './choreography.mjs?v=3';

const story = document.querySelector('.assembly-story');
const pin = document.querySelector('.pin');
const chapters = [...document.querySelectorAll('[data-chapter]')];
const navigation = [...document.querySelectorAll('[data-go]')];
const partElements = Object.fromEntries(Object.keys(PARTS).map(name => [name, document.getElementById(`part-${name}`)]));
const number = document.getElementById('chapter-number');
const figure = document.getElementById('figure-number');
const partName = document.getElementById('part-name');
const caption = document.getElementById('figure-caption');
const instruction = document.getElementById('scroll-instruction');
const callout = document.getElementById('callout');
const calloutLine = document.getElementById('callout-line');
const calloutDot = document.getElementById('callout-dot');
const calloutLabel = document.getElementById('callout-label');
const wiring = document.getElementById('wiring');
const enclosurePower = document.getElementById('enclosure-power');
const shadow = document.getElementById('scene-shadow');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let storyTop = 0;
let travel = 1;
let displayed = 0;
let target = 0;
let active = -1;
let frame = 0;

function measure() {
  storyTop = story.getBoundingClientRect().top + window.scrollY;
  travel = Math.max(1, story.offsetHeight - pin.offsetHeight);
  requestRender();
}

function setChapter(index) {
  if (index === active) return;
  active = index;
  const stage = STAGES[index];
  chapters.forEach((chapter, i) => {
    const visible = i === index;
    chapter.classList.toggle('is-active', visible);
    chapter.inert = !visible;
    if (visible) chapter.removeAttribute('aria-hidden');
    else chapter.setAttribute('aria-hidden', 'true');
  });
  navigation.forEach((button, i) => {
    if (i === index) button.setAttribute('aria-current', 'step');
    else button.removeAttribute('aria-current');
  });
  number.textContent = String(index + 1).padStart(2, '0');
  figure.textContent = `FIG. ${String(index + 1).padStart(2, '0')}`;
  partName.textContent = ['Jetson Orin Nano Super', '128 GB microSD', 'Mini USB microphone', 'Tiny USB speaker', 'AtomS3-Lite', 'Mains power', 'Local Voice / Form study'][index];
  caption.textContent = stage.caption;
  instruction.textContent = index === 6 ? 'Scroll for the build notes' : 'Scroll to assemble';
  calloutLine.setAttribute('d', `M${stage.point.join(' ')} ${stage.elbow.join(' ')}H${stage.label[0]}`);
  calloutDot.setAttribute('cx', stage.point[0]);
  calloutDot.setAttribute('cy', stage.point[1]);
  calloutLabel.setAttribute('x', stage.label[0]);
  calloutLabel.setAttribute('y', stage.label[1]);
  calloutLabel.setAttribute('text-anchor', stage.align || 'end');
  calloutLabel.textContent = stage.callout;
}

function paint(t) {
  const chapter = Math.min(6, Math.floor(t + .5));
  setChapter(chapter);
  // The two USB audio illustrations share their footprint and on-screen scale.
  const audioScale = poseAt(PARTS.microphone, t)[2];
  for (const [name, keys] of Object.entries(PARTS)) {
    const [x, y, partScale, rotation, opacity] = poseAt(keys, t);
    const scale = name === 'speaker' ? audioScale : partScale;
    const element = partElements[name];
    element.setAttribute('transform', `translate(${x.toFixed(2)} ${y.toFixed(2)}) rotate(${rotation.toFixed(2)}) scale(${scale.toFixed(4)})`);
    element.setAttribute('opacity', opacity.toFixed(3));
  }
  // Leaders disappear between chapters rather than chasing a moving part.
  const distance = chapter === 6 ? Math.max(0, 6 - t) : Math.abs(t - chapter);
  callout.setAttribute('opacity', reducedMotion.matches ? '1' : (1 - smoothstep(.15, .48, distance)).toFixed(3));
  wiring.style.opacity = (smoothstep(4.65, 5.05, t) * (1 - smoothstep(5.35, 5.85, t))).toFixed(3);
  enclosurePower.setAttribute('opacity', smoothstep(5.85, 6.2, t).toFixed(3));
  shadow.setAttribute('opacity', (.6 + .4 * smoothstep(4, 6, t)).toFixed(3));
  shadow.setAttribute('cy', (489 + 26 * smoothstep(5.4, 6.2, t)).toFixed(2));
  shadow.setAttribute('rx', (290 - 70 * smoothstep(5.4, 6.2, t)).toFixed(2));
  shadow.setAttribute('ry', (107 - 40 * smoothstep(5.4, 6.2, t)).toFixed(2));
  navigation.forEach((button, i) => button.style.setProperty('--fill', clamp(t - i + .12).toFixed(3)));
}

function render() {
  frame = 0;
  target = clamp((window.scrollY - storyTop) / travel) * END;
  if (reducedMotion.matches) {
    // Still frames preserve the story without spatial movement.
    displayed = target >= 5.5 ? END : Math.round(target);
  } else {
    // A short catch-up softens trackpad events; scrolling remains entirely native.
    displayed += (target - displayed) * .24;
    if (Math.abs(target - displayed) < .001) displayed = target;
  }
  paint(displayed);
  if (!reducedMotion.matches && Math.abs(target - displayed) >= .001) frame = requestAnimationFrame(render);
}

function requestRender() {
  if (!frame) frame = requestAnimationFrame(render);
}

function goTo(chapter) {
  const time = chapter === 6 ? 6.35 : chapter;
  window.scrollTo({ top: storyTop + travel * time / END, behavior: reducedMotion.matches ? 'instant' : 'smooth' });
}

navigation.forEach(button => button.addEventListener('click', () => goTo(Number(button.dataset.go))));
document.getElementById('replay').addEventListener('click', () => {
  goTo(0);
  navigation[0].focus({ preventScroll: true });
});
window.addEventListener('scroll', requestRender, { passive: true });
window.addEventListener('resize', measure, { passive: true });
window.addEventListener('pageshow', measure);
reducedMotion.addEventListener('change', () => { displayed = target; measure(); });
new ResizeObserver(measure).observe(pin);
document.fonts.ready.then(measure);
measure();
displayed = clamp((window.scrollY - storyTop) / travel) * END;
paint(reducedMotion.matches ? (displayed >= 5.5 ? END : Math.round(displayed)) : displayed);
