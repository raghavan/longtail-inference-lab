# Local Voice website preview

Status: local design preview, November 15, 2026. Not approved for production.

This is a standalone presentation of Local Voice for the existing device route. It preserves the original seven-stage hardware assembly, typography, paper color, illustrations, and reverse scrolling. It removes the numbered hardware-study masthead and adds a second interactive story explaining capture, transcription, answering, synthesis, and playback.

## Review the mock-up

Serve `mockup/` using a local static HTTP server. No dependencies or build are required. The files are outside the public website deployment directory. Do not copy them into the deployed website until the owner reviews the preview.

- `mockup/index.html`: hardware narrative, architecture, platform status, and evidence.
- `mockup/inside.css` and `mockup/inside.js`: architecture presentation and scroll/click navigation.
- `mockup/styles.css`, `assembly.js`, `choreography.mjs`, and `assets/`: preserved hardware experience, with refreshed wording.

The architecture examples are deliberately authored illustrations, not live inference or measured outputs. Model names and implementation limits come from the current source. eSpeak is a functional synthesizer, not another language model. The dark architecture section uses the same typography and bronze accent as the hardware section. Its nodes and stage controls support direct selection; short viewports use a non-sticky, directly selectable presentation.

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
