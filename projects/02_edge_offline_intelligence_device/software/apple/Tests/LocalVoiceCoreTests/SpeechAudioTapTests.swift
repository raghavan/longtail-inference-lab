import AVFoundation
import Foundation
import Speech
import Testing
@testable import LocalVoiceCore

@Suite @MainActor struct SpeechAudioTapTests {
    @Test func audioCallbackRunsOffMainActorAndOwnsItsOutput() async throws {
        let source = try #require(AVAudioFormat(standardFormatWithSampleRate: 48_000, channels: 1))
        let destination = try #require(AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: 16_000, channels: 1, interleaved: false))
        let (stream, continuation) = AsyncThrowingStream<AnalyzerInput, Error>.makeStream()
        // Construct on MainActor, exactly as record() does, then invoke on a
        // background executor. An inherited UI assertion would trap here.
        let tap = try #require(SpeechAudioTap.make(from: source, to: destination, continuation: continuation))
        try await Task.detached {
            dispatchPrecondition(condition: .notOnQueue(.main))
            let format = try #require(AVAudioFormat(standardFormatWithSampleRate: 48_000, channels: 1))
            let input = try #require(AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 9_600))
            input.frameLength = 9_600
            let samples = try #require(input.floatChannelData?[0])
            for index in 0..<9_600 { samples[index] = 0.25 }
            tap(input, AVAudioTime(sampleTime: 0, atRate: 48_000))
            // Simulate the hardware recycling its input before the analyzer
            // consumes anything. Converted samples must remain intact.
            for index in 0..<9_600 { samples[index] = 0 }
            continuation.finish()
        }.value

        var outputs: [AnalyzerInput] = []
        for try await input in stream { outputs.append(input) }
        let output = try #require(outputs.first?.buffer)
        #expect(outputs.count == 1)
        #expect(output.format.sampleRate == 16_000)
        #expect(output.format.commonFormat == .pcmFormatInt16)
        #expect(output.frameLength > 0)
        let samples = try #require(output.int16ChannelData?[0])
        #expect((0..<Int(output.frameLength)).contains { samples[$0] != 0 })
    }
}
