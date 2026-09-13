import AVFoundation
import Foundation

@MainActor public protocol SpeechOutput: AnyObject {
    var readiness: Readiness { get }
    var voices: [SpeechVoice] { get }
    var preferredVoiceIdentifier: String? { get }
    var selectedVoice: SpeechVoice? { get }
    func selectVoice(_ identifier: String?)
    func speak(_ text: String, finished: @escaping @MainActor () -> Void) throws
    func stop()
}

@MainActor public final class AppleSpeechOutput: SpeechOutput {
    private var synthesizer: AVSpeechSynthesizer?
    private var delegate: SpeechCompletionDelegate?
    private var requestID: UUID?
    private var completion: (@MainActor () -> Void)?

    public private(set) var preferredVoiceIdentifier: String?
    public init(preferredVoiceIdentifier: String? = nil) { self.preferredVoiceIdentifier = preferredVoiceIdentifier }

    public static func availableVoices() -> [SpeechVoice] {
        // Use installed Apple voices only. Never request personal voices or
        // route private text through a third-party speech provider extension.
        return AVSpeechSynthesisVoice.speechVoices().filter {
            $0.identifier.hasPrefix("com.apple.voice.") &&
            !$0.voiceTraits.contains(.isPersonalVoice) && !$0.voiceTraits.contains(.isNoveltyVoice) &&
            $0.language.split(separator: "-").first == "en" &&
            AVSpeechSynthesisVoice(identifier: $0.identifier) != nil
        }.map {
            SpeechVoice(id: $0.identifier, name: $0.name, language: $0.language,
                        quality: SpeechVoice.Quality(rawValue: $0.quality.rawValue) ?? .standard)
        }.sorted {
            if $0.quality != $1.quality { return $0.quality.rawValue > $1.quality.rawValue }
            return $0.id < $1.id
        }
    }

    public static func installedVoice(preferredIdentifier: String? = nil) -> AVSpeechSynthesisVoice? {
        guard let voice = SpeechVoice.preferred(in: availableVoices(), identifier: preferredIdentifier) else { return nil }
        return AVSpeechSynthesisVoice(identifier: voice.id)
    }

    public var voices: [SpeechVoice] { Self.availableVoices() }
    public var selectedVoice: SpeechVoice? { SpeechVoice.preferred(in: voices, identifier: preferredVoiceIdentifier) }
    public func selectVoice(_ identifier: String?) { stop(); preferredVoiceIdentifier = identifier }

    public var readiness: Readiness {
        Self.installedVoice() == nil ?
            .unavailable("Install an English system voice in Accessibility settings, then check again.") : .ready
    }

    public func speak(_ text: String, finished: @escaping @MainActor () -> Void) throws {
        stop()
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty, text.count <= 4_000 else {
            throw VoiceError.message("Enter text of up to 4,000 characters to read aloud.")
        }
        guard let voice = Self.installedVoice(preferredIdentifier: preferredVoiceIdentifier) else {
            throw VoiceError.message(readiness.message)
        }
        let id = UUID()
        let synthesizer = AVSpeechSynthesizer()
        #if os(iOS)
        // Give playback its own managed session after the recording session ends.
        synthesizer.usesApplicationAudioSession = false
        #endif
        let delegate = SpeechCompletionDelegate { [weak self] in
            Task { @MainActor in self?.finish(id: id) }
        }
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = voice
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        self.synthesizer = synthesizer
        self.delegate = delegate
        requestID = id
        completion = finished
        synthesizer.delegate = delegate
        synthesizer.speak(utterance)
    }

    public func stop() {
        requestID = nil
        completion = nil
        synthesizer?.delegate = nil
        synthesizer?.stopSpeaking(at: .immediate)
        synthesizer = nil
        delegate = nil
    }

    private func finish(id: UUID) {
        guard id == requestID else { return }
        let finished = completion
        stop()
        finished?()
    }
}

// Delegate callbacks may arrive on a framework queue. Only a Sendable closure
// crosses that boundary; AVSpeechUtterance never enters an asynchronous task.
private final class SpeechCompletionDelegate: NSObject, AVSpeechSynthesizerDelegate {
    private let finished: @Sendable () -> Void
    init(finished: @escaping @Sendable () -> Void) { self.finished = finished }
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) { finished() }
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) { finished() }
}
