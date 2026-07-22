# Edge Offline Intelligence Device

## Status

Proposal

This document describes a possible lab project. It is not an active experiment and does not yet have an implementation commitment.

## Project idea

Build a small, self contained voice intelligence device that can listen, understand, answer, and speak without an internet connection or another local computer.

The device should contain its own:

1. Microphone input
2. Speaker output
3. Edge compute
4. Local open weight models
5. Local storage
6. Battery or portable power system
7. Physical privacy controls
8. Minimal interaction surface

The central principle is:

> Intelligence should remain available when the network disappears.

## Design thesis

Most voice assistants are lightweight terminals for remote infrastructure. They stop being intelligent when the network, account, service, or provider is unavailable.

The Edge Offline Intelligence Device explores the opposite design:

```text
Voice
  |
  v
Local speech recognition
  |
  v
Local open weight language model
  |
  v
Local speech generation
  |
  v
Voice
```

The complete conversation path remains inside one physical device.

The user may install models and software while connected, then place the device into an offline mode where no network is required for ordinary use.

## Why this is a project

This idea is broader than one experiment because several hardware and software capabilities must behave as one dependable appliance:

1. Compact edge inference
2. Speech capture
3. Speech recognition
4. Language generation
5. Speech synthesis
6. Audio playback
7. Power management
8. Thermal management
9. Model storage
10. Physical interaction design
11. Offline recovery
12. Privacy and local memory policy

Individual experiments can later compare models, audio components, power modes, and enclosure designs. The complete device is a systems and product project.

## Intended experience

The device should feel closer to a small personal object than a developer computer.

A normal interaction should be:

1. Press and hold the top control.
2. Speak naturally from close range.
3. Release the control.
4. The device transcribes the question locally.
5. A local model generates a concise answer.
6. The device speaks the answer through its own speaker.

No phone, browser, cloud account, WiFi connection, or companion server should be required.

## Audio direction

The physical voice path is:

1. **Input:** tiny microphone
2. **Output:** tiny speaker

The first version should use one compact audio module containing both components.

## Luxury minimalist interaction

Luxury minimalism is not only a visual style. It is a reduction of decisions, dependencies, and visible machinery.

The device should have:

1. No screen
2. One primary press and hold control
3. One physical microphone mute control
4. One restrained status light
5. One charging connection
6. One speaker opening
7. No keyboard
8. No touch interface
9. No account setup after initial installation
10. No required mobile application

The enclosure should hide the development board, cables, storage, audio module, battery system, and cooling components.

The user should experience one object and one interaction.

## Why push to talk should be the default

The first version should not begin with an always listening wake word.

Push to talk provides:

1. Lower idle power consumption
2. Stronger privacy
3. Fewer accidental activations
4. No continuous speech processing
5. Less microphone feedback from the speaker
6. Simpler audio hardware
7. Better operation with a tiny close range microphone
8. Clear conversational turn boundaries

The device can stop recording before playback begins. This half duplex interaction avoids the need for a large microphone array and complex acoustic echo cancellation.

A wake word can remain a later experiment rather than a first version requirement.

## Day to day uses

The device is intended for brief, useful conversations such as:

1. Explain a historical event.
2. Define an unfamiliar idea.
3. Compare two concepts.
4. Help think through a decision.
5. Suggest a simple routine.
6. Rephrase a sentence.
7. Recall general knowledge contained in the model.
8. Summarize a locally stored note.
9. Answer questions while traveling without connectivity.
10. Provide a private voice notebook mode.

It should prefer short spoken answers. Long responses are difficult to consume through a tiny speaker and consume unnecessary energy.

## System boundary

The complete trusted system includes:

1. Microphone
2. Audio codec
3. Edge compute module
4. Local storage
5. Speech recognition model
6. Language model
7. Speech generation model
8. Conversation controller
9. Optional local memory
10. Speaker

The ordinary interaction path must not require:

1. Cloud speech recognition
2. Remote model inference
3. Cloud speech generation
4. A local network server
5. A phone application
6. A web account
7. Telemetry
8. Remote logging

## Reference architecture

```text
Press and hold control
        |
        v
Tiny microphone
        |
        v
Voice activity and recording
        |
        v
Local speech to text model
        |
        v
Local conversation controller
        |
        v
Local open weight language model
        |
        v
Local text to speech model
        |
        v
Tiny speaker
```

Supporting services:

```text
Local NVMe storage
Battery and charging controller
Thermal and power controller
Physical mute state
Optional encrypted local memory
```

## Reference hardware direction

### Prototype compute

Begin with an **NVIDIA Jetson Orin Nano Super Developer Kit with 8 GB memory**.

This is the lowest complexity way to validate the complete pipeline because it provides:

1. CUDA acceleration
2. A supported Jetson software stack
3. Enough memory for a compact quantized language model when services are managed carefully
4. NVMe storage support
5. USB audio support
6. A practical path to TensorRT optimized speech models

The developer kit is a prototype platform, not the final physical form.

### Refined compute

A refined daily device should evaluate an **NVIDIA Jetson Orin NX 16 GB module on a compact carrier board**.

The additional memory should make it easier to keep speech recognition, language generation, and speech synthesis available without aggressive unloading. A smaller carrier can also produce a cleaner enclosure than the full developer kit.

The project should first measure whether the 8 GB prototype delivers an acceptable experience before moving to the more expensive module.

### Storage

Use a local NVMe SSD rather than removable flash storage for routine use.

A 512 GB SSD is sufficient for the initial system and provides room for:

1. Operating system
2. Containers or runtimes
3. Several quantized models
4. Speech models
5. Voice files
6. Evaluation recordings
7. Optional offline documents
8. Update rollback images

The final device should not expose storage during normal use.

## Tiny audio direction

### Preferred personal audio module

Evaluate the **M5Stack Atom VoiceS3R** as the smallest integrated audio front end.

It contains:

1. A MEMS microphone
2. A one watt speaker
3. A mono audio codec
4. A physical button
5. A compact enclosure measuring approximately 24 by 24 by 17 millimeters
6. USB power and programmable firmware

The project should test whether it can operate as a direct USB audio device attached to the Jetson inside the same enclosure.

This module is appropriate because the device is a close range personal assistant rather than a room scale smart speaker.

The first version should reuse its button as the press and hold interaction control when practical.

### Audio fallback

If the tiny audio module produces poor recording quality, electrical noise, or insufficient playback volume, evaluate the **ReSpeaker XVF3800 USB microphone array** with a small internal speaker.

The fallback provides stronger voice processing, including beamforming, noise suppression, and acoustic echo cancellation, but it is physically larger and conflicts with the smallest possible form.

Move to the larger audio board only when measurements show that the tiny module is not usable.

### Speaker expectations

A one watt speaker is not intended for room filling audio.

The target experience is:

1. Personal distance
2. Quiet office
3. Bedside use
4. Short spoken answers
5. Moderate volume
6. Clear speech rather than music quality

The enclosure should include a small acoustic chamber so the speaker does not sound thinner than necessary.

## Portable power direction

The device should support:

1. Plugged in desk mode
2. Battery powered portable mode

The prototype should use a certified external battery pack and a commercial regulated power path rather than loose lithium cells.

The portable design should aim for:

1. USB C charging
2. Safe battery management
3. Charge while operating
4. Clean shutdown before battery exhaustion
5. Visible low battery indication
6. A replaceable or serviceable battery pack when possible
7. No exposed power conversion boards

Because the Jetson developer kit expects a dedicated power input, the project must validate the battery and regulator under peak inference load before calling the device portable.

A refined carrier board may provide a cleaner power design than adapting the developer kit.

## Thermal design

Local inference produces heat even when the enclosure is small.

The device should use:

1. A metal internal frame or heat spreader
2. A quiet active fan when required
3. Large passive ventilation paths
4. A low power idle state
5. Model unloading after an inactivity period when useful
6. A performance mode that does not exceed safe surface temperatures

The enclosure should never sacrifice safe thermal behavior for visual purity.

The fan should remain off or nearly silent while idle and during short speech capture.

## Physical form

The first integrated enclosure should target a footprint close to a small external SSD or a thick deck of cards.

Possible form:

```text
Top

[ single recessed control ]
[ restrained status light ]

Front

[ narrow speaker grille ]

Side

[ physical microphone mute ]
[ USB C charging ]

Inside

[ audio module ]
[ Jetson and carrier ]
[ NVMe storage ]
[ battery ]
[ cooling path ]
```

Preferred materials and appearance:

1. Bead blasted aluminum or high quality matte polymer
2. Black, warm white, or natural metal finish
3. No exposed development board
4. No prominent branding
5. No decorative lighting
6. No robotic face or artificial personality cues

