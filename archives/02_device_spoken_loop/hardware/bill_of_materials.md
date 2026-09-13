# Bill of Materials

**Last updated:** August 9 2026
**Status:** Nothing ordered. This is a purchase plan, not an inventory.
**Ceiling:** $500 for everything needed to begin Experiment 02.1.

## Order of operations

Nothing here is bought until the [laptop pilot](../software/README.md) has run the complete loop end to end. The pilot costs nothing, uses the same controller and analysis that the device will use, and answers whether the interaction is worth building hardware around.

## How to read the prices

Prices were gathered from public listings in August 2026. Several vendor pages could not be opened from the environment where this list was compiled, so **every price is indicative and must be confirmed at checkout**. Regional pricing and Jetson availability both move quickly.

## Tier 1 — the $500 build

These six lines are everything Experiment 02.1 needs: the complete offline voice loop on mains power with reference audio, instrumented well enough to publish.

| # | Item | Indicative | Why it is here |
| --- | --- | --- | --- |
| 1 | Jetson Orin Nano Super Developer Kit, 8 GB | **$249** | The compute tier under test |
| 2 | 500 GB NVMe M.2 2280 SSD | **$40** | Not optional; see below |
| 3 | ReSpeaker XVF3800 USB 4-Mic Array with case | **$53.90** | Reference audio instrument |
| 4 | microSD card, 64 GB | **$10** | Flashing and recovery |
| 5 | Momentary tactile switch or USB footswitch | **$5** | Timestampable press-and-hold control |
| 6 | Infrared thermometer | **$25** | Keeps the 45 °C ruin boundary measurable |
| | **Subtotal** | **~$383** | |
| | **With tax and shipping** | **~$443** | leaves roughly $57 of headroom |

### 1. Jetson Orin Nano Super Developer Kit, 8 GB — $249

- NVIDIA: <https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/>
- Amazon: <https://www.amazon.com/NVIDIA-Jetson-Orin-Nano-Developer/dp/B0BZJTQ5YP>
- SparkFun: <https://www.sparkfun.com/nvidia-jetson-orin-nano-developer-kit.html>
- Micro Center: <https://www.microcenter.com/product/691058/nvidia-jetson-orin-nano-super-developer-kit>

Includes the 19 V power adapter, heatsink and fan, and a preinstalled WiFi module. **It includes no storage.**

Two things worth checking before paying:

1. **Price at or near $249.** Meaningfully above that means a reseller listing.
2. **The older Jetson Orin Nano Developer Kit is equally fine.** "Super" is a software update delivered through JetPack, not different silicon, so a cheaper original kit reaches the same performance. Record which one you bought either way, because the JetPack version is a fixed control.

Some storefront links sit under NVIDIA's enterprise or robotics-edge sections and route to distributor quotes rather than a normal cart. If a page asks for company details, buy from one of the retail links above instead.

### 2. 500 GB NVMe M.2 2280 SSD — ~$40

**Do not substitute a microSD card for this.** Model load time is a measured stage in the latency ledger, and the `stt_load` and `llm_load` stages are exactly where the sequential condition spends its time. Running the experiment from slow storage would not merely be slower; it would confound the primary comparison.

Any mainstream M.2 2280 drive works. Samsung 990 EVO and WD Blue SN580 are common choices.

### 3. ReSpeaker XVF3800 USB 4-Mic Array with case — $53.90

- With case: <https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-4-Mic-Array-With-Case-p-6490.html>
- Bare board: <https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-Mic-Array-p-6488.html> — $49.99
- Amazon: <https://www.amazon.com/seeed-studio-4-Microphone-Processing-Cancellation/dp/B0GVJ5YQ58>

A USB audio class device, so it appears as a normal sound card with no firmware work. Using a known-good audio path keeps the latency measurement clean: any unexplained delay belongs to the pipeline rather than to a bring-up problem. It also doubles as the audio fallback the design direction already names, so it is not a throwaway purchase.

Confirm the variant provides speaker output as well as capture. If it does not, add a small powered speaker — playback is half of the loop being measured.

### 6. Infrared thermometer — ~$25

Surface temperature is a ruin boundary, and the device has no sensor for it. A USB power meter was considered and dropped: the Jetson carries onboard rail sensing that `tegrastats` already reports, making the meter a cross-check rather than an instrument.

## Tier 2 — cheap, and worth having early

