# Jetson order record and arrival checklist

**Recorded:** September 13, 2026

**Status:** All eight first-batch items are ordered: the Arrow Jetson kit, six DigiKey accessories, and one Newegg microSD card. The Arrow confirmation records $428.93 including tax and free shipping, with expected shipment September 14 and delivery September 21, 2026. Actual arrival and device acceptance remain open; DigiKey and Newegg final charges remain pending.

**Tracking:** [Hardware issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47)

**Evidence:** Zero published comparative quality or performance measurements for Mac, iPhone, or Jetson.

## Eight-item parts list

**One of each item is ordered. Do not purchase these eight items again.** Public product links below identify the selected parts; prices exclude checkout charges, which are recorded separately. The first prototype uses mains power, a microphone, a speaker, and a physical listening button. Screen, battery, enclosure, and NVMe storage are deferred.

| Store | Item and purchase link | Purpose | Listed price |
| --- | --- | --- | ---: |
| Arrow | [NVIDIA Jetson Orin Nano Super Developer Kit, 8 GB](https://www.arrow.com/en/products/945-13766-0000-000/nvidia.html), NVIDIA 945-13766-0000-000 | Complete compute kit, including carrier, cooling, Wi-Fi/Bluetooth, mains adapter, and US power cord | $399.00 |
| DigiKey | [Adafruit Mini USB Microphone, 3367](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3367/6623861) | Speech input | $5.95 |
| DigiKey | [Adafruit Mini External USB Stereo Speaker, 3369](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3369/6623862) | Spoken replies; USB supplies audio and power | $12.50 |
| DigiKey | [M5Stack AtomS3-Lite, C124](https://www.digikey.com/en/products/detail/m5stack-technology-co-ltd/C124/18070571) | Physical button and status light; requires programming | $8.00 |
| DigiKey | [Adafruit USB-C microSD reader, 5212](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5212/15761513) | Write the system card using the existing Mac | $6.95 |
| DigiKey | [Adafruit USB-C to USB-C data cable, 4199](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4199/10230016) | Mac-to-Jetson setup/console connection | $9.95 |
| DigiKey | [Adafruit USB-A to USB-C data cable, 4474](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4474/11587355) | Connect the button to the Jetson | $4.95 |
| Newegg | [SanDisk Extreme 128 GB A2 UHS-I microSDXC](https://www.newegg.com/sandisk-2tb-microsd-a2-v30/p/N82E16820173727), SDSQXH9-128G-GZ6MA | System, applications, and model storage; select this exact 128 GB SKU | $42.99 |
| | **Arrow $399.00 + DigiKey $48.30 + Newegg $42.99** | **Parts subtotal; checkout charges excluded** | **$490.29** |

### Orders and expected fulfillment

- **Arrow: ordered on September 13.** The supplied order confirmation matches one NVIDIA 945-13766-0000-000 complete US-region Orin Nano Super developer kit. The item is $399.00, tax $29.93, shipping free, and no tariff amount is listed, giving a confirmed order total of **$428.93**. Ground shipment is expected September 14 and delivery September 21, 2026. These are retailer-supplied future dates, not evidence of actual dispatch or arrival. Inspect the included cooling, power supply, and US cord on arrival.
- **DigiKey: ordered, owner-confirmed on September 13.** The supplied item export matches all six part numbers, quantities, and prices above and totals $48.30. It lists each item as Immediate but contains no final order total or shipment confirmation. During checkout, standard shipping was quoted at $4.99 and tariff at $0.45, giving $53.74 before tax; these remain estimates until reconciled with the final receipt. Do not order these accessories again.
- **Newegg: ordered on September 13.** The supplied order summary confirms one SanDisk Extreme 128 GB microSD card, retailer item N82E16820173727, at $42.99, sold and fulfilled by Newegg. The final tax, shipping charge, total, and actual dispatch/delivery status are not visible in the supplied summary. Earlier checkout quoted free shipping; retain that as an estimate until the final total is recorded. The retailer's fulfillment label does not establish dispatch. Do not purchase another card. The order matches the selected 128 GB item despite the product URL's misleading capacity slug.

This public record contains only technical parts, quantities, costs, dates, and progress. Names, contact details, addresses, payment/account details, order/tracking numbers, private URLs, raw receipts, and screenshots stay outside GitHub. See the [public memory policy](../../../areas/lab_operations/public_research_memory.md).

## Memory and the first interaction

The **8 GB working memory is included** in the Jetson and shared by the CPU, GPU, and operating system. It is not a separate RAM purchase or an upgradeable memory stick. The **128 GB microSD card is storage**, not extra working memory. Begin model trials around a **1–3B parameter answer model with 4-bit weights**, alongside compact English transcription and local speech synthesis. Exact models and runtimes remain unselected; each needs a compatibility, memory, quality, and latency check. [NVIDIA hardware reference](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/hardware_layout.html), [NVIDIA FAQ](https://developer.nvidia.com/embedded/faq).

The intended Jetson interaction is:

**Press button → speak → press again to finish → local transcription → local answer using a configurable system prompt → automatic spoken reply → idle.**

The button controls listening while the Jetson stays powered. Use English, one question at a time, with no conversation history, web search, document search, or vector retrieval in this first stage. The AtomS3-Lite supplies an assembled button and light; its USB event handling and the Jetson application still need implementation. [Button hardware documentation](https://docs.m5stack.com/en/core/AtomS3%20Lite).

The working Apple apps use Apple's on-device answer backend, not a selected downloadable open model. Apple models and installed voices cannot be copied onto Jetson. Keep the Apple apps' current manual **Read aloud** behavior; the dedicated voice-only device will speak its completed answer automatically. Its voice quality must be evaluated after selecting a local synthesizer. See the [architecture decision](../design_direction.md).

## Budget checkpoint

The **first-year ceiling remains $1,000** for all new hardware, required subscriptions and software/distribution fees, tax, shipping, and tariffs. The [budget record](bill_of_materials.md) now records **$520.22 in known order costs**: Arrow's $428.93 total plus DigiKey's $48.30 and Newegg's $42.99 item subtotals. The latter two final totals remain pending. Arrow's confirmed $29.93 tax uses part of the original $100 checkout allowance, leaving $70.07 reserved for the remaining charges. With the possible $99 Apple Developer renewal reserve, **$310.71 remains provisionally unallocated**. These reserves are not additional purchases; do not count the confirmed parts or tax twice. No paid inference subscription is planned.

Battery operation, a portable enclosure, and any screen are later decisions within that same ceiling. Approximately two hours per charge remains an unmeasured future target, not a condition for this first purchase batch.

## Next steps

1. Read this record, [current status](../status.md), and [issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47). All eight items are ordered. Reconcile the DigiKey and Newegg final charges and record actual shipment/delivery as evidence becomes available. Do not repurchase these items or treat expected dates as completed delivery.
2. Confirm the full first-batch total and any renewal due within the first year. On arrival, inspect all eight item identities and quantities, including the kit's cooling, power supply, and US cord. Keep the whole project within $1,000. Publish only sanitized costs, dates, and technical status; keep all PII and raw purchase materials outside GitHub.
3. After arrival, inspect firmware and use a supported official installation path. Start with the supplied mains adapter, the existing Mac, the microSD reader, and USB data console. The Jetson USB-C connection is for data, not mains power. Qualify microphone, speaker, and button connectivity before building the voice loop.
4. Select and record exact transcription, answer, and voice artifacts, licenses, quantization, runtime versions, context/output limits, and the approved test prompt. Implement the button flow and verify a local spoken question and spoken reply. Use deliberately authored evaluation examples; keep private prompts and raw microphone content out of GitHub.
5. After setup downloads, disconnect external networks and test the full voice loop, errors, and cancellation. Agree on usefulness and acceptable waiting time before scoring; record latency, peak memory, failures, and power/thermal conditions separately for Jetson. Revisit battery and enclosure choices after the mains-powered loop works. Purchased parts alone do not establish a working device or measured result.

**Setup dependency to resolve:** [Jetson AI Lab's headless USB setup guide](https://www.jetson-ai-lab.com/tutorials/hackathon-guide/) supports the intended console approach. Factory JetPack 5.x firmware can need an update before a 6.x SD image boots; confirm the applicable [firmware procedure](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/update_firmware.html) and [JetPack installation guide](https://docs.nvidia.com/jetson/jetpack/6.2.1/install-setup/index.html). SDK Manager recovery requires an Ubuntu x64 host, which is not an assumed owned asset. If the received unit requires another host, display, or boot device, resolve that setup cost within the budget before proceeding. OS, model, and voice downloads precede offline operation; missing assets must not trigger a cloud fallback.
