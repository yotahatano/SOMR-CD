from __future__ import annotations
class PyttsxTTS:
    def __init__(self):
        try:
            import pyttsx3  # type: ignore
        except Exception as e:
            raise RuntimeError("pyttsx3 is required for PyttsxTTS") from e
        self.engine = pyttsx3.init()
        try:
            voices = self.engine.getProperty("voices")
            for v in voices:
                if "ja" in (getattr(v, "id", "") or "").lower() or "japanese" in (getattr(v, "name", "") or "").lower():
                    self.engine.setProperty("voice", v.id)
                    break
        except Exception:
            pass
    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()