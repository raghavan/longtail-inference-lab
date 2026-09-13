# Jetson shopping list and restart checklist

**Recorded:** September 13, 2026

**Status:** Shopping list ready; purchasing is on hold until the next owner session, planned for next week. No order, payment, or reservation has been completed.

**Tracking:** [Hardware issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47)

**Evidence:** Zero published comparative quality or performance measurements for Mac, iPhone, or Jetson.

## Buy these eight items from three stores

Buy **one of each**. Prices and availability below are September 13 observations, not reserved stock or checkout quotes. Recheck them when resuming. The first prototype uses mains power, a microphone, a speaker, and a physical listening button. Screen, battery, enclosure, and NVMe storage are deferred.

| Store | Item and purchase link | Purpose | Listed price |
| --- | --- | --- | ---: |
| Arrow | [NVIDIA Jetson Orin Nano Super Developer Kit, 8 GB](https://www.arrow.com/en/products/945-13766-0000-000/nvidia.html), NVIDIA 945-13766-0000-000 | Complete compute kit, including carrier, cooling, Wi-Fi/Bluetooth, mains adapter, and US power cord | $399.00 |
| DigiKey | [Adafruit Mini USB Microphone, 3367](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3367/6623861) | Speech input | $5.95 |
| DigiKey | [Adafruit Mini External USB Stereo Speaker, 3369](https://www.digikey.com/en/products/detail/adafruit-industries-llc/3369/6623862) | Spoken replies; USB supplies audio and power | $12.50 |
| DigiKey | [M5Stack AtomS3-Lite, C124](https://www.digikey.com/en/products/detail/m5stack-technology-co-ltd/C124/18070571) | Physical button and status light; requires programming | $8.00 |
| DigiKey | [Adafruit USB-C microSD reader, 5212](https://www.digikey.com/en/products/detail/adafruit-industries-llc/5212/15761513) | Write the system card using the existing Mac | $6.95 |
| DigiKey | [Adafruit USB-C to USB-C data cable, 4199](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4199/10230016) | Mac-to-Jetson setup/console connection | $9.95 |
| DigiKey | [Adafruit USB-A to USB-C data cable, 4474](https://www.digikey.com/en/products/detail/adafruit-industries-llc/4474/11587355) | Connect the button to the Jetson | $4.95 |
| B&H | [SanDisk Extreme 128 GB A2 UHS-I microSDXC](https://www.bhphotovideo.com/c/product/1948572-REG/sandisk_sdsqxh9_128g_gz6ma_128gb_extreme_uhs_i_microsdxc.html/overview), SDSQXH9-128G-GZ6MA | System, applications, and model storage | $40.25 |
| | **Arrow $399.00 + DigiKey $48.30 + B&H $40.25** | **Parts subtotal; checkout charges excluded** | **$487.55** |

### Supplier and checkout checkpoint

- **Arrow is the preferred Jetson source at this checkpoint.** Its product page showed one unit in US stock, and the prepared cart showed quantity one at $399 with an estimated shipment of “Ships tomorrow.” This was a dated estimate, not a delivery promise. Checkout reached account sign-in; payment was not completed. A cart does not reserve inventory and may expire. Confirm the exact complete kit and included US mains cord before payment.
- **DigiKey:** all six listed accessories showed availability. Consolidate them into one order. Final shipping and any tariff charges remain unconfirmed.
- **B&H:** the selected SanDisk card showed in stock with free item shipping. Recheck final tax and delivery charges.
- **Jetson fallback links:** [NVIDIA's direct US store](https://marketplace.nvidia.com/en-us/enterprise/robotics-edge/jetson-orin-nano-super-developer-kit/) showed $399 but out of stock; [SparkFun](https://www.sparkfun.com/nvidia-jetson-orin-nano-developer-kit.html) showed $399 on backorder without a firm shipment date. Refresh availability before changing suppliers.

## Memory and the first interaction

The **8 GB working memory is included** in the Jetson and shared by the CPU, GPU, and operating system. It is not a separate RAM purchase or an upgradeable memory stick. The **128 GB microSD card is storage**, not extra working memory. Begin model trials around a **1–3B parameter answer model with 4-bit weights**, alongside compact English transcription and local speech synthesis. Exact models and runtimes remain unselected; each needs a compatibility, memory, quality, and latency check. [NVIDIA hardware reference](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/hardware_layout.html), [NVIDIA FAQ](https://developer.nvidia.com/embedded/faq).

The intended Jetson interaction is:

**Press button → speak → press again to finish → local transcription → local answer using a configurable system prompt → automatic spoken reply → idle.**

The button controls listening while the Jetson stays powered. Use English, one question at a time, with no conversation history, web search, document search, or vector retrieval in this first stage. The AtomS3-Lite supplies an assembled button and light; its USB event handling and the Jetson application still need implementation. [Button hardware documentation](https://docs.m5stack.com/en/core/AtomS3%20Lite).

The working Apple apps use Apple's on-device answer backend, not a selected downloadable open model. Apple models and installed voices cannot be copied onto Jetson. Keep the Apple apps' current manual **Read aloud** behavior; the dedicated voice-only device will speak its completed answer automatically. Its voice quality must be evaluated after selecting a local synthesizer. See the [architecture decision](../design_direction.md).

## Budget checkpoint

The **first-year ceiling remains $1,000** for all new hardware, required subscriptions and software/distribution fees, tax, shipping, and tariffs. The [budget record](bill_of_materials.md) allocates $487.55 for these parts, $99 for a possible Apple Developer renewal, and a provisional $100 allowance for checkout charges. That leaves **$313.45 unallocated** for later work and contingency, subject to actual checkout costs. No paid inference subscription is planned. New spending recorded at this checkpoint: **$0**.

Battery operation, a portable enclosure, and any screen are later decisions within that same ceiling. Approximately two hours per charge remains an unmeasured future target, not a condition for this first purchase batch.

## Resume here next week

1. Read this list, [current status](../status.md), and [issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47). Recheck Arrow stock, all eight prices, and the cart contents; do not assume the prepared cart remains available. Keep the SanDisk card and the six-item DigiKey order unless a new sourcing decision is recorded.
2. Confirm the complete delivered totals, included power supply/US cord, and any renewal due within the first year. Keep the whole project within $1,000. Record purchases only after successful checkout; publish item, amount, and fulfillment status without private order or account details.
3. After arrival, inspect firmware and use a supported official installation path. Start with the supplied mains adapter, the existing Mac, the microSD reader, and USB data console. The Jetson USB-C connection is for data, not mains power. Qualify microphone, speaker, and button connectivity before building the voice loop.
4. Select and record exact transcription, answer, and voice artifacts, licenses, quantization, runtime versions, context/output limits, and the approved test prompt. Implement the button flow and verify a local spoken question and spoken reply. Use deliberately authored evaluation examples; keep private prompts and raw microphone content out of GitHub.
5. After setup downloads, disconnect external networks and test the full voice loop, errors, and cancellation. Agree on usefulness and acceptable waiting time before scoring; record latency, peak memory, failures, and power/thermal conditions separately for Jetson. Revisit battery and enclosure choices after the mains-powered loop works. Purchased parts alone do not establish a working device or measured result.

**Setup dependency to resolve:** [Jetson AI Lab's headless USB setup guide](https://www.jetson-ai-lab.com/tutorials/hackathon-guide/) supports the intended console approach. Factory JetPack 5.x firmware can need an update before a 6.x SD image boots; confirm the applicable [firmware procedure](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/update_firmware.html) and [JetPack installation guide](https://docs.nvidia.com/jetson/jetpack/6.2.1/install-setup/index.html). SDK Manager recovery requires an Ubuntu x64 host, which is not an assumed owned asset. If the received unit requires another host, display, or boot device, resolve that setup cost within the budget before proceeding. OS, model, and voice downloads precede offline operation; missing assets must not trigger a cloud fallback.
