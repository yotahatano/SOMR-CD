# src/hello_demo/tts/__init__.py
from .base import TTSBase
from .pyttsx_tts import PyttsxTTS
from .voicevox_tts import VoiceVoxTTS  # ← 追加

__all__ = ["TTSBase", "PyttsxTTS","VoiceVoxTTS"]
