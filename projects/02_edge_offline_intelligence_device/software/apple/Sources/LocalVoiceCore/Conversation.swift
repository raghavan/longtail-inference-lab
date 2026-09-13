import Foundation
import Observation

public enum Readiness: Equatable, Sendable {
    case ready
    case setupNeeded(String)
    case unavailable(String)

    public var message: String {
        switch self {
        case .ready: return "Ready"
        case .setupNeeded(let message), .unavailable(let message): return message
        }
    }
    public var isReady: Bool { self == .ready }
}

public enum VoiceError: LocalizedError {
    case message(String)
    public var errorDescription: String? {
        switch self { case .message(let message): return message }
    }
}

@MainActor public protocol AnswerEngine: AnyObject {
    var readiness: Readiness { get }
    func answer(_ text: String, update: @escaping @MainActor (String) -> Void) async throws
}

@MainActor public protocol SpeechInput: AnyObject {
    func readiness() async -> Readiness
    func prepare() async throws
    func record(update: @escaping @MainActor (String) -> Void, started: @escaping @MainActor () -> Void) async throws -> String
    func stop()
    func cancel() async
}

@MainActor @Observable public final class Conversation {
    public enum Phase: String { case idle, preparing, listening, transcribing, answering, cancelling }
    public var transcript = ""
    public private(set) var answer = ""
    public private(set) var phase: Phase = .idle
    public private(set) var notice = "Speak or type a question."
    public private(set) var speechReadiness: Readiness = .unavailable("Checking speech…")
    public private(set) var answerReadiness: Readiness = .unavailable("Checking answers…")
    public var isBusy: Bool { phase != .idle }
    public static let maximumInputCharacters = 1_200
    private let answers: any AnswerEngine
    private let speech: any SpeechInput
    private var operation: Task<Void, Never>?
    private var deadline: Task<Void, Never>?
    private var revision = 0

    public init(answers: any AnswerEngine, speech: any SpeechInput) {
        self.answers = answers
        self.speech = speech
    }

    public func refresh() async {
        answerReadiness = answers.readiness
        speechReadiness = await speech.readiness()
    }

    public func prepareSpeech() {
        guard !isBusy else { return }
        let current = begin(.preparing, notice: "Preparing local speech. Setup may need internet.")
        operation = Task {
            do {
                try await speech.prepare()
                guard current == revision else { return }
                await refresh()
                notice = speechReadiness.isReady ? "Speech is ready on this device." : speechReadiness.message
                phase = .idle
            } catch { finish(error, revision: current) }
        }
    }

    public func ask() {
        guard !isBusy else { return }
        let text = transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        guard validate(text) else { return }
        let current = begin(.answering, notice: "Writing an answer on this device…")
        armDeadline(seconds: 60, revision: current)
        operation = Task { await generate(text, revision: current) }
    }

    public func record() {
        guard !isBusy, speechReadiness.isReady else { return }
        transcript = ""
        let current = begin(.preparing, notice: "Preparing the microphone…")
        armDeadline(seconds: 90, revision: current)
        operation = Task {
            do {
                let text = try await speech.record(update: { [weak self] text in
                    guard let self, self.revision == current else { return }
                    self.transcript = text
                }, started: { [weak self] in
                    guard let self, self.revision == current else { return }
                    self.phase = .listening
                    self.notice = "Listening. Stop when you finish speaking."
                })
                guard current == revision else { return }
                transcript = text
                guard validate(text) else { phase = .idle; deadline?.cancel(); return }
                phase = .answering
                notice = "Writing an answer on this device…"
                await generate(text, revision: current)
            } catch { finish(error, revision: current) }
        }
    }

    public func stopRecording() {
        guard phase == .listening else { return }
        phase = .transcribing
        notice = "Finishing the transcript…"
        speech.stop()
    }

    public func cancel() async {
        revision += 1
        let current = revision
        operation?.cancel()
        deadline?.cancel()
        phase = .cancelling
        await speech.cancel()
        guard current == revision else { return }
        phase = .idle
        answer = ""
        notice = "Cancelled. You can start again."
    }

    public func clear() async {
        await cancel()
        transcript = ""
        notice = "Speak or type a question."
    }

    private func begin(_ phase: Phase, notice: String) -> Int {
        revision += 1
        deadline?.cancel()
        answer = ""
        self.phase = phase
        self.notice = notice
        return revision
    }

    private func validate(_ text: String) -> Bool {
        guard !text.isEmpty else { notice = "No words were captured. Speak again or type a question."; return false }
        guard text.count <= Self.maximumInputCharacters else {
            notice = "Please shorten the question to 1,200 characters or fewer."
            return false
        }
        answerReadiness = answers.readiness
        guard answerReadiness.isReady else { notice = answerReadiness.message; return false }
        return true
    }

    private func generate(_ text: String, revision current: Int) async {
        do {
            try await answers.answer(text) { [weak self] text in
                guard let self, self.revision == current else { return }
                self.answer = text
            }
            try Task.checkCancellation()
            guard current == revision else { return }
            phase = .idle
            deadline?.cancel()
            notice = answer.isEmpty ? "The local model returned no text. Try again." : "Answer complete."
        } catch { finish(error, revision: current) }
    }

    private func finish(_ error: Error, revision current: Int) {
        guard current == revision else { return }
        deadline?.cancel()
        phase = .idle
        answer = ""
        notice = error is CancellationError ? "Cancelled. You can start again." :
            (error as? VoiceError)?.localizedDescription ?? "The local operation could not finish. Please try again."
    }

    private func armDeadline(seconds: Int, revision current: Int) {
        deadline = Task { [weak self] in
            do { try await Task.sleep(for: .seconds(seconds)) } catch { return }
            guard let self, self.revision == current, self.isBusy else { return }
            await self.cancel()
            self.notice = "This request took too long and was cancelled. Try a shorter question."
        }
    }
}
