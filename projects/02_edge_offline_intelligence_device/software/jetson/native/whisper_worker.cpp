// Small ABI boundary compiled against the pinned whisper.cpp header and library.
#include "whisper.h"
#include <cstdint>
#include <string>
#include <vector>
struct VoiceContext { whisper_context *ctx; std::string text; };
extern "C" {
void *lv_create(const char *model, int gpu) {
    auto p = whisper_context_default_params();
    p.use_gpu = gpu != 0; p.flash_attn = true; p.gpu_device = 0;
    auto ctx = whisper_init_from_file_with_params(model, p);
    return ctx ? new VoiceContext{ctx, {}} : nullptr;
}
const char *lv_transcribe(void *handle, const int16_t *pcm, int count, int threads) {
    if (!handle || count < 1600 || count > 480000 || threads < 1 || threads > 16) return nullptr;
    auto &v = *static_cast<VoiceContext *>(handle);
    std::vector<float> samples(count);
    for (int i = 0; i < count; ++i) samples[i] = pcm[i] / 32768.0f;
    auto p = whisper_full_default_params(WHISPER_SAMPLING_BEAM_SEARCH);
    p.greedy.best_of = whisper_full_default_params(WHISPER_SAMPLING_GREEDY).greedy.best_of;
    p.n_threads = threads; p.language = "en"; p.no_context = true;
    p.no_timestamps = true; p.print_realtime = false; p.print_progress = false;
    p.print_timestamps = false; p.print_special = false;
    v.text.clear();
    if (whisper_full(v.ctx, p, samples.data(), count) != 0) return nullptr;
    for (int i = 0; i < whisper_full_n_segments(v.ctx); ++i) {
        v.text += whisper_full_get_segment_text(v.ctx, i);
        if (v.text.size() > 4800) return nullptr;
    }
    return v.text.c_str();
}
void lv_destroy(void *handle) {
    if (handle) { auto v = static_cast<VoiceContext *>(handle); whisper_free(v->ctx); delete v; }
}
}
