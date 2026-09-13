import Foundation
import LocalVoiceCore

@main struct LocalVoiceCheck {
    @MainActor static func main() async {
        let speech = AppleSpeechInput()
        let answers = AppleAnswerEngine()
        do {
            switch CommandLine.arguments.dropFirst().first ?? "--readiness" {
            case "--readiness":
                print("Development readiness check; not a performance measurement.")
                print("answers_ready=\(answers.readiness.isReady)")
                print("speech_ready=\(await speech.readiness().isReady)")
            case "--prepare-speech":
                try await speech.prepare()
                print("speech_ready=\(await speech.readiness().isReady)")
            case "--check-answer":
                var answer = ""
                try await answers.answer("Explain why the sky looks blue in two short sentences.") { answer = $0 }
                guard !answer.isEmpty else { throw VoiceError.message("No answer was returned.") }
                print("Synthetic local answer smoke check passed; not a quality benchmark.")
                print(answer)
            case "--check-voice":
                guard CommandLine.arguments.count == 3 else { throw VoiceError.message("Supply one authored synthetic audio file.") }
                let transcript = try await speech.transcribeFile(URL(fileURLWithPath: CommandLine.arguments[2]))
                guard !transcript.isEmpty else { throw VoiceError.message("No transcript was returned.") }
                var answer = ""
                try await answers.answer(transcript) { answer = $0 }
                guard !answer.isEmpty else { throw VoiceError.message("No answer was returned.") }
                print("Synthetic audio-to-text-answer smoke check passed; microphone capture was not exercised.")
                print("Transcript: \(transcript)")
                print("Answer: \(answer)")
            case "--transcribe":
                guard CommandLine.arguments.count == 3 else { throw VoiceError.message("Supply one local audio file.") }
                let text = try await speech.transcribeFile(URL(fileURLWithPath: CommandLine.arguments[2]))
                guard !text.isEmpty else { throw VoiceError.message("No transcript was returned.") }
                print(text)
            default:
                throw VoiceError.message("Use --readiness, --prepare-speech, --check-answer, --check-voice AUDIO_FILE, or --transcribe AUDIO_FILE.")
            }
        } catch {
            // Keep diagnostics free of raw framework payloads and private host paths.
            print((error as? VoiceError)?.localizedDescription ?? "Local check failed; inspect readiness and local assets.")
            exit(1)
        }
    }
}
