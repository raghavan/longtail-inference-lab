# Project budget and Jetson selection

**First-year total ceiling:** $1,000 USD, confirmed September 12, 2026.
**Status:** Planning allocation; no purchase placed or new spending recorded in this update.
**Evidence:** Zero published Jetson measurements.

## Cost scope

The confirmed ceiling covers the first 12 months of the project: all new hardware needed to build the end product and every required subscription, software/model license, and app-distribution fee. Include storage, audio, controls, output hardware, power, cooling, enclosure, assembly materials, tax, and shipping. Reuse the already-owned Mac and iPhone without counting their original purchase prices. Any new development or test hardware also consumes this budget.

Count each required subscription over its expected use during the first year, including renewals due in that period; do not compare a monthly subscription price with a one-time hardware price as if they were the same cost. Existing equipment and prepaid services can reduce new spending but do not increase the ceiling. Costs after the first year must be reported separately.

| Allocation | Maximum planned amount |
| --- | ---: |
| Jetson configuration and all physical accessories | $700 |
| Required subscriptions, software, and app-distribution fees | $100 |
| Tax and shipping reserve | $100 |
| Contingency | $100 |
| **Total** | **$1,000** |

These are provisional spending envelopes, not vendor quotes. The $1,000 total and its first-year scope are confirmed; the category allocations can move within that total. The hardware envelope must cover the compute module or kit, carrier if separate, cooling, storage, microphone, output/control hardware, power, and the chosen physical packaging. Optional battery work also consumes this same budget. A parts list is viable only if its complete delivered cost fits; a module-only price cannot establish that.

The local-inference design plans for no paid cloud inference subscription. If a paid runtime, model license, or other subscription becomes necessary, its first-year cost must fit within the same ceiling by reallocating these envelopes.

Apple lists membership at $99 per year. Reserve that cost if enrollment or renewal is needed for the project during the first year; an already-covered membership is not a new charge. [Apple Developer membership](https://developer.apple.com/programs/whats-included/).

## Hardware candidates

| Candidate | Role | Selection rule |
| --- | --- | --- |
| Jetson Orin Nano Super developer kit, 8 GB | Baseline physical prototype candidate | Prefer if the selected local pipeline fits with measured operating headroom and the full build meets the budget |
| Jetson Orin NX, 16 GB, with compatible carrier and peripherals | Higher-memory alternative | Consider if workload/model needs justify the memory and a current complete quote fits the remaining ceiling |

NVIDIA lists Orin Nano modules at 4 GB and 8 GB, and Orin NX at 8 GB and 16 GB. There is no 16 GB Orin Nano in that lineup. [NVIDIA module lineup](https://developer.nvidia.com/embedded/jetson-modules), [Nano Super developer kit](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/).

The larger budget gives the complete prototype more room; it does not establish that an NX 16 GB configuration is affordable or necessary. Obtain current supplier quotes at procurement time and record every included and missing component.

## Procurement gate

Use the Mac/iPhone iterations to settle the useful workload and model envelope. Then produce a dated complete quote, remaining-budget calculation, supported software/JetPack configuration, power and cooling plan, and target-device measurement plan. Begin the physical prototype on mains power with a dependable reference microphone. Select its text display or voice output before finalizing the parts list.

Mac and iPhone measurements inform the workload and implementation. They cannot predict Jetson performance precisely, including CUDA memory behavior, energy, thermals, and model residency. Purchase decisions and later upgrades must state which assumptions remain unmeasured.
