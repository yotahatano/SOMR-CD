from __future__ import annotations
import io, os, wave, json
from vosk import Model, KaldiRecognizer
from .base import STTBase  # ← 既存の抽象基底（ある前提）

class VoskSTT(STTBase):
    def __init__(self, model_path: str | None = None, grammar_words: list[str] | None = None):
        mp = model_path or os.environ.get("VOSK_MODEL_PATH") or "model"
        self._model = Model(mp)
        # keywords.json 由来の語彙 → JSON 文字列で保持（None 可）
        self.grammar_json = (
            json.dumps(sorted(set(grammar_words)), ensure_ascii=False)
            if grammar_words else None
        )

    def transcribe(self, wav_bytes: bytes, sample_rate: int = 16000) -> str:
        """
        wav_bytes（RIFF/WAV or 裸PCM）を擬似ストリーミング処理。
        環境変数 VOSK_PRINT_PARTIALS=1 で partial を逐次 print。
        """
        print_partials = os.getenv("VOSK_PRINT_PARTIALS", "0") == "1"

        # 認識器の準備（あなたの環境では第3引数が未対応のため渡さない）
        rec = KaldiRecognizer(self._model, sample_rate)
        # 単語境界が不要なら False の方が軽い
        try:
            rec.SetWords(False)
        except Exception:
            pass

        gj = self.grammar_json  # JSON 文字列 or None
        if gj:
            try:
                rec.SetGrammar(gj)  # 通常はこちらが使える
            except AttributeError:
                # かなり古い版のみフォールバック（必要なければ削除可）
                rec = KaldiRecognizer(self._model, sample_rate, gj)

        # 入力が RIFF/WAV なら PCM を取り出す
        if len(wav_bytes) >= 12 and wav_bytes[:4] == b"RIFF" and wav_bytes[8:12] == b"WAVE":
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                if wf.getframerate() != sample_rate:
                    raise ValueError(f"sample_rate mismatch: {wf.getframerate()} vs {sample_rate}")
                if wf.getnchannels() != 1:
                    raise ValueError("mono required")
                if wf.getsampwidth() != 2:
                    raise ValueError("16-bit PCM required")
                pcm_bytes = wf.readframes(wf.getnframes())
        else:
            pcm_bytes = wav_bytes  # すでに裸PCM（16kHz/mono/16bit）想定

        # 100ms チャンクで擬似ストリーミング
        bytes_per_sec = sample_rate * 2  # 16-bit mono
        CHUNK = max(3200, bytes_per_sec // 10)  # ≈100ms
        i = 0
        last_final = ""

        while i < len(pcm_bytes):
            chunk = pcm_bytes[i:i+CHUNK]
            i += CHUNK

            if rec.AcceptWaveform(chunk):
                res = json.loads(rec.Result())
                txt = res.get("text", "")
                if print_partials and txt:
                    print(f"[FINAL ] {txt}")
                last_final = txt
            else:
                if print_partials:
                    pres = json.loads(rec.PartialResult())
                    ptxt = pres.get("partial", "")
                    if ptxt:
                        print(f"[PART  ] {ptxt}")

        res = json.loads(rec.FinalResult())
        txt = res.get("text", "") or last_final
        if print_partials and txt:
            print(f"[FINAL*] {txt}")
        return txt
