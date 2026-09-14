// Timeline units are chapters. Poses are [x, y, scale, rotation, opacity].
// Coordinates refer to the 820 × 720 scene, keeping the assembly consistent across screens.
export const END = 6.6;
export const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
export function smoothstep(start, end, value) {
  const t = clamp((value - start) / (end - start));
  return t * t * (3 - 2 * t);
}
export function poseAt(keys, time) {
  if (time <= keys[0][0]) return keys[0].slice(1);
  if (time >= keys.at(-1)[0]) return keys.at(-1).slice(1);
  const index = keys.findIndex(key => key[0] > time);
  const from = keys[index - 1];
  const to = keys[index];
  const mix = smoothstep(from[0], to[0], time);
  return from.slice(1).map((value, i) => value + (to[i + 1] - value) * mix);
}

export const STAGES = [
  { caption: 'A small beginning. Everything else follows.', callout: 'THE LOCAL BRAIN', point: [493, 267], elbow: [615, 194], label: [720, 181] },
  { caption: 'The smallest piece carries a world of possibility.', callout: 'ROOM FOR THE MODELS', point: [597, 242], elbow: [653, 168], label: [768, 153] },
  { caption: 'The conversation begins here.', callout: 'A WAY IN', point: [213, 391], elbow: [135, 459], label: [67, 482], align: 'start' },
  { caption: 'From a thought to a voice in the room.', callout: 'AN ANSWER, OUT LOUD', point: [475, 424], elbow: [565, 537], label: [750, 558] },
  { caption: 'A simple gesture. A clear intention.', callout: 'ONE DELIBERATE PRESS', point: [612, 292], elbow: [674, 207], label: [775, 191] },
  { caption: 'Separate pieces, becoming a single loop.', callout: 'POWER FROM THE WALL', point: [681, 521], elbow: [717, 602], label: [774, 625] },
  { caption: 'A possible form. A real build still to come.', callout: 'A POSSIBLE FINAL FORM', point: [514, 334], elbow: [635, 206], label: [764, 190] },
];

export const PARTS = {
  jetson: [
    [0, 425, 355, 1.03, 0, 1],
    [1, 399, 327, .84, -2, 1],
    [2, 403, 310, .80, 0, 1],
    [3, 394, 290, .76, 0, 1],
    [4, 384, 275, .72, 0, 1],
    [5, 382, 272, .70, 0, 1],
    [5.25, 382, 272, .70, 0, 1],
    [5.85, 428, 354, .67, 0, 1],
    [6.2, 430, 358, .66, 0, 0],
  ],
  storage: [
    [0, 724, 154, .60, -25, 0],
    [.48, 724, 154, .60, -25, 0],
    [.9, 602, 231, .88, -8, 1],
    [1.15, 592, 244, .90, -6, 1],
    [1.95, 285, 309, .40, -10, 1],
    [3, 276, 300, .38, -10, 1],
    [5.22, 270, 297, .38, -10, 1],
    [5.8, 381, 352, .30, -16, 1],
    [6.05, 396, 356, .25, -16, 0],
  ],
  microphone: [
    [0, 112, 493, .95, -24, 0],
    [1.46, 112, 493, .95, -24, 0],
    [1.95, 211, 402, 1.30, -8, 1],
    [2.14, 216, 396, 1.30, -8, 1],
    [3, 266, 380, .80, 0, 1],
    [4, 244, 359, .76, 0, 1],
    [5.25, 244, 359, .76, 0, 1],
    [5.85, 375, 379, .48, 0, 1],
    [6.1, 386, 397, .45, 0, 0],
  ],
  speaker: [
    [0, 579, 559, .95, 14, 0],
    [2.45, 579, 559, .95, 14, 0],
    [2.98, 500, 447, .80, 0, 1],
    [3.25, 500, 442, .80, 0, 1],
    [4, 464, 421, .76, 0, 1],
    [5.25, 464, 421, .76, 0, 1],
    [5.85, 431, 420, .48, 0, 1],
    [6.15, 424, 410, .45, 0, 0],
  ],
  button: [
    [0, 706, 139, .90, 20, 0],
    [3.46, 706, 139, .90, 20, 0],
    [3.98, 611, 320, 1.16, 0, 1],
    [4.22, 605, 324, 1.12, 0, 1],
    [5.25, 582, 365, .84, 0, 1],
    [5.85, 520, 354, .66, 0, 1],
    [6.12, 508, 350, .64, 0, 0],
  ],
  power: [
    [0, 759, 646, .70, 14, 0],
    [4.45, 759, 646, .70, 14, 0],
    [4.98, 689, 550, .88, 0, 1],
    [5.25, 687, 546, .86, 0, 1],
    [5.9, 720, 521, .65, 0, .60],
    [6.3, 790, 456, .45, 0, 0],
  ],
  enclosure: [
    [0, 431, 178, 1.02, 0, 0],
    [5.55, 431, 178, 1.02, 0, 0],
    [5.85, 431, 302, 1.02, 0, .08],
    [6.08, 431, 378, 1.02, 0, .83],
    [6.3, 431, 382, 1.02, 0, 1],
  ],
};
