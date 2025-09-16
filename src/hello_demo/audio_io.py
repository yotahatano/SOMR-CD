from __future__ import annotations
import io, queue, time
import numpy as np
import sounddevice as sd

def float_to_pcm16(wave: np.ndarray) -> bytes:
    wave = np.asarray(wave)
    wave = np.clip(wave, -1.0, 1.0)
    return (wave * 32767.0).astype(np.int16).tobytes()

def pack_wav(pcm_bytes: bytes, sample_rate: int, num_channels: int = 1) -> bytes:
    import struct
    byte_rate = sample_rate * num_channels * 2
    block_align = num_channels * 2
    data_size = len(pcm_bytes)
    fmt_chunk_size = 16
    riff_chunk_size = 4 + (8 + fmt_chunk_size) + (8 + data_size)
    with io.BytesIO() as buf:
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", riff_chunk_size))
        buf.write(b"WAVE")
        buf.write(b"fmt ")
        buf.write(struct.pack("<IHHIIHH", fmt_chunk_size, 1, num_channels,
                              sample_rate, byte_rate, block_align, 16))
        buf.write(b"data")
        buf.write(struct.pack("<I", data_size))
        buf.write(pcm_bytes)
        return buf.getvalue()

class VADRecorder:
    def __init__(self, rate: int, block_ms: int, energy_threshold: float,
                 min_speech_ms: int, min_silence_ms: int, device=None):
        self.rate = rate
        self.block_ms = block_ms
        self.energy_threshold = energy_threshold
        self.min_speech_blocks = max(1, int(min_speech_ms / block_ms))
        self.min_silence_blocks = max(1, int(min_silence_ms / block_ms))
        self.block_samples = int(rate * (block_ms / 1000.0))
        self.device = device
        self.q: queue.Queue = queue.Queue()
        self.stream = None
        self.in_speech = False
        self.speech_blocks = 0
        self.silence_blocks = 0
        self.buffer = []

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[Audio] {status}")
        import numpy as _np
        data = _np.asarray(indata)
        if data.ndim == 2:
            data = data[:,0]
        self.q.put(data.copy())

    def start(self):
        self.stream = sd.InputStream(
            samplerate=self.rate, channels=1, dtype='float32',
            blocksize=self.block_samples, callback=self._callback,
            device=self.device,
        )
        self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    @staticmethod
    def _rms(x):
        import numpy as _np
        return float(_np.sqrt(_np.mean(_np.square(x))))

    def get_utterance(self, timeout=None):
        import numpy as _np
        deadline = None if timeout is None else time.time() + timeout
        while True:
            if deadline is not None and time.time() > deadline:
                return None
            try:
                block = self.q.get(timeout=0.1)
            except queue.Empty:
                continue
            rms = self._rms(block)
            voice = rms >= self.energy_threshold
            if voice:
                self.silence_blocks = 0
                self.speech_blocks += 1
                self.buffer.append(block)
                if not self.in_speech and self.speech_blocks >= self.min_speech_blocks:
                    self.in_speech = True
            else:
                if self.in_speech:
                    self.silence_blocks += 1
                    self.buffer.append(block)
                    if self.silence_blocks >= self.min_silence_blocks:
                        utter = _np.concatenate(self.buffer, axis=0)
                        tail = self.min_silence_blocks * self.block_samples
                        if len(utter) > tail:
                            utter = utter[:-tail]
                        self.in_speech = False
                        self.speech_blocks = 0
                        self.silence_blocks = 0
                        self.buffer = []
                        return utter
                else:
                    self.speech_blocks = 0
                    self.buffer = []