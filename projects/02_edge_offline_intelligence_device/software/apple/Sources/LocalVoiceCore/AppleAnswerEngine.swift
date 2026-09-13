import Foundation
import FoundationModels

@MainActor public final class AppleAnswerEngine: AnswerEngine {
    public init() {}

    public var readiness: Readiness {
        switch SystemLanguageModel.default.availability {
        case .available: return .ready
        case .unavailable(.appleIntelligenceNotEnabled):
            return .unavailable("Enable Apple Intelligence to use local answers.")
        case .unavailable(.modelNotReady):
            return .unavailable("The local answer model is not ready. Check Apple Intelligence settings.")
        case .unavailable(.deviceNotEligible):
            return .unavailable("This device does not support Apple's local answer model.")
        case .unavailable:
            return .unavailable("The local answer model is unavailable.")
        }
    }

    public func answer(_ text: String, update: @escaping @MainActor (String) -> Void) async throws {
        try Task.checkCancellation()
        guard readiness.isReady else { throw VoiceError.message(readiness.message) }
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              text.count <= Conversation.maximumInputCharacters else {
            throw VoiceError.message("Enter a question of up to 1,200 characters.")
        }
        // A fresh, bounded session keeps the first development slice reproducible.
        let session = LanguageModelSession(model: .default, instructions: """
        Answer the user's question in clear, conversational language. Prefer a concise answer of
        about 100 words or fewer unless the question needs less. You have no web access or documents.
        State uncertainty when you do not know. Do not claim to have searched, checked current facts,
        or performed actions. Answer only the current question.
        """)
        let stream = session.streamResponse(to: text, options: GenerationOptions(maximumResponseTokens: 384))
        for try await response in stream {
            try Task.checkCancellation()
            update(response.content)
        }
        try Task.checkCancellation()
    }
}
