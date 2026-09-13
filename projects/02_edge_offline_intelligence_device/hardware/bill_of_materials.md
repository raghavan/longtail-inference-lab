# Project budget and Jetson selection

**First-year total ceiling:** $1,000 USD, confirmed September 12, 2026.

**Checkpoint:** September 13, 2026; shopping list recorded, purchasing on hold until the next owner session. No order or new spending recorded.

**Evidence:** Zero published Jetson measurements.

The [shopping list](portable_procurement.md) contains eight exact items from Arrow, DigiKey, and B&H, with purchase links and dated supplier observations. The first hardware stage is a mains-powered Orin Nano Super 8 GB with USB microphone, USB speaker, physical button, 128 GB SanDisk card, reader, and two data cables. The listed parts subtotal is **$487.55 before tax, shipping, and tariffs**. It is not a guaranteed delivered price.

## First-year allocation

| Allocation | Planned amount |
| --- | ---: |
| Arrow: complete Orin Nano Super 8 GB developer kit | $399.00 |
| DigiKey: microphone, speaker, button, reader, two data cables | $48.30 |
| B&H: SanDisk Extreme 128 GB microSD card | $40.25 |
| Apple Developer enrollment/renewal reserve, if due | $99.00 |
| Provisional tax, shipping, and tariff allowance | $100.00 |
| Unallocated for later hardware and contingency | $313.45 |
| **First-year ceiling** | **$1,000.00** |

The first three rows total **$487.55**. Together with the $99 fee reserve and $100 checkout allowance, the provisional allocation is **$686.55**. These are planning amounts, not expenses already paid. New spending recorded at this checkpoint is **$0**; the prepared retailer cart is neither an order nor a reservation. Replace estimates with actual delivered costs after checkout and adjust the unallocated balance.

The ceiling covers all new hardware needed for the end product and required software, model licenses, subscriptions, and distribution fees during the first 12 months. Any new setup or test equipment also counts. Reuse the existing Mac and iPhone without counting their original prices. Existing equipment or prepaid services can reduce new spending but do not increase the ceiling. Count renewals due during the year; report later years separately.

No paid cloud inference subscription is planned. Apple lists Developer membership at $99 per year; the reserve applies if enrollment or renewal is due during the project year. Existing TestFlight access does not establish a new charge. Any required paid runtime or model license must fit within the same total. [Apple Developer membership](https://developer.apple.com/programs/whats-included/).

## Hardware boundary

The selected first-batch compute target is the **complete Orin Nano Super 8 GB developer kit**, with its supplied cooling and mains power. Its working memory is included and shared; the separate 128 GB card stores the operating system, applications, and models. Model trials should start with a compact quantized answer model plus local transcription and synthesis. The complete software workload still needs qualification on the device.

Screen, battery, portable enclosure, NVMe storage, and extra development/test accessories are deferred. The later approximately two-hour battery target is unmeasured. The $313.45 planning balance does not establish that every later addition is affordable; quote the complete next stage against actual spending before committing to it.

A 16 GB Jetson configuration requires evaluating the Orin NX tier and its complete carrier, cooling, power, and storage cost. It is not an extra RAM stick for this kit or a selected purchase. [NVIDIA module lineup](https://developer.nvidia.com/embedded/jetson-modules).

## Before ordering

Resume from the [purchase and setup checklist](portable_procurement.md#resume-here-next-week). Recheck all stock and prices, the complete kit contents, checkout charges, and any setup equipment needed for the received firmware. Confirm that the delivered total plus all required first-year fees fits the ceiling. Keep private checkout details outside public records.

Mac and iPhone checks cannot establish Jetson memory headroom, answer quality, speed, energy use, thermals, or offline integrity. Record the Jetson configuration and its results separately. Keep [issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47) open until sourcing and device acceptance are recorded.
