import Foundation
import AVFoundation
import Speech

@MainActor public final class AppleSpeechInput: SpeechInput {
    private let locale = Locale(identifier: "en-US")
    private var analyzer: SpeechAnalyzer?
    private var engine: AVAudioEngine?
    private var input: AsyncThrowingStream<AnalyzerInput, Error>.Continuation?
    private var captureDeadline: Task<Void, Never>?
    private var activeID: UUID?
    private var tapInstalled = false

    public init() {}

    public func readiness() async -> Readiness {
        guard SpeechTranscriber.isAvailable,
              await SpeechTranscriber.supportedLocale(equivalentTo: locale) != nil else {
            return .unavailable("Local English speech recognition is unavailable on this device.")
        }
        let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
        return await AssetInventory.status(forModules: [transcriber]) == .installed ? .ready :
            .setupNeeded("Download local English speech assets to enable recording.")
    }

    public func prepare() async throws {
        guard SpeechTranscriber.isAvailable else { throw VoiceError.message("Local speech recognition is unavailable.") }
        let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
        _ = try await AssetInventory.reserve(locale: locale)
        if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
            try await request.downloadAndInstall()
        }
    }

    public func record(update: @escaping @MainActor (String) -> Void, started: @escaping @MainActor () -> Void) async throws -> String {
        guard activeID == nil else { throw VoiceError.message("A recording is already active.") }
        guard await readiness().isReady else { throw VoiceError.message("Prepare local speech before recording.") }
        try Task.checkCancellation()
        guard await AVCaptureDevice.requestAccess(for: .audio) else {
            throw VoiceError.message("Microphone access is needed. Allow it in Privacy & Security settings.")
        }
        try Task.checkCancellation()
        #if os(iOS)
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.record, mode: .measurement)
        try audioSession.setActive(true)
        #endif
        let id = UUID()
        activeID = id
        let transcriber = SpeechTranscriber(locale: locale, preset: .progressiveTranscription)
        let analyzer = SpeechAnalyzer(modules: [transcriber])
        self.analyzer = analyzer
        let engine = AVAudioEngine()
        self.engine = engine
        let sourceFormat = engine.inputNode.outputFormat(forBus: 0)
        guard sourceFormat.sampleRate > 0, sourceFormat.channelCount > 0,
              let format = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber], considering: sourceFormat) else {
            await cancel()
            throw VoiceError.message("The microphone audio format is unavailable. Check the selected input device.")
        }
        let (stream, continuation) = AsyncThrowingStream<AnalyzerInput, Error>.makeStream()
        input = continuation
        guard let tap = SpeechAudioTap.make(from: sourceFormat, to: format, continuation: continuation) else {
            await cancel()
            throw VoiceError.message("The microphone audio format could not be converted.")
        }
        let results = Task { @MainActor in
            var finalized = ""
            for try await result in transcriber.results {
                try Task.checkCancellation()
                let segment = String(result.text.characters)
                if result.isFinal {
                    finalized += segment
                    update(finalized)
                } else { update(finalized + segment) }
            }
            return finalized.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        do {
            try await analyzer.prepareToAnalyze(in: format)
            try Task.checkCancellation()
            engine.inputNode.installTap(onBus: 0, bufferSize: 4096, format: sourceFormat, block: tap)
            tapInstalled = true
            try await analyzer.start(inputSequence: stream)
            engine.prepare()
            try engine.start()
            started()
            captureDeadline = Task { [weak self] in
                do { try await Task.sleep(for: .seconds(30)) } catch { return }
                guard let self, self.activeID == id else { return }
                self.stop()
            }
            try await withTaskCancellationHandler {
                try await analyzer.finalizeAndFinishThroughEndOfInput()
            } onCancel: {
                continuation.finish(throwing: CancellationError())
                Task { await analyzer.cancelAndFinishNow() }
            }
            let text = try await results.value
            await cleanup(id: id)
            return text
        } catch {
            results.cancel()
            await cleanup(id: id)
            throw error
        }
    }

    public func stop() {
        captureDeadline?.cancel()
        engine?.stop()
        if tapInstalled { engine?.inputNode.removeTap(onBus: 0); tapInstalled = false }
        input?.finish()
    }

    public func cancel() async {
        guard let id = activeID else { return }
        await cleanup(id: id)
    }

    private func cleanup(id: UUID) async {
        guard activeID == id else { return }
        stop()
        let finishingAnalyzer = analyzer
        await finishingAnalyzer?.cancelAndFinishNow()
        guard activeID == id else { return }
        engine = nil
        analyzer = nil
        input = nil
        activeID = nil
        #if os(iOS)
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        #endif
    }

    public func transcribeFile(_ url: URL) async throws -> String {
        guard await readiness().isReady else { throw VoiceError.message("Local speech assets are not installed.") }
        let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
        let analyzer = SpeechAnalyzer(modules: [transcriber])
        let results = Task { @MainActor in
            var text = ""
            for try await result in transcriber.results { text += String(result.text.characters) }
            return text.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        do {
            let file = try AVAudioFile(forReading: url)
            try await analyzer.start(inputAudioFile: file, finishAfterFile: true)
            return try await results.value
        } catch {
            results.cancel()
            await analyzer.cancelAndFinishNow()
            throw error
        }
    }
}

