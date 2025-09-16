from __future__ import annotations
import io, os, wave, json
class VoskSTT:
    def __init__(self, model_path: str | None = None):
        try:
            from vosk import Model, KaldiRecognizer  # type: ignore
        except Exception as e:
            raise RuntimeError("vosk is required for VoskSTT") from e
        self._Model = Model
        self._KaldiRecognizer = KaldiRecognizer
        mp = model_path or os.environ.get("VOSK_MODEL_PATH")
        if not mp or not os.path.isdir(mp):
            raise RuntimeError("VOSK model path not set or invalid. Set VOSK_MODEL_PATH or pass model_path.")
        self._model = self._Model(mp)
    def transcribe(self, audio_wav_bytes: bytes, sample_rate: int) -> str | None:
        rec = self._KaldiRecognizer(self._model, sample_rate)
        rec.SetWords(False)
        wf = wave.open(io.BytesIO(audio_wav_bytes), "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise RuntimeError("Vosk expects 16-bit mono WAV")
        text_parts = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                j = json.loads(rec.Result())
                if j.get("text"):
                    text_parts.append(j["text"])
        j = json.loads(rec.FinalResult())
        if j.get("text"):
            text_parts.append(j["text"])
        trans = " ".join(text_parts).strip()
        return trans or None