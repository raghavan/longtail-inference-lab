// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "LocalVoice",
    platforms: [.macOS("26.0"), .iOS("26.0")],
    products: [
        .library(name: "LocalVoiceCore", targets: ["LocalVoiceCore"]),
        .executable(name: "LocalVoice", targets: ["LocalVoiceApp"]),
        .executable(name: "LocalVoiceCheck", targets: ["LocalVoiceCheck"])
    ],
    targets: [
        .target(name: "LocalVoiceCore"),
        .executableTarget(name: "LocalVoiceApp", dependencies: ["LocalVoiceCore"]),
        .executableTarget(name: "LocalVoiceCheck", dependencies: ["LocalVoiceCore"]),
        .testTarget(name: "LocalVoiceCoreTests", dependencies: ["LocalVoiceCore"])
    ],
    swiftLanguageModes: [.v6]
)
