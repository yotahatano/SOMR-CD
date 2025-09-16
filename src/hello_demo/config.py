from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    mode: str = "keyword"            # "keyword" or "end"
    tts: str = "wav"                  # "wav" or "pyttsx3"
    stt: str = "auto"                 # "auto", "google", "vosk"
    device: Optional[int] = None
    rate: int = 16000
    block_ms: int = 30
    energy_threshold: float = 0.015
    min_speech_ms: int = 200
    min_silence_ms: int = 500

    keyword: str = "こんにちは"
    wav_file: str = "./audio/konnichiwa.wav"

    keywords_file: Optional[str] = None

    gate: str = "none"                  # "none"|"nth"|"every"|"hotkey"
    respond_on: Optional[str] = None
    every_n: Optional[int] = None
    hotkey: str = "SPACE"
    arm_window_ms: int = 3000

    sequence_file: Optional[str] = None
    loop_sequence: bool = False