# Local Voice website preview

Status: local design preview, November 15, 2026. Not approved for production.

The preview preserves the existing seven-stage scroll-driven hardware assembly and adds a retro illustrated account of the real software pipeline: Whisper tiny.en → Gemma 4 E2B → Piper neural speech. It removes the numbered hardware-study masthead. The owner requested local visual review before production.

## Review the mock-up

Serve `mockup/` using a local static HTTP server. No dependencies or build are required. The files are outside the public website deployment directory. Do not promote them before owner review.

- `mockup/index.html`: hardware narrative, model journey, platform status, and evidence boundaries.
- `mockup/inside.css` and `mockup/inside.js`: illustration layout, scroll sequence, animation, scrubbing, example selection, and runtime details.
- `mockup/assets/voice-models.png`: original generated retro editorial illustration. A person speaks to the prototype; sound features, learned model layers, tokens, and neural speech generation are drawn above one Jetson circuit-board cutaway.
- `mockup/styles.css`, `assembly.js`, `choreography.mjs`, and the original SVG assets preserve the hardware story.

The former printer, computer, and radio metaphors have been replaced by representations of the actual operations. The enlarged board is schematic, not a literal board layout. The person and prototype concept remain. A separate original enclosure SVG ties the software story to the hardware assembly.

## Interactions

- Scroll or select a stage to follow the question left to right and the spoken reply back to the same device.
- Animate/pause one turn; the explicit animation takes about twenty seconds from the beginning and does not represent device latency. Wheel, touch, navigation keys, or hiding the tab interrupts playback.
- Scrub the timeline with a range control, including keyboard input.
- Choose one of three authored examples: capital of France, sunlight for plants, or a short walk. Questions and replies update consistently. No inference, recording, speech playback, or external API call occurs in the page.
- Toggle “Under the hood” for exact runtime/model details and diagram annotations.
- Recognition reveals transcript pieces while a scan line crosses the schematic spectrogram; Gemma reveals illustrative token pieces; Piper animates a waveform; the final path returns to the speaker/listener.
- Narrow screens pan to the active station and use concise copy. Short viewports provide a non-sticky, selectable version. Reduced-motion handling removes spatial illustration effects.

The pictures, layer counts, token pieces, and waveform are explanatory abstractions, not real activations, exact tokenizer output, recorded audio, or benchmark results. Gemma receives text from Whisper in this application; its native audio capability is not used. Piper embeds eSpeak for phonemization, while its ONNX neural voice generates the waveform.

## Current configuration and evidence

Source inspection identifies Whisper tiny.en F16, Gemma 4 E2B instruction-tuned Q4_K_M, and Piper 1.8.0 with `en_US-ljspeech-medium`, 22,050 Hz output. The model server uses a 2,048-token context and 128-token default answer cap, with thinking disabled. CUDA is used for recognition and answering; Piper uses the CPU.

The current deployment record reports an active/enabled/ready service, 42 passing regressions, and authored pipeline checks. Physical neural-voice listening acceptance, a new reboot, and disconnected operation for this profile remain pending. Old-model timing figures were removed from this current-stack presentation. No quality benchmark is claimed.

Authorities:

- [Technical status](../../../projects/02_edge_offline_intelligence_device/status.md).
- [Upgrade contract](../../../projects/02_edge_offline_intelligence_device/development/jetson_gemma4_voice_upgrade.md).
- [Deployment evidence](../../../projects/02_edge_offline_intelligence_device/results/2026-11-15-jetson-gemma4-piper.md).
- [Runtime lock](../../../projects/02_edge_offline_intelligence_device/software/jetson/runtime-lock.json) and [application source](../../../projects/02_edge_offline_intelligence_device/software/jetson/local_voice/core.py).
- [Whisper upstream](https://github.com/openai/whisper), [Google Gemma](https://ai.google.dev/gemma/docs/core), and [Piper upstream](https://github.com/OHF-Voice/piper1-gpl) support the conceptual explanations.

## EGM state

Scoped presentation change over the existing architecture and website contract. The [drift report](2026-11-15_DRIFT_REPORT.md) records alignment findings. Visual-review revisions are implemented; the owner’s local design review remains the current gate. No Goldfish review or production approval is claimed. No device code changes belong to this task.

## Verification

JavaScript syntax, unique HTML IDs, local assets, internal fragment targets, whitespace, and repository safety scan are checked. In-app browser QA covers desktop and mobile layouts, stage selection, example changes, animation/pause, keyboard scrubbing, runtime detail toggle, and the short-viewport fallback. No external inference service or microphone permission is needed. OS-level reduced-motion emulation is not claimed.

No production files are changed by this task. No source push or production deployment. Concurrent device work remains separate.

Current revision observations: the twenty-second animation completed at step 5 with the matching short-walk response and reset its play state. Pause stopped an in-progress turn. Keyboard Home/ArrowRight changed the scrub position. All three example selectors updated the question, answer pieces, and reply. Runtime detail mode showed the correct Gemma and Piper configurations. All stages fit at 375 × 667 after shortening the Piper heading/copy; 320 × 568 used the non-sticky fallback without page overflow. The final 1280 × 800 preview had no missing images or captured console warnings/errors. Temporary browser viewport overrides were reset.
