from __future__ import annotations
from typing import Optional, Any, List, Dict
import json, os, re, unicodedata, time, sys
from .config import Config
from .audio_io import VADRecorder, float_to_pcm16, pack_wav
from .tts import TTSBase
from .stt import STTBase
from .playback import WavPlayback

class HelloApp:
    def __init__(self, cfg: Config, tts_client: TTSBase, stt_client: Optional[STTBase] = None,
                 on_user=None, on_system=None):
        self.cfg = cfg
        self.tts = tts_client
        self.stt = stt_client
        self.playback = WavPlayback()
        self.on_user = on_user
        self.on_system = on_system

        self.keyword_map: List[Dict[str, Any]] | None = None
        if cfg.keywords_file and os.path.exists(cfg.keywords_file):
            try:
                with open(cfg.keywords_file, "r", encoding="utf-8") as f:
                    self.keyword_map = json.load(f)
                assert isinstance(self.keyword_map, list)
                print(f"[Keywords] Loaded {len(self.keyword_map)} entries from {cfg.keywords_file}")
            except Exception as e:
                print(f"[Keywords] Failed to load {cfg.keywords_file}: {e}")
                self.keyword_map = None

        self.utt_count = 0
        self._armed_until = 0.0
        self._is_windows = (sys.platform.startswith("win"))
        hk = (self.cfg.hotkey or "SPACE").upper()
        self._hotkey_space = (hk == "SPACE")
        self._hotkey_char = None if self._hotkey_space else (hk[0].lower())

        self.sequence: List[Dict[str, Any]] = []
        self.seq_idx: int = 0
        if cfg.sequence_file and os.path.exists(cfg.sequence_file):
            try:
                self.sequence = self._load_sequence(cfg.sequence_file)
                print(f"[VAD-Seq] Loaded {len(self.sequence)} items from {cfg.sequence_file}")
            except Exception as e:
                print(f"[VAD-Seq] Failed to load sequence: {e}")

    @staticmethod
    def _norm(s: str | None) -> str:
        if not s:
            return ""
        s = unicodedata.normalize("NFKC", s)
        s = "".join(s.split()).lower()
        return s

    def _match_from_map(self, text: str | None) -> dict | None:
        if not self.keyword_map:
            return None
        t = self._norm(text)
        for entry in self.keyword_map:
            patterns = entry.get("match") or entry.get("keywords") or []
            use_regex = bool(entry.get("regex"))
            for p in patterns:
                if use_regex:
                    try:
                        if re.search(p, text or ""):
                            return entry
                    except re.error as e:
                        print(f"[Keywords] Bad regex '{p}': {e}")
                else:
                    if self._norm(str(p)) in t:
                        return entry
        return None

    def _poll_hotkey(self):
        if not self.cfg or self.cfg.gate != "hotkey":
            return
        try:
            if self._is_windows:
                import msvcrt
                armed = False
                while msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if self._hotkey_space and ch == b" ":
                        armed = True
                    elif (not self._hotkey_space):
                        try:
                            c = ch.decode(errors="ignore").lower()
                            if c and c == self._hotkey_char:
                                armed = True
                        except Exception:
                            pass
                if armed:
                    self._armed_until = time.time() + (self.cfg.arm_window_ms / 1000.0)
                    print(f"[Gate] ARMED {self.cfg.arm_window_ms} ms ({'SPACE' if self._hotkey_space else self._hotkey_char})")
            else:
                pass
        except Exception as e:
            print(f"[Gate] hotkey poll error: {e}")

    def _should_play_vad(self) -> bool:
        self.utt_count += 1
        g = self.cfg.gate
        if g == "none":
            return True
        if g == "nth":
            if not self.cfg.respond_on:
                print(f"[Gate] nth: no --respond-on specified -> skip utter#{self.utt_count}")
                return False
            try:
                wanted = {int(x.strip()) for x in self.cfg.respond_on.split(",") if x.strip()}
            except Exception:
                print("[Gate] nth: bad --respond-on format -> skip")
                return False
            ok = (self.utt_count in wanted)
            if not ok:
                print(f"[Gate] nth: want {sorted(wanted)} -> skip utter#{self.utt_count}")
            return ok
        if g == "every":
            ok = (self.cfg.every_n and self.cfg.every_n > 0 and (self.utt_count % self.cfg.every_n == 0))
            if not ok:
                print(f"[Gate] every: N={self.cfg.every_n} -> skip utter#{self.utt_count}")
            return ok
        if g == "hotkey":
            now = time.time()
            ok = (now <= self._armed_until)
            if not ok:
                remaining_ms = int((self._armed_until - now) * 1000)
                print(f"[Gate] hotkey: not armed (remain {remaining_ms} ms) -> skip utter#{self.utt_count}")
            return ok
        return True

    def _load_sequence(self, path: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        if path.lower().endswith(".json"):
            data = json.load(open(path, "r", encoding="utf-8"))
            if isinstance(data, list):
                for it in data:
                    if isinstance(it, str):
                        items.append({"wav": it})
                    elif isinstance(it, dict):
                        if it.get("wav") or it.get("file"):
                            items.append({"wav": it.get("wav") or it.get("file"),
                                          "say": it.get("say") or it.get("text")})
            else:
                raise ValueError("sequence json must be a list")
        else:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s and not s.startswith("#"):
                        items.append({"wav": s})
        return items

    def _next_sequence_item(self) -> Dict[str, Any] | None:
        if not self.sequence:
            return None
        if self.seq_idx < len(self.sequence):
            entry = self.sequence[self.seq_idx]
            self.seq_idx += 1
            return entry
        if self.cfg.loop_sequence:
            self.seq_idx = 0
            entry = self.sequence[self.seq_idx]
            self.seq_idx += 1
            return entry
        return None

    def run(self) -> None:
        cfg = self.cfg
        rec = VADRecorder(
            rate=cfg.rate, block_ms=cfg.block_ms, energy_threshold=cfg.energy_threshold,
            min_speech_ms=cfg.min_speech_ms, min_silence_ms=cfg.min_silence_ms,
            device=cfg.device,
        )
        rec.start()
        print("\\nSpeak into the microphone. Ctrl+C to quit.\\n")
        try:
            while True:
                self._poll_hotkey()
                utter = rec.get_utterance()
                if utter is None:
                    continue
                pcm = float_to_pcm16(utter)
                wav_bytes = pack_wav(pcm, sample_rate=cfg.rate, num_channels=1)

                if cfg.mode == "end":
                    if not self._should_play_vad():
                        print(f"[VAD] utter#{self.utt_count}: gated -> skip")
                        continue
                    if self.on_user:
                        self.on_user(f"(発話 {len(utter)/cfg.rate:.2f}s)")
                    wav_path = cfg.wav_file
                    entry = self._next_sequence_item()
                    if entry:
                        wav_path = entry.get("wav") or wav_path
                        print(f"[VAD-Seq] next -> {wav_path}")
                    else:
                        if self.cfg.sequence_file:
                            print("[VAD-Seq] sequence finished; fallback to --wav-file")
                    print(f"[VAD] utter#{self.utt_count}: playing {wav_path}")
                    if self.on_system:
                        import os as _os
                        self.on_system(f"再生: {_os.path.basename(wav_path)}")
                    try:
                        self.playback.play(wav_path)
                    except Exception as e:
                        print(f"[TTS] WAV playback failed: {e}. Falling back to TTS.")
                        self.tts.speak(self.cfg.keyword)
                    self._armed_until = 0.0
                    continue

                if cfg.mode == "keyword":
                    if self.stt is None:
                        print("[Mode:keyword] No STT client provided.")
                        continue
                    text = self.stt.transcribe(wav_bytes, sample_rate=cfg.rate)
                    print(f"[STT] Transcript: {text}")
                    if self.on_user:
                        self.on_user(text or "")
                    if self.keyword_map:
                        entry = self._match_from_map(text)
                        if entry:
                            wav_path = entry.get("wav") or entry.get("file") or cfg.wav_file
                            say = entry.get("say") or entry.get("text") or cfg.keyword
                            print(f"[Mode:keyword] Matched entry -> wav={wav_path!r}")
                            if self.on_system:
                                import os as _os
                                self.on_system(f"再生: {_os.path.basename(wav_path)}")
                            if wav_path and os.path.exists(wav_path):
                                try:
                                    self.playback.play(wav_path)
                                except Exception as e:
                                    print(f"[TTS] WAV playback failed: {e}. Falling back to TTS.")
                                    self.tts.speak(say)
                            else:
                                self.tts.speak(say)
                        else:
                            print("[Mode:keyword] No mapping matched.")
                    else:
                        if text and cfg.keyword in text:
                            print("[Mode:keyword] Keyword detected. Responding...")
                            if self.on_system:
                                import os as _os
                                self.on_system(f"再生: {_os.path.basename(cfg.wav_file)}")
                            try:
                                self.playback.play(cfg.wav_file)
                            except Exception as e:
                                print(f"[TTS] WAV playback failed: {e}. Falling back to TTS.")
                                self.tts.speak(self.cfg.keyword)
                        else:
                            print("[Mode:keyword] Keyword not found.")
                    continue

                print(f"[App] Unknown mode: {cfg.mode}")
        except KeyboardInterrupt:
            print("\\n[Exit] Stopping...")
        finally:
            rec.stop()