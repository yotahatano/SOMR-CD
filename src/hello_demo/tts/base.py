from __future__ import annotations
from abc import ABC, abstractmethod
class TTSBase(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        ...