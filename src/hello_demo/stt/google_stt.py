from __future__ import annotations
class GoogleSTT:
    def __init__(self):
        try:
            from google.cloud import speech  # type: ignore
        except Exception as e:
            raise RuntimeError("google-cloud-speech is required for GoogleSTT") from e
        self._speech = speech
        self._client = speech.SpeechClient()
    def transcribe(self, audio_wav_bytes: bytes, sample_rate: int) -> str | None:
        speech = self._speech
        audio = speech.RecognitionAudio(content=audio_wav_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="ja-JP",
            enable_automatic_punctuation=False,
            model="latest_short",
        )
        resp = self._client.recognize(config=config, audio=audio)
        for result in resp.results:
            if result.alternatives:
                return result.alternatives[0].transcript.strip()
        return None