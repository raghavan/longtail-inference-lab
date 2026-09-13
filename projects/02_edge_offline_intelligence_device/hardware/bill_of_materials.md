# Project budget and Jetson selection

**First-year total ceiling:** $1,000 USD, confirmed September 12, 2026.

**Checkpoint:** September 13, 2026; six DigiKey accessories and one Newegg microSD card are ordered. Their parts values are $48.30 and $42.99 respectively, totaling $91.29. Final delivered totals remain pending. The Jetson kit order is still unconfirmed.

**Evidence:** Zero published Jetson measurements.

The [shopping list](portable_procurement.md) contains eight exact items from Arrow, DigiKey, and Newegg, with purchase links and dated supplier observations. The first hardware stage is a mains-powered Orin Nano Super 8 GB with USB microphone, USB speaker, physical button, 128 GB SanDisk card, reader, and two data cables. The listed parts subtotal is **$490.29 before tax, shipping, and tariffs**. It includes the seven ordered items and is not a guaranteed delivered price.

## First-year allocation

| Allocation | Planned amount |
| --- | ---: |
| Arrow: complete Orin Nano Super 8 GB developer kit | $399.00 |
| DigiKey: microphone, speaker, button, reader, two data cables | $48.30 |
| Newegg: SanDisk Extreme 128 GB microSD card | $42.99 |
| Apple Developer enrollment/renewal reserve, if due | $99.00 |
| Provisional tax, shipping, and tariff allowance | $100.00 |
| Unallocated for later hardware and contingency | $310.71 |
| **First-year ceiling** | **$1,000.00** |

The first three rows total **$490.29**. Together with the $99 fee reserve and $100 checkout allowance, the provisional allocation is **$689.29**. These are planning amounts, not a settled-spending total. Checkout charges belong within the $100 allowance and must not be counted twice. Replace estimates with actual delivered costs and adjust the unallocated balance.

## Order record

| Merchant | Order status and evidence | Known cost | Still needed |
| --- | --- | ---: | --- |
| DigiKey | Owner confirmed order placement on September 13; exported line items match all six accessories, one each | $48.30 parts subtotal | Final tax, shipping, tariff, total, and fulfillment status |
| Arrow | Kit order not yet confirmed; earlier cart held one complete 8 GB kit | $399.00 listed price | Successful checkout and delivered total |
| Newegg | Supplied September 13 order summary confirms one SanDisk Extreme 128 GB card, item N82E16820173727, sold and fulfilled by Newegg | $42.99 item price | Final tax, shipping, total, and fulfillment status |

The DigiKey checkout previously quoted $4.99 shipping and $0.45 tariff, or **$53.74 before tax**. The item export does not establish those final charges. Newegg checkout previously quoted free shipping, but the supplied order summary does not show the final charges. The **$91.29 ordered parts value** is already in the allocation above; the actual aggregate spend and exact remaining first-year balance remain pending. Do not reorder the six accessories or the card. Shipment, delivery, and payment settlement are not established by order placement or a retailer fulfillment label alone. Private receipts and identifiers stay outside this public record.

The ceiling covers all new hardware needed for the end product and required software, model licenses, subscriptions, and distribution fees during the first 12 months. Any new setup or test equipment also counts. Reuse the existing Mac and iPhone without counting their original prices. Existing equipment or prepaid services can reduce new spending but do not increase the ceiling. Count renewals due during the year; report later years separately.

No paid cloud inference subscription is planned. Apple lists Developer membership at $99 per year; the reserve applies if enrollment or renewal is due during the project year. Existing TestFlight access does not establish a new charge. Any required paid runtime or model license must fit within the same total. [Apple Developer membership](https://developer.apple.com/programs/whats-included/).

## Hardware boundary

The selected first-batch compute target is the **complete Orin Nano Super 8 GB developer kit**, with its supplied cooling and mains power. Its working memory is included and shared; the separate 128 GB card stores the operating system, applications, and models. Model trials should start with a compact quantized answer model plus local transcription and synthesis. The complete software workload still needs qualification on the device.

Screen, battery, portable enclosure, NVMe storage, and extra development/test accessories are deferred. The later approximately two-hour battery target is unmeasured. The $310.71 planning balance does not establish that every later addition is affordable; quote the complete next stage against actual spending before committing to it.

A 16 GB Jetson configuration requires evaluating the Orin NX tier and its complete carrier, cooling, power, and storage cost. It is not an extra RAM stick for this kit or a selected purchase. [NVIDIA module lineup](https://developer.nvidia.com/embedded/jetson-modules).

## Before ordering

Resume from the [purchase and setup checklist](portable_procurement.md#next-steps). Reconcile the existing accessory and storage orders and check whether the Jetson kit has since been purchased. Recheck kit stock and price, complete kit contents, checkout charges, and any setup equipment needed for the received firmware. Confirm that the delivered total plus all required first-year fees fits the ceiling. Keep private checkout details outside public records.

Mac and iPhone checks cannot establish Jetson memory headroom, answer quality, speed, energy use, thermals, or offline integrity. Record the Jetson configuration and its results separately. Keep [issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47) open until sourcing and device acceptance are recorded.
