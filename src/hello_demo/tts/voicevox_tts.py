# src/hello_demo/tts/voicevox_tts.py
from __future__ import annotations
import io
import json
import wave
import requests

from .base import TTSBase

DEFAULT_ENGINE_URL = "http://127.0.0.1:50021"  # VoiceVox Engine の既定
DEFAULT_SPEAKER = 46  # 例: 四国めたん(ノーマル)。環境に応じて変更可。

class VoiceVoxTTS(TTSBase):
    """
    VoiceVox Engine (HTTP) を使って都度 TTS 生成する実装。
    生成した WAV バイト列を返す（再生は既存の playback/wavplay 側に委譲）。
    """

    def __init__(
        self,
        engine_url: str = DEFAULT_ENGINE_URL,
        speaker: int = DEFAULT_SPEAKER,
        speed_scale: float = 1.0,
        pitch_scale: float = 0.0,
        intonation_scale: float = 1.0,
        volume_scale: float = 1.0,
    ) -> None:
        self.engine_url = engine_url.rstrip("/")
        self.speaker = speaker
        self.speed_scale = speed_scale
        self.pitch_scale = pitch_scale
        self.intonation_scale = intonation_scale
        self.volume_scale = volume_scale

    def synth(self, text: str) -> bytes:
        """
        与えられたテキストを合成して WAV (byte) を返す。
        返り値は RIFF/WAVE のバイト列。
        """
        if not text or text.strip() == "":
            return b""

        # 1) audio_query
        q = requests.post(
            f"{self.engine_url}/audio_query",
            params={"text": text, "speaker": self.speaker},
            timeout=10,
        )
        q.raise_for_status()
        query = q.json()

        # optional: パラメタ調整
        query["speedScale"] = self.speed_scale
        query["pitchScale"] = self.pitch_scale
        query["intonationScale"] = self.intonation_scale
        query["volumeScale"] = self.volume_scale

        # 2) synthesis
        s = requests.post(
            f"{self.engine_url}/synthesis",
            params={"speaker": self.speaker, "enable_interrogative_upspeak": True},
            data=json.dumps(query),
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        s.raise_for_status()
        wav_bytes = s.content

        # 最低限の妥当性チェック（WAV ヘッダ）
        if not (len(wav_bytes) > 44 and wav_bytes[:4] == b"RIFF" and wav_bytes[8:12] == b"WAVE"):
            # 念のため RIFF ラッパを自作することもできるが、通常は不要
            # ここではシンプルに例外化
            raise RuntimeError("VoiceVox synthesis returned non-WAV data")
        return wav_bytes

    # 既存の TTSBase に合わせてメソッド名が違う場合は適宜 rename
    def speak(self, text: str) -> bytes:
        return self.synth(text)
