import Foundation
import AVFoundation
import LocalVoiceCore

@main struct LocalVoiceCheck {
    @MainActor static func main() async {
        do {
            let arguments = Array(CommandLine.arguments.dropFirst())
            let speech = AppleSpeechInput()
            let answers = AppleAnswerEngine()
            switch arguments.first ?? "--readiness" {
            case "--readiness":
                print("Development readiness check; not a performance measurement.")
                print("answers_ready=\(answers.readiness.isReady)")
                print("speech_ready=\(await speech.readiness().isReady)")
                print("voice_ready=\(AppleSpeechOutput().readiness.isReady)")
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
                guard arguments.count == 2 else { throw VoiceError.message("Supply one authored synthetic audio file.") }
                let transcript = try await speech.transcribeFile(URL(fileURLWithPath: arguments[1]))
                guard !transcript.isEmpty else { throw VoiceError.message("No transcript was returned.") }
                var answer = ""
                try await answers.answer(transcript) { answer = $0 }
                guard !answer.isEmpty else { throw VoiceError.message("No answer was returned.") }
                print("Synthetic audio-to-text-answer smoke check passed; microphone capture was not exercised.")
                print("Transcript: \(transcript)")
                print("Answer: \(answer)")
            case "--transcribe":
                guard arguments.count == 2 else { throw VoiceError.message("Supply one local audio file.") }
                let text = try await speech.transcribeFile(URL(fileURLWithPath: arguments[1]))
                guard !text.isEmpty else { throw VoiceError.message("No transcript was returned.") }
                print(text)
            case "--check-tts":
                try await SpeechProbe.run()
            default:
                throw VoiceError.message("Use --readiness, --prepare-speech, --check-answer, --check-tts, --check-voice AUDIO_FILE, or --transcribe AUDIO_FILE.")
            }
        } catch {
            // Keep diagnostics free of raw framework payloads and private host paths.
            print((error as? VoiceError)?.localizedDescription ?? "Local check failed; inspect readiness and local assets.")
            exit(1)
        }
    }
}

private enum SpeechProbe {
    struct Chunk: Sendable { let frames: Int; let nonzero: Bool }
    @MainActor static func run() async throws {
        guard let voice = AppleSpeechOutput.installedVoice() else {
            throw VoiceError.message("No installed English system voice.")
        }
        let sample = "Hello. This voice is generated on this device."
        let synthesizer = AVSpeechSynthesizer()
        let utterance = AVSpeechUtterance(string: sample)
        utterance.voice = voice
        let (stream, continuation) = AsyncStream<Chunk>.makeStream()
        let deadline = Task {
            do { try await Task.sleep(for: .seconds(20)) } catch { return }
            continuation.finish()
        }
        defer { deadline.cancel(); synthesizer.stopSpeaking(at: .immediate) }
        synthesizer.write(utterance, toBufferCallback: sink(continuation))
        var frames = 0
        var nonzero = false
        var finished = false
        for await chunk in stream {
            frames += chunk.frames
            nonzero = nonzero || chunk.nonzero
            if chunk.frames == 0 { finished = true }
        }
        guard finished, frames > 0, nonzero else { throw VoiceError.message("Synthetic speech did not complete with audible samples.") }
        print("Synthetic text-to-audio check passed; no speaker playback, recording, or quality score.")
        print("language=\(voice.language) voice=\(voice.identifier) frames=\(frames)")
    }

    nonisolated static func sink(_ continuation: AsyncStream<Chunk>.Continuation) -> @Sendable (AVAudioBuffer) -> Void {
        return { buffer in
            guard let pcm = buffer as? AVAudioPCMBuffer else { continuation.finish(); return }
            let frames = Int(pcm.frameLength)
            var nonzero = false
            if let samples = pcm.floatChannelData?[0] {
                nonzero = (0..<frames).contains { abs(samples[$0]) > 0.00001 }
            } else if let samples = pcm.int16ChannelData?[0] {
                nonzero = (0..<frames).contains { samples[$0] != 0 }
            }
            continuation.yield(Chunk(frames: frames, nonzero: nonzero))
            if frames == 0 { continuation.finish() }
        }
    }
}
