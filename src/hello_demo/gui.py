from __future__ import annotations
import threading
from .cli import parse_args, build_tts, build_stt
from .app import HelloApp
from .ui_tk import SimpleUI
def main():
    cfg = parse_args()
    tts_client = build_tts(cfg.tts)
    stt_client = build_stt(cfg.stt) if cfg.mode == "keyword" else None
    ui = SimpleUI("Hello Demo UI")
    def on_user(text: str): ui.enqueue("user", text or "")
    def on_system(text: str): ui.enqueue("system", text or "")
    app = HelloApp(cfg, tts_client, stt_client, on_user=on_user, on_system=on_system)
    th = threading.Thread(target=app.run, daemon=True); th.start(); ui.run()
if __name__ == "__main__": main()