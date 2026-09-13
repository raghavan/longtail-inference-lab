# Projects

Projects contain the laboratory's active, bounded research. Each needs a question, a measurement plan, a success boundary, a stop boundary, and a completion condition.

## Active project

### [02 Edge Offline Intelligence Device](02_edge_offline_intelligence_device/README.md)

**Status:** Native Mac voice input, text answers, and optional local read-aloud work; the owner confirmed basic iOS TestFlight operation. The [Jetson shopping list](02_edge_offline_intelligence_device/hardware/portable_procurement.md) is recorded for a first mains-powered voice prototype. The six DigiKey accessories and Newegg storage card are ordered; the Jetson kit order remains unconfirmed. Model-selection intake remains open. Zero published comparative quality or performance measurements for Mac, iPhone, or Jetson.

Build a local voice-input and text-answer experience in three iterations: a native Mac app, an iPhone app through TestFlight with conditional launch, and a self-contained NVIDIA Jetson prototype. The first-year total ceiling is $1,000, covering all new hardware for the end product, required subscriptions and software/distribution fees, tax, and shipping.

The [architecture](02_edge_offline_intelligence_device/design_direction.md) selects the Mac's model integration around the iPhone's constraints. The [technical status](02_edge_offline_intelligence_device/status.md) records the working Mac slice with manual English read-aloud, development checks, and limitations. The [intake draft](../resources/project_proposals/apple_local_voice_intake.md) proposes an Apple on-device model evaluation and a compact open-model fallback. It needs the target phone and representative English general-conversation cases before comparative model selection.

## Status meanings

| Status | Meaning |
| --- | --- |
| Idea | The question still needs intake. |
| Specified | The bounded question and measurement plan are documented. |
| Running | Measured execution has begun. |
| Analyzing | Collected results are being interpreted. |
| Complete | The declared measurement and publication condition has been met. |
| Closed | Active work has ended with a conclusion, including any unmet evidence requirements. |
| Paused | Work is suspended with explicit conditions for resuming. |

An active project's next experiment can be in intake; its draft stays in resources until specified. Complete, Closed, and Paused work belongs in the archive.