enum SpeechAudioTap {
    // AVAudioEngine calls this on its audio queue. Creating the closure outside
    // MainActor keeps Swift from adding a UI-executor assertion to the callback.
    // Sendable also prevents the callback from capturing actor-isolated UI state.
    nonisolated static func make(
        from source: AVAudioFormat,
        to destination: AVAudioFormat,
        continuation: AsyncThrowingStream<AnalyzerInput, Error>.Continuation
    ) -> (@Sendable (AVAudioPCMBuffer, AVAudioTime) -> Void)? {
        guard let converter = PCMConverter(from: source, to: destination) else { return nil }
        return { buffer, _ in
            do {
                if let converted = try converter.convert(buffer) {
                    continuation.yield(AnalyzerInput(buffer: converted))
                }
            } catch { continuation.finish(throwing: error) }
        }
    }
}

// The converter is confined to one audio tap callback. Each output owns its memory;
// hardware input buffers are never retained by the asynchronous analyzer.
private final class PCMConverter: @unchecked Sendable {
    private let converter: AVAudioConverter
    private let format: AVAudioFormat
    init?(from source: AVAudioFormat, to destination: AVAudioFormat) {
        guard let converter = AVAudioConverter(from: source, to: destination) else { return nil }
        self.converter = converter
        format = destination
    }
    func convert(_ buffer: AVAudioPCMBuffer) throws -> AVAudioPCMBuffer? {
        let capacity = AVAudioFrameCount(ceil(Double(buffer.frameLength) * format.sampleRate / buffer.format.sampleRate)) + 32
        guard let output = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: capacity) else {
            throw VoiceError.message("Could not allocate an audio buffer.")
        }
        var error: NSError?
        let source = PCMInput(buffer)
        let status = converter.convert(to: output, error: &error) { _, inputStatus in
            guard let next = source.take() else { inputStatus.pointee = .noDataNow; return nil }
            inputStatus.pointee = .haveData
            return next
        }
        if status == .error { throw VoiceError.message("Microphone audio conversion failed.") }
        return output.frameLength > 0 ? output : nil
    }
}

// Conversion is synchronous within the audio callback. The lock ensures only one
// converter request receives the input, and the buffer never escapes that conversion.
private final class PCMInput: @unchecked Sendable {
    private let lock = NSLock()
    private var buffer: AVAudioPCMBuffer?
    init(_ buffer: AVAudioPCMBuffer) { self.buffer = buffer }
    func take() -> AVAudioPCMBuffer? {
        lock.lock()
        defer { lock.unlock() }
        let next = buffer
        buffer = nil
        return next
    }
}
