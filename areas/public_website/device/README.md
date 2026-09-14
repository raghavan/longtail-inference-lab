# Local Voice assembly study

The hardware assembly page at <https://lily.md/device/>. This page follows the laboratory homepage's Newsreader and IBM Plex Mono typography, warm paper, bronze accents, and fine rules.

The experience starts with a Jetson and introduces storage, a microphone, a speaker, a button, and power. Scrolling gathers the components into an illustrative enclosure. Scrolling backward reverses the sequence. The chapter controls jump directly to each component; reduced-motion preferences select still frames.

## Editing

- `index.html` contains the narrative and scene structure.
- `styles.css` contains the page layout and responsive styles.
- `choreography.mjs` contains the chapter data and component poses in the 820 by 720 scene.
- `assembly.js` maps native scroll position to the poses and chapter controls.
- `assets/` contains seven self-contained, editable SVG illustrations.

Serve the parent website directory with a static HTTP server and visit the `device/` route. No package installation or build step is required. The existing GitHub Pages workflow publishes the page when website changes reach `main`. The typography uses the same Google Fonts families as the existing site, with local serif and monospace fallbacks.

## Evidence boundary

The [hardware record](../../../projects/02_edge_offline_intelligence_device/hardware/portable_procurement.md) is authoritative. Component illustrations are simplified, and enclosure fit, scale, cooling, and cable routing are conceptual. The first physical build is mains-powered; screen, battery, and portable enclosure remain deferred. Zero comparative quality or performance measurements are published for Mac, iPhone, or Jetson.

The speaker is drawn as a tiny USB form study at the microphone's visual size. This is a presentation concept, not the housing or dimensions of the ordered Adafruit 3369 speaker.

The USB card reader and setup cable are preparation accessories rather than permanent parts of the finished device, so they do not appear as separate assembly chapters. The mains power supply remains outside the illustrated enclosure; the final frame shows its lead, with the adapter outside the composition.

Manufacturer references: [Jetson layout](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/hardware_layout.html), [microphone](https://www.adafruit.com/product/3367), [speaker](https://www.adafruit.com/product/3369), and [AtomS3-Lite](https://docs.m5stack.com/en/core/AtomS3%20Lite). The SVGs are original illustrations, not manufacturer CAD.
