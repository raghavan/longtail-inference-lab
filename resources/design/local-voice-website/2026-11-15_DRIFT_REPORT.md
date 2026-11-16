# Local Voice website drift report

Scope: existing website presentation versus the November 15 architecture, runtime lock, controller, and dated development evidence. Only discrepancies and their disposition are listed.

## Existing public device page and website contract

- The live page inspected at the start of this task still described hardware assembly as future work and zero comparative measurements. The current source records standalone CPU operation and a limited CPU/CUDA comparison. The isolated preview updates that distinction; no production publication is authorized in this task.
- The numbered “hardware study” masthead and hardware-only story no longer cover the requested standalone Local Voice presentation. The preview removes the edition number, retains the assembly, and adds an independently navigable architecture section.
- The original final-frame caption said a real build was still to come. The preview now distinguishes the working voice loop from the conceptual enclosure.
- The former speaker label described only a tiny form study. The preview identifies the actual Adafruit 3369 while preserving the illustration's conceptual-size disclaimer.

## Architecture decision versus current implementation

- The architecture decision's early proposed-model wording is superseded in its later implementation note and runtime lock by Whisper tiny.en F16, Qwen2.5 1.5B Instruct Q4_K_M, and eSpeak NG. The preview presents those concrete development choices without claiming final quality qualification.
- The architecture decision's preliminary procurement and no-Jetson-implementation wording is stale when read without its implementation note. The preview uses the dated physical-device records for status, and does not rewrite the underlying research decision in this presentation-only task.

## CUDA development record versus broad status wording

- Broad “standalone operation works” wording could imply the CUDA profile had passed the same physical-button and reboot checks as CPU. The detailed CUDA record explicitly leaves those checks open. The preview labels CPU standalone evidence, CUDA integration, and pending CUDA physical acceptance separately.

## Visual review revision

- The initial dark, stacked component diagram did not match the requested illustrated left-to-right journey. It is replaced by a warm-paper retro panorama and a returning speech path, with the hardware story preserved.
- The initial narrative emphasized the AtomS3-Lite protocol. The revised architecture story instead follows sound → transcript → generated answer → synthesized speech → the original listener. Inference is explained separately from transcription and synthesis.
- The token and machinery illustrations are abstractions, not exact tokenizer output or extra physical components. The page now states these limits and identifies the dated validated model baseline.

## Actual-model illustration revision

- The mechanical metaphors obscured the actual technology. The updated picture represents Whisper audio features/transcription, Gemma learned weights/token generation, and Piper pronunciation/neural waveform synthesis on one Jetson cutaway.
- The earlier Qwen/eSpeak labels no longer matched the current runtime lock. The preview now identifies Whisper tiny.en F16, Gemma 4 E2B Q4_K_M, and Piper 1.8.0 / LJ Speech medium. The current deployment record became available during the revision and reports service activation; physical voice acceptance remains pending.
- The old timing comparison could incorrectly imply Gemma/Piper latency. It was removed from the current-stack presentation; configuration limits and a link to the current deployment record replace it.
- The first illustrated version only supported scroll/step selection. The revision adds explicit animation/pause, keyboard scrubbing, three consistently propagated authored examples, and an optional runtime-detail view. None invokes live inference or audio recording.

## Simplification after visual review

- The example customization and exploration toolbar added too much UI to the illustration. Removed all toolbar controls and their code, keeping one fixed France question with scroll/chapter navigation. Model/runtime detail content remains below the illustration.

## README.md — widget motion revision

No drift detected. Replaced the traveling signal dot with stage-specific, two-cycle widget wiggles. The original art is composed through SVG masks and clips; the board and person remain stationary. Reduced-motion preferences disable the new animations. Desktop and phone checks confirm stage mapping and no page overflow. Local preview only; owner visual review remains pending.
