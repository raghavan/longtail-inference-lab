# iPhone app and TestFlight delivery

The `LocalVoice.xcodeproj` application target builds the existing shared SwiftUI entry point and links `LocalVoiceCore` from the parent Swift package. It produces a real iPhone app bundle. There is no duplicate phone model implementation, external package dependency, or bundled model weight. Current beta: **Local Voice Lab 0.3.0 (build 5)** in TestFlight, bundle identifier `lab.longtailinference.localvoice`. The installed app is named **Local Voice**.

Use an Apple Intelligence–capable iPhone running iOS 26 or later. Enable Apple Intelligence and install the required system assets on that phone. The app checks answer, transcription, and speaking-voice availability at runtime. English is the current scope. Each completed answer remains silent until **Read aloud** is pressed.

## Install the owner beta

Apple processed build 0.3.0 (5) on September 12, 2026. The internal **Owner testing** group contains the build as **Ready to Test** and the authorized owner as **Invited**. Installation and physical-device evaluation remain unverified.

1. Open Apple's TestFlight invitation on the iPhone and follow it into the TestFlight app.
2. Accept the invitation and install **Local Voice Lab**. Open **Local Voice** from the home screen.
3. Check answer and speech readiness. Use **Prepare local speech** if offered; initial system asset setup may require internet. Allow microphone access when testing recording.
4. Try a short typed question, then **Record** and **Stop and answer**. Press **Read aloud** only when playback is wanted. Use **Voice** and **Preview voice** to compare installed English voices.

For a higher-quality installed voice, use Settings → Accessibility → Read & Speak → Voices → English, download an available Enhanced or Premium voice, and refresh voices in the app. Voice names and availability vary by device. Record the phone model and iOS version before evaluating microphone accuracy, voice naturalness, interruptions, offline behavior, or resource use. Keep private questions, recordings, and invitation links out of public project records.

## Build and inspect

From the `software/apple` directory:

```bash
swift test
./build-ios.sh simulator
```

The simulator app is `build/ios/Build/Products/Debug-iphonesimulator/LocalVoice.app`. Open the Xcode project, select the **LocalVoice** app scheme and an iPhone simulator, then Run to install and inspect it. Select the application scheme, not the executable scheme from the local Swift package.

The iOS 26.5 simulator completed an authored typed question and manual read-aloud. It reported English speech transcription as unavailable, so microphone capture was not exercised there. Simulator results do not establish physical-phone model availability, speech accuracy, naturalness, memory, latency, battery use, or offline behavior.

## Sign and archive

Use the existing enrolled Apple developer account in Xcode. Copy `Config/Signing.example.xcconfig` to `Config/Signing.local.xcconfig` and set the developer team there. The local file is ignored. Do not commit account details, team IDs, certificates, keys, provisioning profiles, or raw upload logs. Selecting a team in Xcode can also write it into the project file; remove those tracked overrides after moving the value to the local configuration.

```bash
./build-ios.sh archive
```

This requests automatic provisioning and creates `build/ios/LocalVoice.xcarchive` after signing completes. macOS may require the owner to approve keychain access for `codesign`. Enter credentials directly into the system dialog. A completed development-signed archive still requires App Store distribution signing and upload; archive success alone is not TestFlight delivery.

## Deliver to the owner

1. Use the existing **Local Voice Lab** iOS record in App Store Connect: English (U.S.), the matching bundle identifier, and SKU `local-voice-ios`. Increment the build number in `Config/App.xcconfig` for a new upload; do not create a duplicate app record.
2. Open the archive in Xcode Organizer, choose **Distribute App**, and upload to App Store Connect using the existing developer team. Resolve any validation errors before claiming acceptance.
3. Wait for Apple processing. In the app's TestFlight tab, make the processed build available to the owner's internal testing group. Add only the authorized owner; external testers and public release are separate decisions.
4. Confirm the actual TestFlight build state and owner availability, then record the version/build and sanitized status in the [delivery record](../../../development/ios_testflight.md). Never publish signing or account identifiers.

Account authentication, legal agreements, and enrollment may require the owner. Do not revoke certificates, buy a membership, or accept agreements to bypass a blocked delivery step. Apple distinguishes [upload](https://help.apple.com/xcode/mac/current/en.lproj/dev442d7f2ca.html), [TestFlight distribution](https://help.apple.com/xcode/mac/current/en.lproj/dev2539d985f.html), and [internal tester access](https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers/).

## Privacy and release metadata

`PrivacyInfo.xcprivacy` declares no app data collection or tracking and declares UserDefaults reason `CA92.1` for the voice selection preference stored in this app's own defaults. The implementation has no app-owned audio/transcript persistence or analytics. This declaration describes app behavior; it does not substitute for the planned network-disconnected verification. See Apple's [required-reason API documentation](https://developer.apple.com/documentation/bundleresources/app-privacy-configuration/nsprivacyaccessedapitypes/nsprivacyaccessedapitype).

`Info.plist` includes microphone and speech permission descriptions, the launch screen, version/build, and iPhone orientations. `ITSAppUsesNonExemptEncryption` is false: the app implements no encryption of its own and embeds no third-party encryption library. See Apple's [export-compliance key documentation](https://developer.apple.com/documentation/bundleresources/information-property-list/itsappusesnonexemptencryption).

The opaque 1024-pixel app icon and its generation provenance are in [Assets.xcassets/README.md](Assets.xcassets/README.md). Build products, archives, and upload artifacts stay ignored. The [development milestone](../../../development/ios_testflight.md) defines completion and remaining physical-phone checks.
