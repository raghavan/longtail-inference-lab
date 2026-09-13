# Project budget and Jetson selection

**First-year total ceiling:** $1,000 USD, confirmed September 12, 2026.

**Checkpoint:** September 13, 2026; all eight first-batch items are ordered across Arrow, DigiKey, and Newegg. The Arrow order total is confirmed at $428.93. DigiKey and Newegg final charges remain pending; arrival and device acceptance are not yet confirmed.

**Evidence:** Zero published Jetson measurements.

The [order record and arrival checklist](portable_procurement.md) contains the eight exact ordered items and public product links. The first hardware stage is a mains-powered Orin Nano Super 8 GB with USB microphone, USB speaker, physical button, 128 GB SanDisk card, reader, and two data cables. The parts subtotal is **$490.29 before tax, shipping, and tariffs**. Including Arrow's confirmed $29.93 tax, **$520.22 in order costs is recorded so far**; this is an incomplete total until the other merchants' final charges are reconciled.

## First-year allocation

| Allocation | Recorded or reserved amount |
| --- | ---: |
| Arrow: complete kit, including confirmed tax and free shipping | $428.93 |
| DigiKey: six ordered accessories, parts subtotal only | $48.30 |
| Newegg: ordered SanDisk Extreme 128 GB card, item price only | $42.99 |
| Apple Developer enrollment/renewal reserve, if due | $99.00 |
| Remaining provisional tax, shipping, and tariff allowance | $70.07 |
| Unallocated for later hardware and contingency | $310.71 |
| **First-year ceiling** | **$1,000.00** |

The first three rows total **$520.22**, combining Arrow's confirmed order total with the other two item subtotals. Arrow's $29.93 tax uses part of the original $100 checkout allowance, leaving $70.07 reserved for charges still to be reconciled. Together with the $99 fee reserve, the provisional allocation remains **$689.29**, leaving $310.71 provisionally unallocated. These are mixed recorded costs and planning reserves, not a settled-spending total. Do not add recorded item costs or Arrow tax a second time. Replace remaining estimates with final costs and adjust the balance.

## Order record

| Merchant | Order status and evidence | Known cost | Still needed |
| --- | --- | ---: | --- |
| DigiKey | Owner confirmed order placement on September 13; exported line items match all six accessories, one each | $48.30 parts subtotal | Final tax, shipping, tariff, total, and fulfillment status |
| Arrow | Supplied September 13 order confirmation matches one complete US-region 8 GB kit, 945-13766-0000-000 | $428.93 total: $399.00 item + $29.93 tax; shipping free, no tariff amount listed | Confirm actual dispatch and delivery; retailer lists expected shipment September 14 and delivery September 21, 2026 |
| Newegg | Supplied September 13 order summary confirms one SanDisk Extreme 128 GB card, item N82E16820173727, sold and fulfilled by Newegg | $42.99 item price | Final tax, shipping, total, and fulfillment status |

The DigiKey checkout previously quoted $4.99 shipping and $0.45 tariff, or **$53.74 before tax**. The item export does not establish those final charges. Newegg checkout previously quoted free shipping, but the supplied order summary does not show the final charges. All eight item costs are already in the allocation above; the final aggregate spend and exact remaining first-year balance remain pending. Do not reorder any first-batch item. Shipment, delivery, and payment settlement are not established by order placement or a retailer fulfillment label alone. Future dates are expectations, not confirmed fulfillment. Keep all PII, private receipts, screenshots, and identifiers outside public records under the [public memory policy](../../../areas/lab_operations/public_research_memory.md).

The ceiling covers all new hardware needed for the end product and required software, model licenses, subscriptions, and distribution fees during the first 12 months. Any new setup or test equipment also counts. Reuse the existing Mac and iPhone without counting their original prices. Existing equipment or prepaid services can reduce new spending but do not increase the ceiling. Count renewals due during the year; report later years separately.

No paid cloud inference subscription is planned. Apple lists Developer membership at $99 per year; the reserve applies if enrollment or renewal is due during the project year. Existing TestFlight access does not establish a new charge. Any required paid runtime or model license must fit within the same total. [Apple Developer membership](https://developer.apple.com/programs/whats-included/).

## Hardware boundary

The selected first-batch compute target is the **complete Orin Nano Super 8 GB developer kit**, with its supplied cooling and mains power. Its working memory is included and shared; the separate 128 GB card stores the operating system, applications, and models. Model trials should start with a compact quantized answer model plus local transcription and synthesis. The complete software workload still needs qualification on the device.

Screen, battery, portable enclosure, NVMe storage, and extra development/test accessories are deferred. The later approximately two-hour battery target is unmeasured. The $310.71 planning balance does not establish that every later addition is affordable; quote the complete next stage against actual spending before committing to it.

A 16 GB Jetson configuration requires evaluating the Orin NX tier and its complete carrier, cooling, power, and storage cost. It is not an extra RAM stick for this kit or a selected purchase. [NVIDIA module lineup](https://developer.nvidia.com/embedded/jetson-modules).

## After ordering

Resume from the [arrival and setup checklist](portable_procurement.md#next-steps). Reconcile the DigiKey and Newegg final costs, record actual fulfillment as it becomes available, and inspect kit contents and received firmware after arrival. Any new setup equipment and required first-year fees must fit the remaining ceiling. Keep private checkout details outside public records.

Mac and iPhone checks cannot establish Jetson memory headroom, answer quality, speed, energy use, thermals, or offline integrity. Record the Jetson configuration and its results separately. Keep [issue 47](https://github.com/raghavan/longtail-inference-lab/issues/47) open until sourcing and device acceptance are recorded.