| Item | Indicative | Link |
| --- | --- | --- |
| M5Stack Atom VoiceS3R | **$15–25** | [M5Stack](https://shop.m5stack.com/products/atom-echos3r-smart-speaker-dev-kit) · [Amazon](https://www.amazon.com/M5Stack-VoiceS3R-ESP32-S3-Microphone-Amplifier/dp/B0GZDJVP9S) · [Pi Hut](https://thepihut.com/products/atom-echos3r-smart-speaker-dev-kit) · [docs](https://docs.m5stack.com/en/core/Atom_EchoS3R) |

The candidate tiny audio front end for the finished object: MEMS microphone, ES8311 codec, Class D amplifier, 1 W 8 Ω speaker, and a button in roughly 24 × 24 × 17 mm.

**Read this before planning around it.** The design direction asks whether it can attach as a direct USB audio device. Public specifications describe an ESP32-S3 with an I2S codec — a microcontroller with audio attached to *it*, not a USB sound card. Three options exist, and Phase 2 chooses between them with measurements:

1. Flash USB audio class firmware so it enumerates as a sound card on the Jetson.
2. Wire the codec's I2S lines directly to the Jetson header, bypassing the ESP32-S3.
3. Stream over WiFi — rejected, because it breaks the offline single-device boundary that is the point of the project.

Buy it now because it is inexpensive and the bring-up question is worth answering early. Keep it off the critical path of Experiment 02.1.

Adding it brings the total to roughly **$465** after tax and shipping, still inside the ceiling.

## Tier 3 — do not order yet

Deferred until Experiment 02.1 publishes `idle_power` and `energy_per_interaction`. Buying a battery before those exist is guessing at capacity.

### Portable power

The Orin Nano Super Developer Kit ships with a 19 V adapter and expects a dedicated power input, so the battery path must be validated under peak inference load before the device is called portable. Planned lines once sized: a certified USB-C PD battery bank rated well above measured peak, a PD trigger cable at a voltage the carrier accepts, and a USB power meter for validating draw.

The design direction is explicit that the prototype uses a certified pack and a commercial regulated power path rather than loose lithium cells. That constraint holds.

### Enclosure, thermal, and finishing

Nothing until Phase 4. Enclosure geometry depends on measured surface temperature and fan behaviour, and the acoustic chamber depends on whichever speaker survives Phase 2.

Note that the developer kit is physically larger than the target object, so the enclosure phase will need either a compact carrier or a different form than the design direction's "thick deck of cards" sketch. That is a Phase 4 problem and is not funded under this ceiling.

## If 8 GB proves insufficient

Experiment 02.1 requires at least 1.0 GB of headroom under peak load in the resident condition. If that fails, the upgrade path is the Orin NX 16 GB on a compact carrier — and at that point it is justified by a measurement rather than by anticipation.

| Variant | Note | Link |
| --- | --- | --- |
| reComputer Super J4012 | Orin NX 16 GB Super, ~157 TOPS, full ports. ~$1,503 in one listing — verify, since the non-Super launched at $899. | [Seeed](https://www.seeedstudio.com/reComputer-Super-J4012-p-6443.html) |
| reComputer Mini J4012 | 63 × 95 × 66.7 mm with fan and enclosure — closest to the target object size. | [Seeed](https://www.seeedstudio.com/reComputer-Mini-J4012-p-6355.html) |
| reComputer J4012 | Super mode not supported. Cheaper. | [Seeed](https://www.seeedstudio.com/reComputer-J4012-p-5586.html) |

Useful references either way:

- J401 carrier datasheet, including the 9–19 V input range: <https://files.seeedstudio.com/wiki/reComputer-J4012/Carrier-Board-J401/J401-datasheet.pdf>
- Flashing JetPack to the J401: <https://wiki.seeedstudio.com/reComputer_J4012_Flash_Jetpack/>

## Sources

- [Jetson Orin Nano Super Developer Kit, NVIDIA](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/)
- [Jetson Orin Nano Developer Kit gets a Super boost, NVIDIA Technical Blog](https://developer.nvidia.com/blog/nvidia-jetson-orin-nano-developer-kit-gets-a-super-boost/)
- [$249 Jetson Orin Nano Super Developer Kit, JetsonHacks](https://jetsonhacks.com/2024/12/17/jetson-orin-nano-super-developer-kit/)
- [ReSpeaker XVF3800 USB 4-Mic Array with case, Seeed Studio](https://www.seeedstudio.com/ReSpeaker-XVF3800-USB-4-Mic-Array-With-Case-p-6490.html)
- [ReSpeaker XVF3800 coverage, CNX Software](https://www.cnx-software.com/2025/07/29/respeaker-xmos-xvf3800-4-mic-array-board-features-esp32-s3-module-works-over-usb/)
- [Atom VoiceS3R documentation, M5Stack](https://docs.m5stack.com/en/core/Atom_EchoS3R)
- [reComputer Super J4012, Seeed Studio](https://www.seeedstudio.com/reComputer-Super-J4012-p-6443.html)
