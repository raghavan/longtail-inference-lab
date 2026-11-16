# Local Voice website preview

Status: approved for production promotion on November 15, 2026.

The preview preserves the existing seven-stage scroll-driven hardware assembly and adds a retro illustrated account of the real software pipeline: Whisper tiny.en → Gemma 4 E2B → Piper neural speech. It removes the numbered hardware-study masthead. The owner requested local visual review before production.

## Review the mock-up

Serve `mockup/` using a local static HTTP server. No dependencies or build are required. The files are outside the public website deployment directory. Owner review is complete; the approved version is copied into `areas/public_website/device/`.

- `mockup/index.html`: hardware narrative, model journey, platform status, and evidence boundaries.
- `mockup/inside.css` and `mockup/inside.js`: illustration layout, scroll sequence, and chapter navigation.
- `mockup/assets/voice-models.png`: original generated retro editorial illustration. A person speaks to the prototype; sound features, learned model layers, tokens, and neural speech generation are drawn above one Jetson circuit-board cutaway.
- `mockup/styles.css`, `assembly.js`, `choreography.mjs`, and the original SVG assets preserve the hardware story.

The former printer, computer, and radio metaphors have been replaced by representations of the actual operations. The enlarged board is schematic, not a literal board layout. The person and prototype concept remain. A separate original enclosure SVG ties the software story to the hardware assembly.

## Interaction

The illustration follows one fixed question: “What is the capital of France?” Scroll through the five stages or select a chapter. Recognition reveals the transcript, Gemma reveals answer pieces, Piper animates a waveform, and the reply returns to the same device. Each active illustrated widget gives a brief, two-cycle wiggle when its stage begins; the prototype moves on listening and reply. The person and board remain still. There is no traveling signal dot. SVG masks and clips reuse the original illustration without new image assets. Reduced-motion preferences disable the wiggles.

The owner asked to keep this area simple. There is no example selector, exploration slider, playback toolbar, or technical toggle in the illustration. Runtime details remain in the reading section below it. Narrow screens pan to the active station; short viewports retain chapter selection. Reduced-motion handling removes spatial effects.

The pictures, layer counts, token pieces, and waveform are explanatory abstractions, not real activations, exact tokenizer output, recorded audio, or benchmark results. Gemma receives text from Whisper in this application; its native audio capability is not used. Piper embeds eSpeak for phonemization, while its ONNX neural voice generates the waveform.

## Current configuration and evidence

Source inspection identifies Whisper tiny.en F16, Gemma 4 E2B instruction-tuned Q4_K_M, and Piper 1.8.0 with `en_US-ljspeech-medium`, 22,050 Hz output. The model server uses a 2,048-token context and 128-token default answer cap, with thinking disabled. CUDA is used for recognition and answering; Piper uses the CPU.

The current resident-worker deployment reports ready service, 55 passing regressions, phrase streaming, and two confirmed fast, complete live answers. Live playback requests were 1.113 and 1.061 seconds after capture ended, distinct from nine authored WAV trials with a 0.827-second median. Acoustic onset was not instrumented. New profile-specific reboot/disconnection and long-session qualification remain open. Old-model timing figures were removed from this current-stack presentation. No quality benchmark is claimed.

Authorities:

- [Technical status](../../../projects/02_edge_offline_intelligence_device/status.md).
- [Upgrade contract](../../../projects/02_edge_offline_intelligence_device/development/jetson_gemma4_voice_upgrade.md).
- [Deployment evidence](../../../projects/02_edge_offline_intelligence_device/results/2026-11-15-jetson-responsive-voice.md).
- [Runtime lock](../../../projects/02_edge_offline_intelligence_device/software/jetson/runtime-lock.json) and [application source](../../../projects/02_edge_offline_intelligence_device/software/jetson/local_voice/core.py).
- [Whisper upstream](https://github.com/openai/whisper), [Google Gemma](https://ai.google.dev/gemma/docs/core), and [Piper upstream](https://github.com/OHF-Voice/piper1-gpl) support the conceptual explanations.

## EGM state

Scoped presentation change over the existing architecture and website contract. The [drift report](2026-11-15_DRIFT_REPORT.md) records alignment findings. Visual-review revisions are implemented; the owner’s local design review is complete. Production promotion is authorized; no Goldfish review is claimed. No device code changes belong to this task.

## Verification

JavaScript syntax, whitespace, and repository safety checks passed. Desktop (1280 × 800) and phone (375 × 667) layouts were checked after removing the toolbar; stage selection and responsive panning still work, with no page overflow or captured console warnings/errors. The widget-motion revision was checked at both sizes: each of the five stages selects only its corresponding widget animation, with no signal-dot element remaining. No select or input controls remain in the illustration. The temporary viewport override was reset. Reduced-motion handling remains in source; OS-level emulation is not claimed.

The approved files are promoted into the production device page. Concurrent device work remains separate. Deployment status is tracked in the task knowledge record.