## Software stack

The initial software stack should remain deliberately small.

### Operating system

Use NVIDIA Jetson Linux through the current supported JetPack release.

The production image should boot directly into the voice service without exposing a desktop environment.

### Speech recognition

Begin with a compact Whisper family model through one of the Jetson compatible runtimes:

1. Whisper TensorRT
2. Faster Whisper
3. A compatible speech container from Jetson Containers

Initial candidates:

1. Whisper Base English for the lowest memory pressure
2. Whisper Small English for improved recognition quality
3. A multilingual Whisper variant when Tamil or other languages become a requirement

The speech model should run only after the user presses the control.

### Answer generation

Begin with a four bit quantized compact instruct model.

Primary candidates:

1. Qwen3.5 4B in text only, nonthinking mode when the runtime supports it reliably
2. Qwen3 4B as the compatibility baseline
3. Gemma 3 4B as an alternative quality and latency comparison

The model runtime should begin with:

1. Ollama for the simplest prototype
2. llama.cpp when tighter memory control or startup behavior is required
3. A Jetson optimized runtime only when measurement justifies the added complexity

The project should not lock itself to one model. The device is the stable product boundary and the model is replaceable.

### Speech generation

Begin with Piper because it is compact and represented in the Jetson container ecosystem.

Evaluate a higher quality compact voice such as Kokoro only when it fits the latency and memory budget.

The first priority is understandable speech with a fast first audio response.

### Conversation controller

Implement a small Python service that coordinates:

1. Button state
2. Recording
3. Speech recognition
4. Prompt construction
5. Language model request
6. Sentence streaming
7. Speech synthesis
8. Playback
9. Cancellation
10. Power and error states

Avoid a large agent framework.

The controller should be observable through local logs during development but should not require an interactive dashboard in normal use.

## Recommended model separation

Use separate models for speech recognition, answer generation, and speech generation in the first version.

This modular design provides:

1. Better memory control
2. Easier replacement
3. Clearer benchmarking
4. Smaller individual models
5. Easier failure diagnosis
6. Independent quality tuning

A unified audio language model can remain a later research direction. It should replace the modular pipeline only when it provides a measurable improvement in latency, quality, or simplicity on the same hardware.

## Memory management strategy

An 8 GB device requires disciplined scheduling.

The baseline controller should test:

1. Keeping the language model resident while loading speech models sequentially
2. Unloading speech recognition before language generation
3. Synthesizing one sentence at a time
4. Limiting conversation context
5. Disabling vision components
6. Using nonthinking generation for ordinary questions
7. Capping spoken response length
8. Using quantized model weights

The system should report actual peak memory rather than assuming individual model file sizes represent runtime use.

## Offline behavior

Offline operation is a hard requirement rather than a marketing label.

Verify operation with:

1. Ethernet disconnected
2. WiFi disabled or physically absent
3. DNS unavailable
4. System clock without network synchronization
5. No cached authentication tokens
6. No remote API fallback

The device should still:

1. Boot
2. Record speech
3. Transcribe
4. Answer
5. Speak
6. Preserve approved local settings
7. Recover from a failed interaction

Any feature that silently falls back to the cloud is outside the trusted path.

## Local knowledge

The language model contains imperfect historical and general knowledge.

A later phase can add a small offline knowledge library stored on the NVMe drive.

Possible sources include:

1. Selected encyclopedia content
2. Personal Markdown notes
3. Device manuals
4. A compact dictionary
5. A curated historical timeline

Retrieval should remain local. The device should distinguish between an answer generated from model memory and an answer grounded in a local document when practical.

The first version should not add retrieval until the basic voice loop is dependable.

## Local memory policy

Default behavior should be private and forgetful.

The device should not retain raw microphone recordings after successful transcription unless development mode is enabled.

Conversation memory options:

1. No memory
2. Current session only
3. User approved local notes
4. Encrypted persistent memory

The physical mute state must override all software behavior.

## Response style

The assistant should be optimized for listening rather than reading.

Default response policy:

1. Answer in one to four sentences.
2. Lead with the direct answer.
3. Avoid long enumerations unless requested.
4. Say when confidence is low.
5. Avoid fabricated precision.
6. Offer a deeper explanation only when asked.
7. Stop speaking immediately when the user presses the control again.

A tiny device becomes more useful when it respects attention.

## Device states

Use one restrained status light with a small vocabulary:

