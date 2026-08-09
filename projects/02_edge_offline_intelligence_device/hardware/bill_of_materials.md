# Bill of Materials

**Last updated:** August 9 2026
**Status:** Nothing ordered. This is a purchase plan, not an inventory.

## How to read the prices

Prices below were gathered from public product listings and coverage in August 2026. Several vendor pages could not be opened directly from the environment where this list was compiled, so **every price is indicative and must be confirmed at checkout**. Where a figure comes from a single listing it is marked as such. Nothing here is a quotation.

Availability of Jetson modules moves quickly and regional pricing varies widely. Check the vendor's own page before assuming a reseller price.

## Tier 1 — order now to start Experiment 02.1

These four lines are everything the first experiment needs. Together they are sufficient to build the complete offline voice loop on mains power and produce the latency, memory, energy, and offline-integrity baseline.

### 1. Compute — reComputer Super J4012 (Jetson Orin NX 16 GB Super)

The chosen high-end compute tier. Orin NX 16 GB module on the J401 carrier, with fan, enclosure, WiFi, and a 128 GB NVMe SSD carrying a preinstalled JetPack image.

- Seeed Studio: <https://www.seeedstudio.com/reComputer-Super-J4012-p-6443.html>
- Amazon: <https://www.amazon.com/reComputer-Super-J4012-Advanced-Computer/dp/B0FMD89R47>
- Indicative price: about **$1,500** from a single listing seen in August 2026. Confirm this before ordering — the previous non-Super J4012 launched at $899, so the gap between variants is large enough to be worth a minute of checking.

Why this variant rather than the alternatives:

