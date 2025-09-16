from __future__ import annotations
from abc import ABC, abstractmethod
class STTBase(ABC):
    @abstractmethod
    def transcribe(self, audio_wav_bytes: bytes, sample_rate: int) -> str | None:
        ...