1. Off means idle or powered down.
2. Soft white means ready.
3. A gentle pulse means listening.
4. A slow pulse means thinking.
5. A steady warm light means speaking.
6. Red means physical microphone mute or error.
7. A brief amber pulse means low battery.

Audio cues should remain subtle and optional.

## Failure behavior

The device should fail clearly without requiring a screen.

1. If no speech is detected, play a short neutral tone.
2. If transcription confidence is low, ask for repetition.
3. If the model cannot load, speak a brief local error message.
4. If battery is too low, decline a new request and shut down safely.
5. If the device overheats, reduce performance or stop inference.
6. If the user interrupts, stop generation and playback immediately.

## Minimum viable project

### Phase 1: Desk prototype

Build the complete voice loop on a Jetson Orin Nano Super with:

1. NVMe storage
2. USB microphone
3. USB or integrated tiny speaker
4. Whisper speech recognition
5. Qwen or Gemma answer model
6. Piper speech generation
7. Python conversation controller
8. Press and hold interaction

The device may use its supplied power adapter during this phase.

### Phase 2: Tiny audio integration

Integrate the Atom VoiceS3R inside the device and validate:

1. Microphone clarity
2. Speaker intelligibility
3. Button behavior
4. USB stability
5. Electrical noise
6. Half duplex interaction
7. Close range usability

### Phase 3: Portable power

Add a certified battery system and measure:

1. Idle runtime
2. Conversations per charge
3. Peak power stability
4. Charge while operating
5. Thermal impact
6. Shutdown behavior

### Phase 4: Enclosure

Create a compact enclosure that presents only:

1. Primary control
2. Mute control
3. Status light
4. Speaker opening
5. Charging port

### Phase 5: Daily use pilot

Use the device for ordinary conversations over several weeks and record:

1. Questions asked
2. Abandoned interactions
3. Recognition failures
4. Slow responses
5. Incorrect answers
6. Battery inconvenience
7. Situations where a phone was still preferred
8. Situations where offline availability changed behavior

All collected voice data should remain local and be deleted or transformed into synthetic evaluation cases before repository publication.

## Suggested project structure

```text
edge_offline_intelligence_device/
  README.md
  hardware/
    bill_of_materials.md
    enclosure.md
    power.md
    audio.md
  software/
    controller/
      main.py
      audio.py
      speech_to_text.py
      language_model.py
      text_to_speech.py
      state.py
    systemd/
    configuration/
  evaluations/
    speech_cases.jsonl
    question_set.jsonl
    power_protocol.md
    daily_use_protocol.md
  results/
    README.md
```

All committed recordings and conversations must be synthetic or explicitly approved for publication.

## Evaluation plan

The project should compare complete pipelines rather than isolated benchmark scores.

### Speech recognition measures

1. Word error rate on representative speech
2. Recognition of names and historical terms
3. Accent robustness
4. End of speech detection delay
5. Peak memory
6. Energy per transcription

### Answer generation measures

1. Time to first token
2. Tokens per second
3. Time to first complete sentence
4. General knowledge accuracy
5. Historical factuality
6. Concision
7. Hallucination rate
8. Peak memory
9. Energy per answer

### Speech generation measures

1. Time to first audio
2. Intelligibility
3. Naturalness
4. Speaker volume
5. Peak memory
6. Energy per response

### Whole device measures

1. Time from button release to first spoken word
2. Successful conversation rate
3. Offline completion rate
4. Conversations per battery charge
5. Idle power
6. Surface temperature
7. Fan noise
8. Recovery after failure
9. User interruption latency
10. Daily preference compared with using a phone

## Initial performance targets

The first useful prototype should aim for:

1. Complete operation without any network
2. Speech recognition success on at least nine of ten ordinary questions
3. First spoken answer within approximately eight seconds for a short question
4. A concise response that finishes within approximately twenty seconds
5. At least two hours of intermittent portable use
6. Reliable press and hold behavior
7. Immediate physical microphone mute
8. Safe thermal operation
9. No retained raw audio by default
10. No companion device requirement

These are starting targets and should be revised after measurement.

## Project success criteria

The project becomes useful when a person can:

1. Pick up the device away from a network.
2. Press one control and ask a natural question.
3. Receive a clear spoken answer from local models.
4. Repeat the interaction without another computer.
5. Use the device on battery power.
6. Understand whether the microphone is active.
7. Interrupt or mute the device physically.
8. Continue using it after a full network disconnection.
9. Replace the answer model without redesigning the entire system.
10. Prefer it for at least some daily questions because it is private, immediate, and available.

