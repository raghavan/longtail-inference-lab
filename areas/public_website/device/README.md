# Local Voice device website

The hardware and model-architecture page at <https://lily.md/device/>. This page follows the laboratory homepage's Newsreader and IBM Plex Mono typography, warm paper, bronze accents, and fine rules.

The experience starts with a Jetson and introduces storage, a microphone, a speaker, a button, and power. Scrolling gathers the components into an illustrative enclosure. Scrolling backward reverses the sequence. The chapter controls jump directly to each component; reduced-motion preferences select still frames.

The model journey follows one authored France question through Whisper tiny.en, Gemma 4 E2B, and Piper, ending at speech output. Each widget briefly wiggles during its action; no traveling signal dot or customization toolbar is used. Scroll or illustrated model-station controls advance the story. Reduced motion disables wiggles. The runtime keeps models resident and streams complete phrases; the four visual stages separate overlapping jobs for clarity. The illustration is explanatory, not a live model run or measured activation trace.

## Editing

- `index.html` contains the narrative and scene structure.
- `styles.css` contains the hardware layout; `inside.css` styles the model journey and reading sections.
- `inside.js` maps scroll/model-station navigation to the fixed example and active widget wiggles.
- `choreography.mjs` contains the chapter data and component poses in the 820 by 720 scene.
- `assembly.js` maps native scroll position to the poses and chapter controls.
- `assets/` contains seven self-contained SVG hardware illustrations and the original generated retro model illustration. SVG masks and clips animate its individual widgets without moving the board or person.

Serve the parent website directory with a static HTTP server and visit the `device/` route. No package installation or build step is required. The existing GitHub Pages workflow publishes the page when website changes reach `main`. The typography uses the same Google Fonts families as the existing site, with local serif and monospace fallbacks.

## Evidence boundary

The [hardware record](../../../projects/02_edge_offline_intelligence_device/hardware/portable_procurement.md) is authoritative. Component illustrations are simplified, and enclosure fit, scale, cooling, and cable routing are conceptual. The first physical build is mains-powered; screen, battery, and portable enclosure remain deferred. The current resident/streaming Gemma 4 E2B/Piper configuration has a [dated latency record](../../../projects/02_edge_offline_intelligence_device/results/2026-11-15-jetson-responsive-voice.md); distinguish synthetic playback-request timestamps from live acoustic onset, and do not apply the preceding model/voice latency figures to it. No scored quality or cross-platform comparison is published.

The speaker is drawn as a tiny USB form study at the microphone's visual size. This is a presentation concept, not the housing or dimensions of the ordered Adafruit 3369 speaker.

The USB card reader and setup cable are preparation accessories rather than permanent parts of the finished device, so they do not appear as separate assembly chapters. The mains power supply remains outside the illustrated enclosure; the final frame shows its lead, with the adapter outside the composition.

Manufacturer references: [Jetson layout](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/hardware_layout.html), [microphone](https://www.adafruit.com/product/3367), [speaker](https://www.adafruit.com/product/3369), and [AtomS3-Lite](https://docs.m5stack.com/en/core/AtomS3%20Lite). The SVGs are original illustrations, not manufacturer CAD.

## Design approval

The owner approved promotion of the locally reviewed mock-up on November 15, 2026. The [design record](../../../resources/design/local-voice-website/README.md) tracks the iterations. Production copy was reconciled with the resident-worker deployment and two confirmed live answers before promotion.

## Recorded demonstration

The page ends with the approved original clockwise landscape recording, a native video player, poster and optional English captions. The 1080p H.264/SDR delivery preserves source timing and stereo audio. Approximately 1.6 seconds to first speech and 6.5 seconds of spoken output are video-derived estimates. A compact sourced table provides cloud API latency context, explicitly distinguishing the single local take from benchmark medians and different tasks. See [demo evidence](../../../resources/design/local-voice-website/video-demo.md).

The November 15 owner-approved cleanup removes the three-platform overview, upcoming-work block, model-journey footer, return loop/repeated listener reply and hardware FIG. counters. The user explicitly authorized deploying the complete reviewed revision.
