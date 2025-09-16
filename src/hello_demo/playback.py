from __future__ import annotations
import os, platform

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