## Non goals

The first version is not intended to be:

1. A frontier model replacement
2. A general autonomous agent
3. A smart home controller
4. A room scale conference speaker
5. A music speaker
6. A cloud connected assistant
7. A device with a large display
8. A tool calling platform
9. An always recording ambient computer
10. A benchmark optimized demonstration with no daily utility

## Important limitations

A compact local model may:

1. Produce incorrect historical facts
2. Confuse dates and names
3. Lack recent knowledge
4. Misunderstand noisy speech
5. Respond slowly
6. Sound mechanical through a tiny speaker
7. Consume significant battery during inference
8. Require active cooling
9. Have limited conversation memory
10. Perform poorly on complex reasoning

The device should expose these limits honestly rather than imitate confidence.

## Main technical risks

### Memory contention

Speech and language models may not fit comfortably at the same time on an 8 GB device.

Mitigation:

1. Sequential model loading
2. Smaller speech model
3. Four bit language model
4. Short context
5. Sentence based speech generation
6. Upgrade to Orin NX 16 GB only when necessary

### Audio feedback

A tiny microphone may hear the tiny speaker.

Mitigation:

1. Half duplex push to talk
2. Stop recording before playback
3. Physical separation inside the enclosure
4. Directional acoustic openings
5. A larger audio module only when required

### Battery instability

Inference can create short peak loads that cause shutdowns.

Mitigation:

1. Certified battery pack
2. Regulated power path
3. Peak load testing
4. Conservative power mode
5. Safe shutdown controller

### Thermal concentration

A compact enclosure may trap heat.

Mitigation:

1. Metal heat spreader
2. Ventilation path
3. Quiet fan
4. Thermal throttling
5. Surface temperature measurements

### Product complexity

Adding wake words, memory, retrieval, tools, displays, and mobile applications could overwhelm the project.

Mitigation:

1. Preserve the one button voice loop as the core product.
2. Require measurements before adding any major subsystem.
3. Treat every visible feature as a cost.

## Relationship to the lab thesis

Long Tail Inference Laboratory studies how useful intelligence can move closer to the person and operate across ordinary devices rather than remain dependent on distant data centers.

The Edge Offline Intelligence Device turns that thesis into a physical object.

It asks:

1. How much useful intelligence can fit inside a personal edge device?
2. What quality is sufficient for everyday spoken questions?
3. How should speech, language, power, memory, and thermal limits be coordinated?
4. Does offline availability change when and how people use intelligence?
5. Can a small open weight model feel more dependable because it is owned and locally available?

The project also provides a concrete platform for later experiments in:

1. Offline knowledge retrieval
2. Local memory
3. Privacy aware inference
4. Model routing
5. Energy aware inference
6. Long tail model evaluation
7. Personal intelligence appliances

## Open design questions

1. Is the Jetson Orin Nano Super 8 GB sufficient for a satisfying complete voice loop?
2. Does the tiny Atom VoiceS3R provide acceptable microphone and speaker quality inside one enclosure?
3. What is the best speech recognition model for accuracy per watt?
4. Which four billion parameter model gives the best spoken answer quality per second?
5. Should the language model remain resident while speech models load only when needed?
6. Can the first spoken sentence begin while the language model is still generating later sentences?
7. How much battery capacity is required for a useful daily object?
8. Is a fan acceptable in a personal voice appliance?
9. Should the device retain any conversation memory by default?
10. Can a local offline encyclopedia materially reduce factual errors without making the system complex?
11. Is push to talk sufficient, or does a wake word create meaningful daily value?
12. Does a unified speech model ever become smaller or faster than the modular pipeline on Jetson?
13. What enclosure geometry produces intelligible speech from a one watt speaker?
14. What answer length feels useful without becoming tiring to hear?
15. Which failures cause the user to return to a phone immediately?

## Reference starting points

1. [NVIDIA Jetson Orin Nano Developer Kit guide](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/quick_start.html)
2. [Jetson Containers](https://github.com/dusty-nv/jetson-containers)
3. [Qwen3.5 4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
4. [M5Stack Atom VoiceS3R documentation](https://docs.m5stack.com/en/core/Atom_EchoS3R)
5. [ReSpeaker XVF3800 documentation](https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/)
