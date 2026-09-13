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
    var beforeRecording: (() -> Void)?
    func readiness() async -> Readiness { .ready }
    func prepare() async throws {}
    func record(update: @escaping @MainActor (String) -> Void, started: @escaping @MainActor () -> Void) async throws -> String {
        beforeRecording?()
        started()
        update(text)
        return text
    }
    func stop() {}
    func cancel() async { cancelled += 1 }
}

@MainActor private final class ControlledOutput: SpeechOutput {
    var state = Readiness.ready
    var spoken: [String] = []
    var completions: [@MainActor () -> Void] = []
    var active = false
    var voices = [SpeechVoice(id: "test-standard", name: "Test voice", language: "en-US", quality: .standard),
                  SpeechVoice(id: "test-premium", name: "Test voice", language: "en-US", quality: .premium)]
    var preferredVoiceIdentifier: String?
    var selectedVoice: SpeechVoice? { SpeechVoice.preferred(in: voices, identifier: preferredVoiceIdentifier) }
    func selectVoice(_ identifier: String?) { preferredVoiceIdentifier = identifier }
    var readiness: Readiness { state }
    func speak(_ text: String, finished: @escaping @MainActor () -> Void) throws {
        active = true
        spoken.append(text)
        completions.append(finished)
    }
    func stop() { active = false }
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

    @Test func completedAnswerIsSilentUntilExplicitReadAloud() async {
        let answers = ControlledAnswers()
        let output = ControlledOutput()
        let model = Conversation(answers: answers, speech: ControlledSpeech(), output: output)
        model.transcript = "A question"
        model.ask()
        await eventually { answers.requests.count == 1 }
        model.readAloud()
        #expect(output.spoken.isEmpty)
        answers.complete(0, text: "A completed answer.")
        await eventually { model.phase == .idle }
        #expect(output.spoken.isEmpty)
        model.readAloud()
        #expect(output.spoken.first == model.answer)
        #expect(model.isSpeaking)
        output.completions[0]()
        #expect(!model.isSpeaking)
        #expect(model.answer == "A completed answer.")
    }

    @Test func recordingStopsPlaybackBeforeOpeningTheMicrophone() async {
        let answers = ControlledAnswers()
        let output = ControlledOutput()
        let speech = ControlledSpeech()
        let model = Conversation(answers: answers, speech: speech, output: output)
        speech.beforeRecording = { #expect(!output.active); #expect(!model.isSpeaking) }
        await model.refresh()
        await completeAnswer(model, answers: answers)
        model.readAloud()
        #expect(output.active)
        model.record()
        await eventually { answers.requests.count == 2 }
        #expect(!output.active)
        answers.complete(1, text: "A completed answer.")
        await eventually { model.phase == .idle }
    }

    private func completeAnswer(_ model: Conversation, answers: ControlledAnswers) async {
        let index = answers.requests.count
        model.transcript = "A synthetic question."
        model.ask()
        await eventually { answers.requests.count == index + 1 }
        answers.complete(index, text: "A completed synthetic answer.")
        await eventually { model.phase == .idle }
    }

    @Test func oldPlaybackCompletionCannotFinishNewPlayback() async {
        let answers = ControlledAnswers()
        let output = ControlledOutput()
        let model = Conversation(answers: answers, speech: ControlledSpeech(), output: output)
        await completeAnswer(model, answers: answers)
        model.readAloud()
        model.stopSpeaking()
        model.readAloud()
        output.completions[0]()
        #expect(model.isSpeaking)
        output.completions[1]()
        #expect(!model.isSpeaking)
    }

    @Test func clearingDuringPlaybackStopsSpeechAndDiscardsText() async {
        let answers = ControlledAnswers()
        let output = ControlledOutput()
        let model = Conversation(answers: answers, speech: ControlledSpeech(), output: output)
        await completeAnswer(model, answers: answers)
        model.readAloud()
        #expect(output.active)
        await model.clear()
        #expect(!output.active)
        #expect(!model.isSpeaking)
        #expect(model.transcript.isEmpty)
        #expect(model.answer.isEmpty)
        output.completions[0]()
        #expect(model.notice == "Speak or type a question.")
    }

    @Test func audioInterruptionStopsPlaybackAndKeepsTheCompletedAnswer() async {
        let answers = ControlledAnswers()
        let output = ControlledOutput()
        let model = Conversation(answers: answers, speech: ControlledSpeech(), output: output)
        await completeAnswer(model, answers: answers)
        let answer = model.answer
        let question = model.transcript
        model.readAloud()
        await model.interruptAudio()
        #expect(!output.active)
        #expect(!model.isSpeaking)
        #expect(model.answer == answer)
        #expect(model.transcript == question)
        let notice = model.notice
        output.completions[0]()
        await model.interruptAudio()
        #expect(model.notice == notice)
    }

    @Test func audioInterruptionDiscardsPartialAndLateOutput() async {
        let answers = ControlledAnswers()
        let speech = ControlledSpeech()
        let model = Conversation(answers: answers, speech: speech)
        model.transcript = "A synthetic question."
        model.ask()
        await eventually { answers.requests.count == 1 }
        answers.requests[0].update("A partial answer")
        await model.interruptAudio()
        #expect(model.phase == .idle)
        #expect(speech.cancelled == 1)
        #expect(model.answer.isEmpty)
        #expect(model.transcript == "A synthetic question.")
        answers.complete(0, text: "A late answer")
        for _ in 0..<10 { await Task.yield() }
        #expect(model.answer.isEmpty)
        #expect(model.notice == "Audio was interrupted. You can start again.")
    }

    @Test func missingVoiceDoesNotEraseTheAnswer() async {
        let answers = ControlledAnswers()
        let output = ControlledOutput()
        output.state = .unavailable("Missing voice")
        let model = Conversation(answers: answers, speech: ControlledSpeech(), output: output)
        await completeAnswer(model, answers: answers)
        let answer = model.answer
        model.readAloud()
        #expect(output.spoken.isEmpty)
        #expect(!model.isSpeaking)
        #expect(model.answer == answer)
        #expect(model.notice == "Missing voice")
    }
    @Test func changingVoiceStopsPlaybackAndPreservesTheAnswer() async {
        let answers = ControlledAnswers()
        let output = ControlledOutput()
        let model = Conversation(answers: answers, speech: ControlledSpeech(), output: output)
        await completeAnswer(model, answers: answers)
        model.readAloud()
        let answer = model.answer
        model.selectVoice("test-standard")
        #expect(!model.isSpeaking)
        #expect(!output.active)
        #expect(model.answer == answer)
        #expect(model.selectedVoice?.id == "test-standard")
        #expect(output.preferredVoiceIdentifier == "test-standard")
        output.completions[0]()
        #expect(!model.isSpeaking)
        model.previewVoice()
        #expect(model.answer == answer)
        #expect(model.isSpeaking)
        #expect(output.spoken.last?.contains("Everything you hear") == true)
    }

    @Test func removedVoiceReturnsToTheBestInstalledVoice() async {
        let output = ControlledOutput()
        let model = Conversation(answers: ControlledAnswers(), speech: ControlledSpeech(), output: output)
        model.selectVoice("test-premium")
        model.previewVoice()
        output.voices.removeAll { $0.id == "test-premium" }
        model.refreshVoices()
        #expect(!model.isSpeaking)
        #expect(model.selectedVoiceIdentifier.isEmpty)
        #expect(model.selectedVoice?.id == "test-standard")
    }

}
