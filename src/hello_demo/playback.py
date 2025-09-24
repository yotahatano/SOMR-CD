from __future__ import annotations
import os, platform, io, wave

class WavPlayback:
    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        if self.is_windows:
            import winsound  # type: ignore
            self._winsound = winsound
        else:
            try:
                import simpleaudio as sa  # type: ignore
            except Exception:
                sa = None
            self._sa = sa

    def play(self, path: str) -> None:
        """既存：ファイルパスから再生"""
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        if self.is_windows:
            self._winsound.PlaySound(path, self._winsound.SND_FILENAME)
        else:
            if self._sa is None:
                raise RuntimeError("simpleaudio not available")
            wave_obj = self._sa.WaveObject.from_wave_file(path)
            play_obj = wave_obj.play()
            play_obj.wait_done()

    def play_bytes(self, wav_bytes: bytes) -> None:
        """新規：WAV(PCM)のバイト列を直接再生"""
        if not wav_bytes:
            return
        if self.is_windows:
            # winsound はメモリ再生に対応（RIFF/WAVEヘッダ必須）
            self._winsound.PlaySound(wav_bytes, self._winsound.SND_MEMORY)
        else:
            if self._sa is None:
                raise RuntimeError("simpleaudio not available")
            # WAVヘッダからパラメタとフレームを取り出し、play_bufferで再生
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
            play_obj = self._sa.play_buffer(frames, n_channels, sampwidth, framerate)
            play_obj.wait_done()
