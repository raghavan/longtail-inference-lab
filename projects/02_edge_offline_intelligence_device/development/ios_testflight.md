# iPhone application and TestFlight development milestone

**Status:** Delivery complete September 12, 2026; owner subsequently confirmed the beta works on their iOS device. Detailed device evaluation remains open.

**Tracking:** [GitHub issue 44](https://github.com/raghavan/longtail-inference-lab/issues/44); [implementation PR 45](https://github.com/raghavan/longtail-inference-lab/pull/45).

This record applies the relevant [experiment template](../../../resources/experiment_template/README.md) sections to packaging and distributing the existing Apple app. It is a development milestone, not the broader comparative model-selection experiment.

## Question and agreed decision

Can the working shared Mac implementation be packaged as a native iPhone app and delivered to the owner through TestFlight for physical-device evaluation?

The owner requested implementation and TestFlight upload. Keep English general conversation, local Apple speech recognition, the on-device answer model, visible text, and manual local read-aloud with installed voice selection. Use the same core and prompt policy on Mac and iPhone. Additional languages, conversation history, web/retrieval, public App Store launch, and Jetson integration are outside this milestone. The $1,000 first-year total ceiling remains unchanged.

## Workload, controls, and assumptions

Use the current bounded single-question flow and deliberately authored UI/check sentences. The phone must support the current Apple Intelligence backend and run iOS 26 or later. Confirm the owner's physical model and OS before claiming phone eligibility or results. Model and voice assets are installed separately on the phone; a successful Mac run or simulator run cannot establish real iPhone inference quality, latency, or memory fitness.

Preserve local processing and transient conversation/audio. The app stores only its voice preference. Include permission descriptions and the required-reason privacy declaration for that preference. Keep developer team identifiers, signing credentials, provisioning profiles, upload logs, and account details outside public project files. Use existing Apple developer access where available.

## Success and stop boundaries

Success requires a reproducible Xcode app target, simulator installation and UI checks, a device archive with valid distribution signing, Apple accepting and processing the upload, and a build available to the owner in TestFlight. Report each stage separately. Do not claim delivery from an archive or upload command alone.

Stop the dependent distribution step if account access, enrollment, agreements, signing, app registration, or Apple processing blocks it. Continue independent implementation and validation. Do not revoke existing certificates, purchase a membership, accept legal agreements, invite unrelated testers, or publish to the App Store as a workaround. Ask only for the missing access or information needed to continue.

## Validation and limitations

Build and run the real SwiftUI app on an iPhone simulator; check narrow layouts, keyboard dismissal, readiness/unavailable states, voice choices, and cancellation. Run the existing shared tests and focused regression checks for lifecycle changes. Build the physical-device archive and inspect its bundle metadata, icon, privacy manifest, architectures, and signing. Record sanitized build identifiers and TestFlight state.

Simulators may lack local answer models and transcription assets; show an honest unavailable state. Physical microphone use, local answer usefulness, Premium voice availability/naturalness, audio interruptions, network-disconnected operation, battery, and peak memory remain owner/device checks after installation. No comparative performance or quality score is claimed.

## Completion record

Beta **0.3.0 (build 5)** has a native iPhone target, shared core and SwiftUI source, an opaque app icon, permission descriptions, and a required-reason privacy manifest. Xcode 26.6 and the iOS 26.5 SDK built the simulator app. Seventeen shared automated tests passed, including two focused interruption regressions. Mac release compilation also passed.

An iPhone 17 Pro simulator running iOS 26.5 was used for development UI checks. It returned a local text answer to an authored typed question and completed manual read-aloud. Installed English voice selection, preview, explicit stop preserving the answer, text entry, and software-keyboard dismissal were exercised. The simulator reported local English transcription as unavailable and listed Standard English speaking voices. These observations are separate from physical-device evaluation.

The physical-device archive completed for 0.3.0 (build 5). The arm64 app passed strict signature verification using a development profile; its iOS 26 minimum, icon, and privacy manifest were checked. App Store distribution export and upload then succeeded. Apple reports the upload as **Complete**, and the build is **Ready to Test** in the internal **Owner testing** group. The group contains one build and one authorized owner tester with status **Invited**. Automatic distribution is disabled; later builds require deliberate assignment.

The App Store Connect and TestFlight listing is **Local Voice Lab**, because **Local Voice** was unavailable as a listing name. The installed app retains **Local Voice**. Existing developer access covered delivery; no purchase or subscription was added. No external testers or public App Store release were included.

This meets the delivery boundary. After delivery on September 12, the owner confirmed that the beta works on their iOS device. Record this as owner-reported installation and basic operation. The device model, iOS version, and individual feature paths were not specified; microphone behavior, offline operation, voice quality, and resource use remain the next evaluation gate. The [iPhone guide](../software/apple/iOS/README.md) records installation, reproducible build, and future delivery steps.
