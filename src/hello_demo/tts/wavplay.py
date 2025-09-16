from __future__ import annotations
import os
from .base import TTSBase
from ..playback import WavPlayback
class WavResponder(TTSBase):
    def __init__(self, wav_path: str, fallback_tts: "PyttsxTTS|None" = None):
        self.wav_path = wav_path
        self.playback = WavPlayback()
        self.fallback = fallback_tts
    def speak(self, text: str) -> None:
        if os.path.exists(self.wav_path):
            try:
                self.playback.play(self.wav_path)
                return
            except Exception as e:
                print(f"[TTS] WAV playback failed: {e}")
        if self.fallback is not None:
            self.fallback.speak(text)
        else:
            print("[TTS] No playback available.")