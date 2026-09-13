import Foundation

public struct SpeechVoice: Identifiable, Equatable, Sendable {
    public enum Quality: Int, Sendable {
        case standard = 1, enhanced, premium
        public var label: String {
            switch self {
            case .standard: return "Standard"
            case .enhanced: return "Enhanced"
            case .premium: return "Premium"
            }
        }
    }
    public let id: String
    public let name: String
    public let language: String
    public let quality: Quality
    public var label: String {
        let name = name.hasSuffix("(\(quality.label))") ? name : "\(name) (\(quality.label))"
        return "\(name) · \(language)"
    }

    public static func preferred(in voices: [SpeechVoice], identifier: String? = nil) -> SpeechVoice? {
        if let identifier, let selected = voices.first(where: { $0.id == identifier }) { return selected }
        return voices.sorted {
            if $0.quality != $1.quality { return $0.quality.rawValue > $1.quality.rawValue }
            if ($0.language == "en-US") != ($1.language == "en-US") { return $0.language == "en-US" }
            return $0.id < $1.id
        }.first
    }
}
