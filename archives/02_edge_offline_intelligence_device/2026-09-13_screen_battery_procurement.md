> **Archived September 13, 2026.** This sourcing proposal was superseded before purchase when the first hardware stage was narrowed to a mains-powered button-and-voice prototype. The screen and battery design below is historical, not a current shopping instruction.
>
> **Conclusion and missing evidence:** Supplier research produced a provisional plan, but no order, physical assembly, Jetson measurement, or battery result followed from this proposal. Its two-hour target was not demonstrated.

# Portable Jetson procurement brief

**Updated:** September 13, 2026; supplier pages checked September 12–13, 2026.
**Status:** Sourcing proposal. No order, reservation, or new expenditure recorded.
**Tracking:** [Portable hardware issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47).
**Evidence:** Zero Jetson runs or published comparative measurements. Prices and listed stock are observations; compatibility, useful answers, and battery life are unmeasured.

## Agreed scope and purchase decision

The next iteration is a small carryable box with its own screen, microphone, speaker, storage, and battery. Target about two hours per charge. All accessories must be acquired; only the existing development Mac and iPhone are reused. English, one question at a time, visible transcript and answer, and manual Read aloud remain the interaction. There is no web, document, or vector retrieval and no conversation history.

Recommend the **official NVIDIA Jetson Orin Nano Super Developer Kit, 8 GB**, at the **$399** price. Its memory is shared by the operating system, CPU, GPU, and models. Start with a compact quantized answer model and bounded context; this is not a promise to run every small model. The 16 GB alternative is Orin NX, a different tier. NVIDIA's current FAQ lists the Nano Super kit at $399 and the NX 16 GB module alone at $999 at volume pricing, before its carrier and accessories. [NVIDIA pricing and product FAQ](https://developer.nvidia.com/embedded/faq).

The complete planning amount is **$952.46**, leaving **$47.54** inside the $1,000 first-year ceiling. This combines observed prices with explicitly marked allowances. It is **not a delivered checkout quote** and is not ready for payment: compute fulfillment, the remaining accessory quotes, enclosure fit, and final tax/shipping must be resolved first. Keep a $99 Apple distribution renewal reserve and plan for $0 paid inference subscriptions.

## Compute availability

