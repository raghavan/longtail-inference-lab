import SwiftUI
import LocalVoiceCore
#if os(macOS)
import AppKit
#endif

@main struct LocalVoiceApp: App {
    @State private var conversation = Conversation(answers: AppleAnswerEngine(), speech: AppleSpeechInput())
    var body: some Scene {
        WindowGroup("Local Voice") {
            ConversationView(conversation: conversation)
                .task { await conversation.refresh() }
                #if os(macOS)
                .frame(minWidth: 640, minHeight: 590)
                .onAppear {
                    NSApplication.shared.setActivationPolicy(.regular)
                    NSApplication.shared.activate(ignoringOtherApps: true)
                }
                #endif
        }
        #if os(macOS)
        .defaultSize(width: 760, height: 740)
        #endif
    }
}

struct ConversationView: View {
    @Environment(\.scenePhase) private var scenePhase
    @Bindable var conversation: Conversation
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 7) {
                        Text("Local Voice").font(.largeTitle.weight(.semibold))
                        Text("Speak a question. Read an answer.").foregroundStyle(.secondary)
                    }
                    Spacer()
                    Label("On this device", systemImage: "desktopcomputer")
                        .font(.caption.weight(.medium)).padding(9)
                        .background(.green.opacity(0.10), in: Capsule())
                }
                VStack(alignment: .leading, spacing: 10) {
                    readinessRow("Answers", state: conversation.answerReadiness)
                    readinessRow("Speech", state: conversation.speechReadiness)
                    if case .setupNeeded = conversation.speechReadiness {
                        Button("Prepare local speech") { conversation.prepareSpeech() }
                            .disabled(conversation.isBusy)
                        Text("One-time setup downloads English speech assets. Your questions are processed locally.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    if !conversation.answerReadiness.isReady {
                        Button("Check again") { Task { await conversation.refresh() } }
                            .disabled(conversation.isBusy)
                    }
                }
                .padding(16).frame(maxWidth: .infinity, alignment: .leading)
                .background(.quaternary.opacity(0.45), in: RoundedRectangle(cornerRadius: 14))

                VStack(alignment: .leading, spacing: 10) {
                    HStack {
                        Text("Your question").font(.headline)
                        Spacer()
                        Text("\(conversation.transcript.count) / 1,200").font(.caption).foregroundStyle(.secondary)
                    }
                    TextEditor(text: $conversation.transcript)
                        .font(.body).frame(minHeight: 120)
                        .padding(9).background(.background, in: RoundedRectangle(cornerRadius: 10))
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(.secondary.opacity(0.3)))
                        .disabled(conversation.isBusy)
                        .accessibilityLabel("Question or transcript")
                    Text("Record up to 30 seconds, or type here. You can edit the transcript and ask again.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                HStack(spacing: 12) {
                    if conversation.phase == .listening {
                        Button("Stop and answer", systemImage: "stop.fill") { conversation.stopRecording() }
                            .buttonStyle(.borderedProminent).tint(.red)
                    } else {
                        Button("Record", systemImage: "mic.fill") { conversation.record() }
                            .disabled(conversation.isBusy || !conversation.speechReadiness.isReady)
                    }
                    Button("Answer", systemImage: "arrow.up") { conversation.ask() }
                        .buttonStyle(.borderedProminent)
                        .disabled(conversation.isBusy || conversation.transcript.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !conversation.answerReadiness.isReady)
                        .keyboardShortcut(.return, modifiers: .command)
                    if conversation.isBusy {
                        Button("Cancel") { Task { await conversation.cancel() } }
                            .disabled(conversation.phase == .cancelling)
                    }
                    Spacer()
                    Button("Clear") { Task { await conversation.clear() } }.disabled(conversation.isBusy)
                }
                HStack(spacing: 9) {
                    if conversation.isBusy { ProgressView().controlSize(.small) }
                    Text(conversation.notice).font(.callout).foregroundStyle(.secondary)
                        .accessibilityLabel("Status: \(conversation.notice)")
                }
                VStack(alignment: .leading, spacing: 12) {
                    Text("Answer").font(.headline)
                    Text(conversation.answer.isEmpty ? "Your answer will appear here." : conversation.answer)
                        .foregroundStyle(conversation.answer.isEmpty ? .secondary : .primary)
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, minHeight: 110, alignment: .topLeading)
                }
                .padding(18).background(.quaternary.opacity(0.3), in: RoundedRectangle(cornerRadius: 14))
                Text("Early prototype · English · One question at a time. Audio and text are not saved by this app.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            .padding(28).frame(maxWidth: 900)
            .frame(maxWidth: .infinity)
        }
        .onDisappear { Task { await conversation.cancel() } }
        .onChange(of: scenePhase) { _, phase in
            if phase == .background { Task { await conversation.cancel() } }
        }
    }

    private func readinessRow(_ title: String, state: Readiness) -> some View {
        HStack(alignment: .top, spacing: 9) {
            Image(systemName: state.isReady ? "checkmark.circle.fill" : "circle.dashed")
                .foregroundStyle(state.isReady ? Color.green : Color.secondary)
            Text("\(title): \(state.message)").font(.callout)
        }
    }
}
