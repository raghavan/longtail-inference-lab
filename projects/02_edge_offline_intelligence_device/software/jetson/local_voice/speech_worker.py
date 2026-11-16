"""Private pipe worker. No sockets, downloads, content logging, or disk cache."""
import ctypes
import json
from pathlib import Path
import sys
import wave


def main():
    role, root, backend, threads = sys.argv[1:]
    root = Path(root)
    handle = None
    lib = None
    if role == "tts":
        from piper import PiperVoice
        voice = PiperVoice.load(str(root / "models/en_US-ljspeech-medium.onnx"),
                                config_path=str(root / "models/en_US-ljspeech-medium.onnx.json"))
    elif role == "asr":
        lib = ctypes.CDLL(str(root / "bin" / backend / "local-voice-whisper.so"))
        lib.lv_create.argtypes = [ctypes.c_char_p, ctypes.c_int]
        lib.lv_create.restype = ctypes.c_void_p
        lib.lv_transcribe.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int16), ctypes.c_int, ctypes.c_int]
        lib.lv_transcribe.restype = ctypes.c_char_p
        lib.lv_destroy.argtypes = [ctypes.c_void_p]
        handle = lib.lv_create(str(root / "models/ggml-tiny.en.bin").encode(), backend == "cuda")
        if not handle:
            raise RuntimeError("load failed")
    else:
        raise ValueError("role")
    print('{"ready":true}', flush=True)
    try:
        while True:
            line = sys.stdin.buffer.readline(32769)
            if not line:
                return
            if len(line) > 32768 or not line.endswith(b"\n"):
                raise ValueError("request size")
            request = json.loads(line)
            # Only parent-owned transient paths can be read or written.
            path = Path(request["path"])
            if not path.is_absolute() or path.parent.parent != Path('/dev/shm') or not path.parent.name.startswith('local-voice-'):
                raise ValueError("path")
            if role == "tts":
                text = request["text"]
                if not isinstance(text, str) or not text.strip() or len(text) > 4000:
                    raise ValueError("text size")
                frames = 0
                with wave.open(str(path), 'wb') as wav:
                    for chunk in voice.synthesize(text):
                        if frames == 0:
                            wav.setnchannels(chunk.sample_channels)
                            wav.setsampwidth(chunk.sample_width)
                            wav.setframerate(chunk.sample_rate)
                        frames += len(chunk.audio_int16_bytes) // (chunk.sample_width * chunk.sample_channels)
                        if frames > chunk.sample_rate * 120:
                            raise ValueError("audio size")
                        wav.writeframes(chunk.audio_int16_bytes)
                result = {"ok": True}
            else:
                with wave.open(str(path), 'rb') as wav:
                    if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 16000) or not 1600 <= wav.getnframes() <= 480000:
                        raise ValueError("audio format")
                    pcm = wav.readframes(wav.getnframes())
                samples = (ctypes.c_int16 * (len(pcm) // 2)).from_buffer_copy(pcm)
                text = lib.lv_transcribe(handle, samples, len(samples), int(threads))
                if text is None:
                    raise RuntimeError("recognition failed")
                result = {"text": text.decode('utf-8')}
            print(json.dumps(result), flush=True)
            # Do not retain request text or audio buffers between requests.
            request = result = text = line = None
            if role == 'tts':
                chunk = None
            if role == 'asr':
                samples = pcm = None
    finally:
        if handle:
            lib.lv_destroy(handle)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Exit status signals failure; never expose input or native exception text.
        sys.exit(1)