| Supplier and exact product | Observed price | Availability and disposition |
| --- | ---: | --- |
| [SparkFun DEV-22098](https://www.sparkfun.com/nvidia-jetson-orin-nano-developer-kit.html), official Nano Super kit | $399.00 | Backorder. Recommended price target, with no confirmed shipping date. Do not imply that it can ship immediately. |
| [Micro Center, official Nano Super kit](https://www.microcenter.com/product/691058/nvidia-jetson-orin-nano-super-developer-kit?storeid=185) | $399.00 | Miami listing showed stock, in-store pickup only. Requires an owner-approved pickup arrangement; travel or forwarding costs are not included in the base plan. |
| [Seeed official kit bundle, E26041601](https://www.seeedstudio.com/NVIDIAr-Jetson-Orintm-Nano-Super-Developer-Kit-Bundle.html) | $450.30 displayed bundle | Live page showed backorder with an estimated ship date of November 17, 2026. The advertised antenna discount was not applied. This substitution would raise the current plan to $1,003.76 before any reserve change. |
| [Amazon listing B0BZJTQ5YP](https://www.amazon.com/dp/B0BZJTQ5YP) | $577.99 lowest new offer inspected | Sold and shipped by WeShipTech, with a September delivery estimate. The same listing showed a $500 used/open-box offer. Neither is the $399 target; the new offer raises this plan to $1,131.45. Neither was added to cart. |

Recommendation: retain the $399 target while resolving a shipping or pickup route. No restock date is promised and no automatic monitoring or future purchase has been scheduled. Do not buy the peripherals substantially before the compute delivery is settled, so their return windows remain useful for integration checks.

## Complete cost plan

USD, quantity one unless stated otherwise. **Listed** means the vendor displayed the price and a purchase/stock state; it does not mean checkout or delivery has been verified. **Allowance** means the exact purchasable part or assembly is still to be quoted.

| Item | Part / supplier | Amount | Quote status and included items |
| --- | --- | ---: | --- |
| Compute, carrier, cooling, mains power | Official Nano Super 8 GB kit, NVIDIA 945-13766-0000-000 / SparkFun DEV-22098 | $399.00 | Listed; backorder. Includes module, carrier, heatsink/fan, Wi-Fi module, and mains supply. Verify US cord in the chosen seller's package. |
| Five-inch touchscreen | [Waveshare 5inch HDMI LCD (H), SKU 14300](https://www.waveshare.com/product/5inch-hdmi-lcd-h.htm) | $52.99 | Listed; Add to Cart available. 800×480, HDMI video and USB capacitive touch. Package includes HDMI cable, USB-A to micro-B cable, micro-HDMI adapter, and four mounting screws. No enclosure. |
| Display adapter | [Cable Matters active DisplayPort-to-HDMI, 102021](https://www.cablematters.com/pc-624-154-active-displayport-to-hdmi-adapter-4k-ready.aspx) | $17.99 | Catalog price; fulfillment needs confirmation. Full-size DisplayPort input, HDMI output. Use the screen's HDMI cable. |
| Battery | [INIU P63-E1, black, 25,000 mAh / 100 W](https://iniushop.com/products/iniu-p63-e1-power-bank-smallest-100w-25000mah) | $66.99 | Listed; selected black variant available. Includes a detachable 100 W USB-C cable. Checkout coupon excluded from the budget. |
| Battery charger | [INIU A11-E1, US / black / one pack](https://iniushop.com/products/iniu-a11-e1-100w-gan-charger-usb-c) | $32.99 | Store catalog confirmed available, SKU D01-A11-E1-US-BK. Use one USB-C output to recharge the battery. |
| Battery-to-Jetson cable | [Adafruit 5451 at DigiKey](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5451/16592510) | $7.95 | Listed in stock. Fixed 15 V USB-C PD request, 5.5×2.5 mm center-positive barrel. Direct Adafruit stock was unavailable. |
| Microphone | [Adafruit Mini USB Microphone, 3367](https://www.adafruit.com/product/3367) | $5.95 | Listed in stock. Mount on an extension away from fan exhaust; recognition quality remains to be tested. |
| Speaker | [Adafruit Mini External USB Stereo Speaker, 3369](https://www.adafruit.com/product/3369) | $12.50 | Listed in stock. USB audio and power; avoids a separate analog audio adapter. |
| Boot and model storage | [SANDISK Extreme 128 GB A2 microSDXC, SDSQXH9-128G-GZ6MA, B&H](https://www.bhphotovideo.com/c/product/1948572-REG/sandisk_sdsqxh9_128g_gz6ma_128gb_extreme_uhs_i_microsdxc.html/overview) | $40.25 | Live product page showed In Stock and free shipping. Older indexed prices differed; recheck checkout. NVMe is deferred. |
| Mac card reader | [Adafruit USB-C microSD reader, 5212](https://www.adafruit.com/product/5212) | $6.95 | Listed in stock. Included because an existing reader is not assumed. |
| Setup keyboard | [Adafruit wired mini keyboard, 1736](https://www.adafruit.com/product/1736) | $9.95 | Listed in stock. Needed for firmware/setup and recovery, not carried in normal voice use. |
| Setup mouse | [Adafruit wired mouse, 2025](https://www.adafruit.com/product/2025) | $4.95 | Listed in stock. Disconnect after touchscreen setup. |
| Short USB extension and miscellaneous cable needs | Exact lengths selected after layout | $10.00 | Allowance. Prioritize microphone placement and strain relief; do not duplicate included screen cables. |
| Protective enclosure, screen mount, battery restraint, assembly materials and basic tools | Vented carryable assembly; final part/drawing open | $60.00 | Allowance, not a verified off-the-shelf complete case. Must cover protected circuit boards, screen bezel/stand, fasteners/standoffs, straps and required hand tools. No purchased 3D printer assumed. |
| USB-C PD voltage/current/energy meter | At least 20 V / 5 A and PD pass-through; exact model open | $25.00 | Allowance for voltage confirmation and device energy checks. Record accuracy and meter overhead; not a calibrated laboratory instrument by default. |
| **All physical parts and development accessories** | | **$753.46** | Includes $95 in unquoted cable/assembly/meter allowances. |
| Apple Developer first-year renewal reserve | [Apple membership](https://developer.apple.com/programs/whats-included/) | $99.00 | Budget reserve, not an additional payment made here. |
| Required paid local-inference subscriptions | None planned | $0.00 | Check the selected model/runtime licenses before packaging. |
| Tax, standard shipping, and any import charges | Exact checkout totals pending | $100.00 | Allowance, not a tax calculation. Reduce purchases if delivered costs exceed the remaining ceiling. |
| **Planned first-year use of budget** | | **$952.46** | Quoted prices plus allowances and fee reserve. |
| **Remaining contingency** | | **$47.54** | Price changes, replacement parts, or microphone improvement must fit here or replace another line. |
| **First-year total ceiling** | | **$1,000.00** | All new spending combined. |

No battery, storage, screen, audio, charger, reader, assembly tool, or measurement accessory is assumed to be already owned. No recurring cloud service, premium shipping, protection plan, or optional subscription is included. This plan covers one experimental prototype; it does not fund a production manufacturing run or commercial product certification.

## Electrical and mechanical compatibility

The official carrier specification gives a **9–20 V DC jack input**. The mating plug is **5.5 mm outside / 2.5 mm inside, center positive**. Use the fixed **15 V** cable, with the battery's documented **15 V / 3 A** profile. This provides at most **45 W at that profile**, even though the battery advertises 100 W at 20 V and the cable is rated for 5 A. Do not substitute a 20 V trigger cable or power the kit through its data-only USB-C port. [NVIDIA carrier specification, section 3.8](https://developer.nvidia.com/downloads/assets/embedded/secure/jetson/orin_nano/docs/jetson_orin_nano_devkit_carrier_board_specification_sp.pdf), [Adafruit 5451 specifications](https://www.adafruit.com/product/5451), [INIU output profiles](https://iniushop.com/products/iniu-p63-e1-power-bank-smallest-100w-25000mah).

```text
Battery USB-C → PD meter → fixed 15 V barrel cable → Jetson DC input
Jetson DisplayPort → active DP-to-HDMI adapter → touchscreen HDMI
Jetson USB-A → touchscreen USB power/touch
Jetson USB-A → microphone extension → USB microphone
Jetson USB-A → USB speaker
```

Use the included mains adapter first. Connect peripherals before applying power. For portable testing, dedicate one battery USB-C output to the Jetson; power the screen and audio from the Jetson so the meter covers the complete operating device. Do not assume uninterrupted operation when connecting a charger or changing battery port loads. Shut down before changing the power arrangement. [NVIDIA hardware layout](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/hardware_layout.html).

The kit exposes DisplayPort, not HDMI video or USB-C display output. NVIDIA supports DP-to-HDMI adapters. The screen uses standard HDMI and USB, but its vendor's Jetson example is the older Nano: exact Orin/JetPack touch and display compatibility is still an integration check. Verify screen USB demand against the carrier's port limits. During setup, connect keyboard/mouse and screen first; after shutdown, disconnect setup peripherals before installing all audio accessories.

Retain the supplied fan/heatsink. The assembled developer kit is about 103×90.5×34.77 mm; the candidate battery is 110×70×36 mm. These are component dimensions, not a finished case drawing. Provide airflow, connector bend clearance, an accessible battery indicator, a protected screen, and strain relief. The battery and screen need secure mounts independent of their cables. The enclosure remains a sourcing/design gate; a case fitting only the Jetson board is not a complete portable device.

## Battery target and limits

Two hours is a **target**, not a vendor-backed runtime for this build. As an illustrative calculation, 25 Ah at an assumed 3.6 V nominal cell voltage is 90 Wh. With 80% usable energy after reserve and losses, that leaves about 72 Wh. Verify the purchased battery's actual Wh label and measure delivered energy; mAh alone is not a device runtime specification.

| Assumed whole-device average draw | Illustrative runtime from 72 Wh |
| --- | ---: |
| 25 W | 2.88 hours |
| 30 W | 2.40 hours |
| 35 W | 2.06 hours |
| 40 W | 1.80 hours |

Begin with the Jetson's 15 W module mode and a moderate screen brightness. That setting excludes carrier, screen, audio, storage, and conversion costs. Keeping the complete average near or below 30 W would give the two-hour target some margin. Peak draw must also remain within the 15 V / 3 A power path. No latency, peak-load, thermal, or battery result is implied by this calculation.

## Software setup and portability

Apple's recognition, answer model, and installed Premium voices cannot be copied to Jetson. Preserve the interaction contract, prompt policy, cancellation, and evaluation cases; implement Linux audio/UI and local open-model backends. Start evaluation within roughly the 1–2B quantized answer-model band already listed in the [architecture](https://github.com/raghavan/longtail-inference-lab/blob/322c70f6ec1459bec2896720b8e37e25ceb7f9db/projects/02_edge_offline_intelligence_device/design_direction.md), with a compact English transcriber and local speech synthesizer. Exact weights, quantization, runtime revision, context, and voice must be selected and recorded before measured runs. Naturalness is a listening result, not a property established by buying a speaker or GPU.

Use an official Orin Nano SD-image installation path for initial bring-up. NVIDIA's [JetPack 6.2.1 installation guide](https://docs.nvidia.com/jetson/jetpack/6.2.1/install-setup/index.html) documents the SD route and requires a firmware update for factory JetPack 5.x units before booting 6.x. Its SDK Manager route requires an Ubuntu x64 host; that is not an existing asset assumed by this budget. Inspect factory firmware and follow the official host-free SD update path where supported. NVIDIA's [current quick-start guide](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/quick_start.html) also describes the newer JetPack 7.2.1 USB installation route after 6.x firmware. Final JetPack/runtime qualification remains open; do not silently budget a new flashing computer or boot device.

Initial OS, model, and voice downloads need connectivity. After setup, inference must work without Wi-Fi, Ethernet, a phone, or a hosted API. Missing assets should produce a visible error instead of a cloud fallback. The iOS beta continues to use its current Apple backend; this procurement does not establish common model weights across Apple and NVIDIA.

## Bring-up and acceptance plan

**Bounded question:** Can this complete 8 GB device deliver useful short English spoken questions and optional spoken replies, with its own screen and about two hours of battery operation, within the first-year ceiling?

1. **Before payment:** settle the compute fulfillment route; turn the remaining allowances into priced items; verify the US mains cord, battery Wh label, charger/cable profiles, enclosure clearances, and the complete delivered total. Keep private fulfillment details out of public records. Record the order only after checkout succeeds.
2. **Mains bring-up:** inspect parts and factory firmware; install the selected official software; confirm readable text, touch controls, microphone capture, and speaker output. Run a typed question first, then a spoken question and manual read-aloud. Record development checks separately from scored results.
3. **Freeze the operating test:** record exact model/voice/runtime artifacts, prompt and context bounds, power mode, screen brightness, memory use, temperature, and meter specification. Use deliberately authored or approved English cases. Agree usefulness and acceptable delay before scoring answers.
4. **Offline and battery run:** after setup downloads, disconnect external networks and test the full interaction. Proposed battery workload: one question of up to 15 seconds every two minutes, up to 128 answer tokens, manual read-aloud once per answer, screen on at fixed 50% brightness for 120 minutes. This is a proposed duty cycle, not a measured result or a continuous-generation guarantee. Include idle draw, failures, and shutdown reserve.
5. **Package and repeat:** fit the protected, ventilated assembly; repeat audio, latency, peak-power, and battery checks in the actual enclosure. A bench result does not qualify the enclosed unit. Publish sanitized results and total cost; keep raw voice and private questions out of the repository.

Stop or narrow the approach if the full delivered quote exceeds $1,000, the power path resets or exceeds its rating, thermal or memory failures persist, offline use requires a server, or useful answers cannot be achieved in the available memory. A failed two-hour test means adjusting model load, duty cycle, screen draw, or battery design within budget; it does not justify claiming the target was met. Completion requires dated device measurements and a cost ledger, not just purchased parts.
