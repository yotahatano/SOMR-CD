= Hello Demo (OOP, multi-file) =

Layout:
  SOMR-CD/
  ├─ audio/                   (optional, put konnichiwa.wav here)
  ├─ creds/                   (optional, Google STT key JSON)
  ├─ models/vosk-ja/          (optional, Vosk JA model)
  └─ src/hello_demo/          (code)

Dependencies (Windows):
  pip install sounddevice numpy pyttsx3
  # Optional STT:
  pip install google-cloud-speech vosk

Run from project root (SOMR-CD):
  # Ensure Python sees ./src
  set PYTHONPATH=./src        (PowerShell: $env:PYTHONPATH = "$PWD\src")
  python -m hello_demo.cli --mode keyword --stt auto --tts wav --wav-file ./audio/konnichiwa.wav

  # Or simply cd into src and run:
  cd src
  python -m hello_demo.cli --mode end --tts pyttsx3

Notes:
  - On Windows, WAV playback uses built-in winsound (no simpleaudio needed).
  - If the WAV is missing, it falls back to pyttsx3.
  - For Google STT, set GOOGLE_APPLICATION_CREDENTIALS to creds JSON.
  - For Vosk, set VOSK_MODEL_PATH to models/vosk-ja/.
