import Testing
@testable import LocalVoiceCore

@Suite struct SpeechVoiceTests {
    @Test func automaticVoicePrefersQualityOverRegionalMatch() {
        let standard = SpeechVoice(id: "us-standard", name: "Standard", language: "en-US", quality: .standard)
        let enhanced = SpeechVoice(id: "gb-enhanced", name: "Enhanced", language: "en-GB", quality: .enhanced)
        let premium = SpeechVoice(id: "us-premium", name: "Premium", language: "en-US", quality: .premium)
        #expect(SpeechVoice.preferred(in: [standard, enhanced]) == enhanced)
        #expect(SpeechVoice.preferred(in: [standard, enhanced, premium]) == premium)
        #expect(SpeechVoice.preferred(in: [standard, premium], identifier: standard.id) == standard)
        #expect(SpeechVoice.preferred(in: [standard, premium], identifier: "removed") == premium)
        #expect(SpeechVoice.preferred(in: []) == nil)
    }
}
