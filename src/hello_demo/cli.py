from __future__ import annotations
import argparse, sys, os
project_src = os.path.join(os.path.dirname(os.path.dirname(__file__)))
if project_src not in sys.path:
    sys.path.insert(0, project_src)
from .config import Config
from .app import HelloApp
from .tts import PyttsxTTS, WavResponder
from .stt import GoogleSTT, VoskSTT, STTBase

def build_tts(tts: str, wav_file: str):
    if tts == "pyttsx3":
        return PyttsxTTS()
    return WavResponder(wav_path=wav_file, fallback_tts=PyttsxTTS())

def build_stt(stt: str) -> STTBase | None:
    if stt == "google":
        return GoogleSTT()
    if stt == "vosk":
        return VoskSTT()
    if stt == "auto":
        try:
            return GoogleSTT()
        except Exception as e:
            print(f"[STT:auto] Google init failed: {e}")
        try:
            return VoskSTT()
        except Exception as e:
            print(f"[STT:auto] Vosk init failed: {e}")
            return None
    return None

def parse_args() -> Config:
    p = argparse.ArgumentParser(description="Hello Demo")
    p.add_argument("--mode", choices=["keyword","end"], default="keyword")
    p.add_argument("--tts", choices=["wav","pyttsx3"], default="wav")
    p.add_argument("--stt", choices=["auto","google","vosk"], default="auto")
    p.add_argument("--device", type=int, default=None)
    p.add_argument("--rate", type=int, default=16000)
    p.add_argument("--block-ms", type=int, default=30)
    p.add_argument("--energy-threshold", type=float, default=0.015)
    p.add_argument("--min-speech-ms", type=int, default=200)
    p.add_argument("--min-silence-ms", type=int, default=500)
    p.add_argument("--keyword", type=str, default="こんにちは")
    p.add_argument("--wav-file", type=str, default="./audio/konnichiwa.wav")
    p.add_argument("--keywords-file", type=str, default=None)
    p.add_argument("--gate", choices=["none","nth","every","hotkey"], default="none")
    p.add_argument("--respond-on", type=str, default=None)
    p.add_argument("--every-n", type=int, default=None)
    p.add_argument("--hotkey", type=str, default="SPACE")
    p.add_argument("--arm-window-ms", type=int, default=3000)
    p.add_argument("--sequence-file", type=str, default=None)
    p.add_argument("--loop-sequence", action="store_true")
    a = p.parse_args()
    return Config(
        mode=a.mode, tts=a.tts, stt=a.stt, device=a.device,
        rate=a.rate, block_ms=a.block_ms, energy_threshold=a.energy_threshold,
        min_speech_ms=a.min_speech_ms, min_silence_ms=a.min_silence_ms,
        keyword=a.keyword, wav_file=a.wav_file, keywords_file=a.keywords_file,
        gate=a.gate, respond_on=a.respond_on, every_n=a.every_n,
        hotkey=a.hotkey, arm_window_ms=a.arm_window_ms,
        sequence_file=a.sequence_file, loop_sequence=a.loop_sequence,
    )

def main():
    cfg = parse_args()
    tts_client = build_tts(cfg.tts, cfg.wav_file)
    stt_client = build_stt(cfg.stt) if cfg.mode == "keyword" else None
    app = HelloApp(cfg, tts_client, stt_client)
    print(f"[Config] {cfg}")
    app.run()

if __name__ == "__main__":
    main()