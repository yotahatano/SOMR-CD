from __future__ import annotations
import argparse, sys, os
project_src = os.path.join(os.path.dirname(os.path.dirname(__file__)))
if project_src not in sys.path:
    sys.path.insert(0, project_src)
from .config import Config
from .app import HelloApp
from .tts import PyttsxTTS, VoiceVoxTTS
from .stt import GoogleSTT, VoskSTT, STTBase

def build_tts(name: str, **kwargs):
    from .tts import PyttsxTTS, VoiceVoxTTS
    if name == "pyttsx3":
        return PyttsxTTS()
    if name == "voicevox":
        return VoiceVoxTTS(
            engine_url=kwargs.get("engine_url", "http://127.0.0.1:50021"),
            speaker=int(kwargs.get("speaker", 46)),
            speed_scale=float(kwargs.get("speed_scale", 1.0)),
            pitch_scale=float(kwargs.get("pitch_scale", 0.0)),
            intonation_scale=float(kwargs.get("intonation_scale", 1.0)),
            volume_scale=float(kwargs.get("volume_scale", 1.0)),
        )
    raise ValueError(f"unknown tts: {name}")

def build_stt(name: str, **kwargs) -> STTBase | None:
    if name == "google":
        return GoogleSTT()
    if name == "vosk":
        from .stt import VoskSTT
        grammar_words = None
        kf = kwargs.get("keywords_file")
        # keywords.json から "match"/"keywords"（list形式）や dictキーを集める
        if kf and os.path.exists(kf):
            with open(kf, "r", encoding="utf-8") as f:
                data = json.load(f)
            words = []
            if isinstance(data, list):
                for e in data:
                    words += (e.get("match") or e.get("keywords") or [])
            elif isinstance(data, dict):
                # {"hello":"…","welcome":"…"} 形式ならキーを語彙に
                words += list(data.keys())
            # 文字列のみ＆重複排除
            grammar_words = sorted({w for w in words if isinstance(w, str) and w.strip()})
        return VoskSTT(
            model_path=os.environ.get("VOSK_MODEL_PATH") or "model",
            grammar_words=grammar_words  # ← メモリ上で渡す。ファイル不要
        )
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
    p.add_argument("--tts", choices=["pyttsx3", "voicevox"], default="voicevox")
    p.add_argument("--stt", choices=["auto","google","vosk"], default="auto")
    p.add_argument("--device", type=int, default=None)
    p.add_argument("--rate", type=int, default=16000)
    p.add_argument("--block-ms", type=int, default=20)
    p.add_argument("--energy-threshold", type=float, default=0.005)
    p.add_argument("--min-speech-ms", type=int, default=150)
    p.add_argument("--min-silence-ms", type=int, default=250)
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
    p.add_argument("--voicevox-url", default="http://127.0.0.1:50021")
    p.add_argument("--voicevox-speaker", type=int, default=3)
    p.add_argument("--voicevox-speed", type=float, default=1.0)
    p.add_argument("--voicevox-pitch", type=float, default=0.0)
    p.add_argument("--voicevox-intonation", type=float, default=1.0)
    p.add_argument("--voicevox-volume", type=float, default=1.0)
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