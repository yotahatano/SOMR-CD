from __future__ import annotations
import time, queue
from tkinter import Tk, Text, END
from tkinter import ttk
class SimpleUI:
    def __init__(self, title: str = "Hello Demo UI"):
        self.root = Tk(); self.root.title(title)
        self.q: queue.Queue[tuple[str, str]] = queue.Queue()
        frm = ttk.Frame(self.root, padding=8); frm.grid(sticky="nsew")
        self.root.rowconfigure(0, weight=1); self.root.columnconfigure(0, weight=1)
        self.lbl_user = ttk.Label(frm, text="O: 認識（あなた）")
        self.lbl_sys  = ttk.Label(frm, text="A: 再生（システム）")
        self.txt_user = Text(frm, height=20, width=50, wrap="word")
        self.txt_sys  = Text(frm, height=20, width=50, wrap="word")
        self.lbl_status = ttk.Label(frm, text="status: -")
        self.lbl_user.grid(row=0, column=0, sticky="w")
        self.lbl_sys.grid(row=0, column=1, sticky="w")
        self.txt_user.grid(row=1, column=0, sticky="nsew", padx=(0,8))
        self.txt_sys.grid(row=1, column=1, sticky="nsew")
        self.lbl_status.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6,0))
        frm.rowconfigure(1, weight=1); frm.columnconfigure(0, weight=1); frm.columnconfigure(1, weight=1)
        self.root.after(50, self._pump)
    def enqueue(self, kind: str, text: str) -> None:
        self.q.put((kind, text))
    def _append(self, widget: Text, text: str) -> None:
        ts = time.strftime("%H:%M:%S"); widget.insert(END, f"[{ts}] {text}\n"); widget.see(END)
    def _pump(self):
        try:
            while True:
                kind, text = self.q.get_nowait()
                if kind == "user": self._append(self.txt_user, text)
                elif kind == "system": self._append(self.txt_sys, text)
                elif kind == "status": self.lbl_status.config(text=f"status: {text}")
        except queue.Empty: pass
        self.root.after(50, self._pump)
    def run(self): self.root.mainloop()