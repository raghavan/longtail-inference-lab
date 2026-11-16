# Local Voice website preview

Status: local design preview, November 15, 2026. Not approved for production.

This is a standalone presentation of Local Voice for the existing device route. It preserves the original seven-stage hardware assembly, typography, paper color, illustrations, and reverse scrolling. It removes the numbered hardware-study masthead and adds a second interactive story explaining a spoken question, transcription, local inference, speech synthesis, and the reply returning to the same person and device.

## Review the mock-up

Serve `mockup/` using a local static HTTP server. No dependencies or build are required. The files are outside the public website deployment directory. Do not copy them into the deployed website until the owner reviews the preview.

- `mockup/index.html`: hardware narrative, architecture, platform status, and evidence.
- `mockup/inside.css` and `mockup/inside.js`: architecture presentation and scroll/click navigation.
- `mockup/styles.css`, `assembly.js`, `choreography.mjs`, and `assets/`: preserved hardware experience, with refreshed wording.

The architecture examples are deliberately authored illustrations, not live inference or measured outputs. The revised story uses a warm-paper, 1990s-style panoramic illustration: person and prototype, tape/typewriter for Whisper, terminal for Qwen, and a speech synthesizer for eSpeak. Scrolling reveals a question bubble, a transcript slip, incremental answer tokens, speech text, and a reply bubble with a return path. These machines are metaphors for software running on the same Jetson, not additional hardware. The original enclosure SVG also appears as a reference. The main narrative omits button protocol details; technical parameters sit below the story.

The panorama reads left to right on desktop. Narrow screens pan to the active station, with shorter copy and horizontal touch scrolling. Stage controls and the four illustrated stations support direct selection; short viewports use a non-sticky presentation. The illustrative token tiles do not claim exact tokenizer segmentation. Model identities follow the validated November 15 Qwen/eSpeak baseline; reconcile any later device upgrade before production promotion.

## Content authorities

- [Current technical status](../../../projects/02_edge_offline_intelligence_device/status.md).
- [Architecture decision](../../../projects/02_edge_offline_intelligence_device/design_direction.md).
- [Jetson implementation](../../../projects/02_edge_offline_intelligence_device/software/jetson/README.md) and [runtime lock](../../../projects/02_edge_offline_intelligence_device/software/jetson/runtime-lock.json).
- [CUDA development check](../../../projects/02_edge_offline_intelligence_device/results/2026-11-15-jetson-cuda-check.md).
- [Existing website contract](../../../areas/public_website/device/README.md).

The preview separates CPU standalone checks from CUDA integration and the remaining CUDA button/reboot checks. It preserves the two-trials-per-profile timing boundary, recording/playback exclusion, and lack of scored quality or cross-platform measurements. The enclosure and tiny speaker illustration remain conceptual.

## EGM state

Scoped presentation change over the existing architecture and website contract. Drift analysis is in [the report](2026-11-15_DRIFT_REPORT.md). The owner requested a visual mock-up before production; that review is the current gate. No Goldfish design review or production approval is claimed. No device implementation changes are included.

## Verification

- Local HTTP response: 200; JavaScript syntax checks passed for all three modules.
- HTML IDs, local assets, and internal fragment targets checked; no broken local references.
- In-app browser: architecture stage selection, reverse scrolling, keyboard Tab/Enter navigation, and hardware chapter navigation checked. No captured console warnings or errors.
- Responsive checks: desktop, 390 × 844, 375 × 667, and 320 × 568. All five stages fit above the controls at 375 × 667. The 320 × 568 view uses the non-sticky fallback; no horizontal page overflow was observed.
- Fixed the timing card's intrinsic width on phones, small-screen architecture overlap, and hardware SVG overlap with chapter controls. Direct chapter selection jumps immediately; ordinary scrolling retains the original assembly interpolation.
- Reduced-motion rules retained and inspected in source; an OS-level reduced-motion browser test was not performed.
- Repository safety scan and whitespace checks passed.
- No production files changed by this task, no source push, and no production deployment. Production remains a separate step after visual review.

## Retro illustration revision

The owner requested a less stacked, less technical presentation with a person, the prototype device, and a retro illustrated round trip. The generated `mockup/assets/voice-workshop.png` is a task-owned editorial illustration; text, token reveals, route, stage labels, and speech bubbles are separate accessible HTML/SVG layers. No image generation occurs in the website.

Revision checks: JavaScript syntax, local image loading, no captured console errors/warnings, and desktop fit at 1280 × 800. All five stages passed heading/scene/caption spacing and page-width checks at 375 × 667. The 390 × 844 view was inspected and shortened mobile copy subsequently applied; the 320 × 568 non-sticky fallback and keyboard Tab/Enter stage selection passed. Viewport override was reset after inspection. Reduced-motion handling remains in source; no OS-setting emulation is claimed.

This revision changes only the local preview and its records. No production publication.
