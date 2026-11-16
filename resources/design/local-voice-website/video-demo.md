# Recorded device demo — local design review

Date: November 15, 2026. Status: implemented in the isolated mock-up; owner visual approval pending. No source push or production deployment authorized yet for this addition.

## Agreed scope

Append the owner-selected clockwise landscape recording to the end of the device page, immediately before its colophon. Show example-specific timing on the left on desktop. Preserve the existing warm paper, bronze, serif/mono design. On phones, put the player first and stack the statistics below it. Use native browser video controls, manual playback, a poster image, English captions and a downloadable fallback. No new player library or hosting service.

This continues the existing website contract; it does not introduce a new device experiment. EGM artifact directory is this design folder. Workflow stage: scoped implementation and drift check, then owner visual review. No Goldfish review is claimed.

## Media preparation

The selected original has an unchanged background and real interaction. A local AVFoundation export applies the clockwise orientation to the pixels and converts HLG/Dolby Vision to Rec.709 SDR. The delivery encode is 1920 × 1080 H.264 MP4 at 30 fps, with progressive-download metadata at the front. The original stereo AAC stream is copied, not synthesized or edited. All 537 video frame timestamps match the original; the full visual timeline is 17.900 seconds. The MP4 container is 17.919 seconds because of AAC packet duration. There are no editorial cuts, speed changes or generated foreground/background frames.

Source fingerprint (selected original): `22ce35642a8eb36fccfb2e36a0ee3a3d765698c64be96ebfe09dcf2bc6e7ca2c`.
Audio packet SHA-256, identical before and after: `c2878fef0abea832cf5f0bbf3f5a1db8219e2a2205a51906ea5a5447c1d6b427`.

Only the deliberately selected technical demonstration, web derivative, poster and associated caption track belong to this preview. Raw working analysis and unrelated personal material are excluded.

## What the displayed numbers mean

| Display | Evidence and boundary |
| --- | --- |
| Approximately 1.6 seconds to first spoken word | Recording-state red light remains visible at frame 234 (7.800 s) and disappears by frame 235 (7.833 s). The first clearly audible reply starts around 9.43–9.45 s in the recording waveform. Difference approximately 1.60–1.65 s, rounded to 1.6 s. This is a video-derived recording-end indicator to acoustic-reply estimate, not isolated model processing time or instrumented button-event latency. |
| Approximately 6.5 seconds spoken reply | First spoken output about 9.44 s; final spoken word finishes about 15.95 s. Includes the pause between the two sentences. Boundary is approximate because room noise continues. |
| 17.9 seconds uncut take | 537 frames at 30 fps. This is recording length, not processing latency. |

No stage-by-stage ASR, LLM or speech-synthesis time is available for this specific take. The separately published live playback-request and authored-WAV timings are not substituted for this example. Current model labels follow the existing runtime record and are configuration context, not independently proven by the movie.

English captions were prepared locally from the selected technical demo. The question is about explaining a large language model to a five-year-old; the two spoken reply sentences are retained. The owner can review the recording and caption wording in the preview.

## Files

- `mockup/index.html`: appended `#real-demo` section and demo stylesheet reference.
- `mockup/demo.css`: isolated layout and responsive styles.
- `mockup/assets/demo/local-voice-demo.mp4`: browser-ready original recording.
- `mockup/assets/demo/local-voice-demo-poster.jpg`: still extracted from that recording.
- `mockup/assets/demo/local-voice-demo.en.vtt`: English captions.

## Verification

Desktop 1280 × 720 and 1280 × 900, and narrow 390 × 844 layout inspected in the local browser. Statistics sit left on desktop; video sits above statistics on narrow screens. No page horizontal overflow observed. Native playback reached 16.4 seconds with 1920 × 1080 decoded dimensions, readyState 4, no video error, and an English captions track exposed. No captured console warnings or errors. Temporary viewport override reset. Poster and fallback assets resolve locally. Full-file decode, relative-asset validation, repository safety scan and whitespace checks passed.

## Release gate

This preview is outside the GitHub Pages upload directory. After explicit owner approval, promote the added section, stylesheet and demo assets to `areas/public_website/device/`, reconcile the production README, run checks, commit/push the task changes and verify GitHub Pages deployment and live video. Preserve unrelated brief edits.
