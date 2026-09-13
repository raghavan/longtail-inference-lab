import Foundation
import Testing
@testable import LocalVoiceCore

@MainActor private final class ControlledAnswers: AnswerEngine {
    var readiness: Readiness = .ready
    struct Request {
        let text: String
        let update: @MainActor (String) -> Void
        let continuation: CheckedContinuation<Void, any Error>
    }
    var requests: [Request] = []
    func answer(_ text: String, update: @escaping @MainActor (String) -> Void) async throws {
        try await withCheckedThrowingContinuation { continuation in
            requests.append(Request(text: text, update: update, continuation: continuation))
        }
    }
    func complete(_ index: Int, text: String) {
        requests[index].update(text)
        requests[index].continuation.resume()
    }
}

@MainActor private final class ControlledSpeech: SpeechInput {
    var text = "A synthetic spoken question."
    var cancelled = 0
    func readiness() async -> Readiness { .ready }
    func prepare() async throws {}
    func record(update: @escaping @MainActor (String) -> Void, started: @escaping @MainActor () -> Void) async throws -> String {
        started()
        update(text)
        return text
    }
    func stop() {}
    func cancel() async { cancelled += 1 }
}

@Suite @MainActor struct ConversationTests {
    private func eventually(_ condition: () -> Bool) async {
        for _ in 0..<1_000 {
            if condition() { return }
            await Task.yield()
        }
        #expect(condition())
    }

    @Test func emptyAndOversizedInputNeverReachTheModel() async {
        let answers = ControlledAnswers()
        let model = Conversation(answers: answers, speech: ControlledSpeech())
        model.transcript = "   "
        model.ask()
        #expect(answers.requests.isEmpty)
        #expect(model.phase == .idle)
        model.transcript = String(repeating: "x", count: 1_201)
        model.ask()
        #expect(answers.requests.isEmpty)
        #expect(model.notice.contains("1,200"))
    }

    @Test func unavailableModelPreservesTheQuestion() async {
        let answers = ControlledAnswers()
        answers.readiness = .unavailable("Model unavailable")
        let model = Conversation(answers: answers, speech: ControlledSpeech())
        model.transcript = "A question"
        model.ask()
        #expect(model.transcript == "A question")
        #expect(model.notice == "Model unavailable")
        #expect(answers.requests.isEmpty)
    }

    @Test func partialAnswerRemainsBusyUntilCompletion() async {
        let answers = ControlledAnswers()
        let model = Conversation(answers: answers, speech: ControlledSpeech())
        model.transcript = "A question"
        model.ask()
        await eventually { answers.requests.count == 1 }
        answers.requests[0].update("First words")
        #expect(model.answer == "First words")
        #expect(model.phase == .answering)
        answers.complete(0, text: "A complete answer.")
        await eventually { model.phase == .idle }
        #expect(model.answer == "A complete answer.")
    }

    @Test func cancelledAnswerCannotOverwriteANewerRequest() async {
        let answers = ControlledAnswers()
        let speech = ControlledSpeech()
        let model = Conversation(answers: answers, speech: speech)
        model.transcript = "First question"
        model.ask()
        await eventually { answers.requests.count == 1 }
        await model.cancel()
        #expect(model.phase == .idle)
        #expect(model.answer.isEmpty)
        model.transcript = "Second question"
        model.ask()
        await eventually { answers.requests.count == 2 }
        answers.requests[1].update("Current answer")
        answers.complete(0, text: "Stale answer")
        for _ in 0..<10 { await Task.yield() }
        #expect(model.answer == "Current answer")
        #expect(model.phase == .answering)
        answers.complete(1, text: "Current answer finished.")
        await eventually { model.phase == .idle }
        #expect(model.answer == "Current answer finished.")
    }

    @Test func speechFeedsItsFinalTranscriptToTheAnswerModel() async {
        let answers = ControlledAnswers()
        let speech = ControlledSpeech()
        let model = Conversation(answers: answers, speech: speech)
        await model.refresh()
        model.record()
        await eventually { answers.requests.count == 1 }
        #expect(answers.requests[0].text == speech.text)
        #expect(model.transcript == speech.text)
        answers.complete(0, text: "A synthetic answer.")
        await eventually { model.phase == .idle }
    }

    @Test func failureDiscardsPartialOutputAndAllowsRetry() async {
        let answers = ControlledAnswers()
        let model = Conversation(answers: answers, speech: ControlledSpeech())
        model.transcript = "A question"
        model.ask()
        await eventually { answers.requests.count == 1 }
        answers.requests[0].update("Partial")
        answers.requests[0].continuation.resume(throwing: VoiceError.message("Local test failure"))
        await eventually { model.phase == .idle }
        #expect(model.answer.isEmpty)
        #expect(model.notice == "Local test failure")
        #expect(model.transcript == "A question")
    }
}