| Variant | Note | Link |
| --- | --- | --- |
| **Super J4012** | Super mode, up to 157 TOPS, full port set, known thermal solution. Recommended for Phase 1 desk work. | [Seeed](https://www.seeedstudio.com/reComputer-Super-J4012-p-6443.html) |
| Mini J4012 | 63 × 95 × 66.7 mm with fan and enclosure — genuinely close to the target object size, and the likely Phase 4 enclosure target. Lower TOPS ceiling. | [Seeed](https://www.seeedstudio.com/reComputer-Mini-J4012-p-6355.html) |
| J4012 (non-Super) | Super mode not supported. Cheaper, and adequate if the measured power ceiling turns out to matter more than peak throughput. | [Seeed](https://www.seeedstudio.com/reComputer-J4012-p-5586.html) |
| Industrial J4012 | Fanless, wide temperature. Silent operation is attractive for a bedside object, but it is larger and more expensive. | [Seeed](https://www.seeedstudio.com/reComputer-Industrial-J4012-p-5684.html) |

Buy one, not two. The Mini becomes interesting only once Experiment 02.1 has produced a power and thermal profile to size an enclosure against, and the fanless Industrial variant only if fan noise turns out to be the thing that ruins the object.

Useful references for setup:

- J401 carrier datasheet: <https://files.seeedstudio.com/wiki/reComputer-J4012/Carrier-Board-J401/J401-datasheet.pdf>
- Flashing JetPack to the J401: <https://wiki.seeedstudio.com/reComputer_J4012_Flash_Jetpack/>

### 2. Reference audio — ReSpeaker XVF3800 USB 4-Mic Array

This is the measuring instrument for Experiment 02.1, not the audio design of the finished device. It is a USB audio class device, so it appears as a normal sound card on a Linux host with no firmware work, and it carries beamforming, noise suppression, and acoustic echo cancellation in hardware.

Using a known-good audio path keeps the latency measurement clean. Any unexplained delay belongs to the pipeline rather than to a bring-up problem.

- With case: <https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-4-Mic-Array-With-Case-p-6490.html> — about **$53.90**
- Bare board: <https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-Mic-Array-p-6488.html> — about **$49.99**
- Amazon: <https://www.amazon.com/seeed-studio-4-Microphone-Processing-Cancellation/dp/B0GVJ5YQ58>

Order the cased version. The case costs a few dollars and protects a board that will be handled repeatedly during measurement.

Confirm before ordering: whether the variant you choose provides speaker output as well as capture. If it does not, add a small powered USB or 3.5 mm speaker to this line — playback is half of the loop being measured.

### 3. Storage — 1 TB NVMe M.2 2280 SSD

The bundled 128 GB SSD holds the operating system and a JetPack image, and it will be uncomfortable once several quantized models, containers, and speech models are present. The J401 carrier takes an M.2 Key M 2280 drive.

- Any mainstream 1 TB M.2 2280 NVMe drive is fine. Samsung 990 EVO and WD Blue SN580 are common, well-supported choices.
- Indicative price: **$60 to $90**.

Optional for the first experiment if disciplined about what is installed, but cheap insurance against a mid-experiment disk-space failure.

### 4. Press-and-hold control

Experiment 02.1 needs a button whose press and release can be timestamped. Use a momentary tactile switch on the 40-pin header, or a single USB footswitch.

- Indicative price: **$5 to $25**.

Do not use the Atom VoiceS3R button for this. See the note below.

## Tier 2 — order alongside, needed for Phase 2 and later

### 5. M5Stack Atom VoiceS3R

The candidate tiny audio front end for the finished object: MEMS microphone, ES8311 codec, Class D amplifier, 1 W 8 Ω speaker, and a button, in roughly 24 × 24 × 17 mm.

- M5Stack store: <https://shop.m5stack.com/products/atom-echos3r-smart-speaker-dev-kit>
- Amazon: <https://www.amazon.com/M5Stack-VoiceS3R-ESP32-S3-Microphone-Amplifier/dp/B0GZDJVP9S>
- The Pi Hut: <https://thepihut.com/products/atom-echos3r-smart-speaker-dev-kit>
- Documentation: <https://docs.m5stack.com/en/core/Atom_EchoS3R>
- Indicative price: **$15 to $25**.

**Read this before planning around it.** The design direction asks whether this module can operate as a direct USB audio device attached to the Jetson. Public specifications describe an ESP32-S3 with an I2S codec — that is, a self-contained microcontroller with audio attached to *it*, not a USB sound card. The ESP32-S3 does have USB OTG capability, so USB audio class firmware is plausible, but it is firmware work rather than a cable.

Three options exist, and Phase 2 should choose between them with measurements:

1. Flash USB audio class firmware so the module enumerates as a sound card on the Jetson.
2. Wire the codec's I2S lines directly to the Jetson header and bypass the ESP32-S3 entirely.
3. Keep the ESP32-S3 as the audio endpoint and stream over WiFi — rejected, because it breaks the offline single-device boundary that is the entire point of the project.

Order it now because it is inexpensive and the bring-up question is worth answering early. Do not put it on the critical path of Experiment 02.1.

### 6. Audio fallback — accept only after measurement

If the tiny module proves unusable, the XVF3800 bought in Tier 1 already is the fallback the design direction names. No additional purchase required. This is a small, deliberate benefit of using it as the reference instrument.

## Tier 3 — do not order yet

Wait for Experiment 02.1 to publish `idle_power` and `energy_per_interaction`. Buying a battery before those numbers exist means guessing at capacity.

### 7. Portable power

The J401 carrier accepts **9–19 V DC through a 5.5/2.5 mm barrel jack**, with configurable power modes typically cited from 10 W to 40 W. That range is convenient: a USB-C Power Delivery battery bank plus a PD trigger cable set to 12 V or 15 V lands inside the accepted input window.

Planned line items once sized:

1. A certified USB-C PD battery bank rated well above the measured peak, with 100 W class output.
2. A USB-C PD trigger cable terminating in a 5.5/2.5 mm barrel plug, fixed at 12 V or 15 V.
3. A USB power meter for validating draw under peak inference load.

The design direction is explicit that the prototype uses a certified pack and a commercial regulated power path rather than loose lithium cells. That constraint holds.

Peak inference load must be validated before the device is described as portable. A bank that sags under a short peak will reboot the Jetson mid-answer, which is the failure most likely to be misdiagnosed as a software fault.

### 8. Enclosure, thermal, and finishing

Nothing until Phase 4. Enclosure geometry depends on measured surface temperature and fan behavior, and the acoustic chamber depends on the speaker that survives Phase 2.

## Measurement instruments

Small, and they make the difference between a result and an anecdote.

| Item | Purpose | Indicative price |
| --- | --- | --- |
| Infrared thermometer | Surface temperature against the 45 °C ruin boundary | $20 to $40 |
| USB power meter | Independent check on input power under load | $15 to $30 |
| Handheld recorder or phone | One-time acoustic offset calibration for the latency ledger | already owned |
| Sound level meter or phone app | Defining the noise level in the stress block | already owned |

## Indicative total

| Tier | Contents | Indicative |
| --- | --- | --- |
| 1 | Compute, reference audio, SSD, button | about **$1,620 to $1,675** |
| 2 | Atom VoiceS3R | about **$20** |
| Instruments | Thermometer, power meter | about **$35 to $70** |
| **To start Experiment 02.1** | Tier 1 plus instruments | **about $1,675 to $1,765** |
| 3 | Battery path, enclosure | deferred until measured |

The compute module dominates the cost by an order of magnitude. That is the strongest practical reason for Experiment 02.1 to report honestly on whether residency — and therefore 16 GB — was needed.

## Sources

- [reComputer Super J4012, Seeed Studio](https://www.seeedstudio.com/reComputer-Super-J4012-p-6443.html)
- [reComputer Super J4012, Amazon](https://www.amazon.com/reComputer-Super-J4012-Advanced-Computer/dp/B0FMD89R47)
- [reComputer Mini J4012, Seeed Studio](https://www.seeedstudio.com/reComputer-Mini-J4012-p-6355.html)
- [reComputer J4012 non-Super, Seeed Studio](https://www.seeedstudio.com/reComputer-J4012-p-5586.html)
- [reComputer Industrial J4012, Seeed Studio](https://www.seeedstudio.com/reComputer-Industrial-J4012-p-5684.html)
- [J401 carrier board datasheet](https://files.seeedstudio.com/wiki/reComputer-J4012/Carrier-Board-J401/J401-datasheet.pdf)
- [Flashing JetPack to the J401](https://wiki.seeedstudio.com/reComputer_J4012_Flash_Jetpack/)
- [ReSpeaker XVF3800 USB 4-Mic Array with case](https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-4-Mic-Array-With-Case-p-6490.html)
- [ReSpeaker XVF3800 USB Mic Array](https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-Mic-Array-p-6488.html)
- [ReSpeaker XVF3800 coverage, CNX Software](https://www.cnx-software.com/2025/07/29/respeaker-xmos-xvf3800-4-mic-array-board-features-esp32-s3-module-works-over-usb/)
- [Atom VoiceS3R, M5Stack store](https://shop.m5stack.com/products/atom-echos3r-smart-speaker-dev-kit)
- [Atom VoiceS3R documentation](https://docs.m5stack.com/en/core/Atom_EchoS3R)
- [Atom VoiceS3R, Amazon](https://www.amazon.com/M5Stack-VoiceS3R-ESP32-S3-Microphone-Amplifier/dp/B0GZDJVP9S)
