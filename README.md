# SOMR-CD (Windows setup guide)

This repository contains a small audio demo app that records voice, detects utterances (VAD), and responds by playing a WAV or speaking via TTS. Windows is the primary target environment.

## Requirements
- Windows 10/11
- Python 3.9+ (3.10 推奨)
- Git

## Quick start (Windows PowerShell)
```powershell
# 1) Clone
git clone https://github.com/<YOUR_USERNAME>/SOMR-CD.git
cd SOMR-CD

# 2) Create & activate virtual environment
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4) Run (examples)
#   A) End-of-utterance playback mode (plays a WAV at end of detected speech)
python src\hello_demo\cli.py --mode end --wav-file .\audio\konnichiwa.wav

#   B) Keyword mode (STT -> match -> respond)
#      By default, STT=auto (tries Google, then Vosk). See notes below.
python src\hello_demo\cli.py --mode keyword --tts wav --wav-file .\audio\konnichiwa.wav

#   Options you may want to try
#   --gate hotkey --hotkey SPACE --arm-window-ms 3000
#   --keywords-file .\keywords.json
#   --sequence-file .\sequence.json --loop-sequence
```

## Project layout (excerpt)
```
src/hello_demo/
  app.py          # main app logic
  cli.py          # command-line entry
  audio_io.py     # recording, VAD (sounddevice)
  playback.py     # WAV playback (winsound on Windows)
```

## Common options
- `--mode`: `end` or `keyword`
- `--tts`: `wav` (play a file) or `pyttsx3`
- `--stt`: `auto`, `google`, `vosk` (used only when `--mode keyword`)
- `--wav-file`: path to a WAV to play
- `--keywords-file`: JSON mapping for keyword->response
- `--sequence-file`: file/JSON listing WAVs to play sequentially (for mode=end)
- `--gate`: `none` | `nth` | `every` | `hotkey`

## Dependencies
`requirements.txt` includes:
- sounddevice
- numpy
- pyttsx3
- (Optional) google-cloud-speech
- (Optional) vosk

On Windows, `winsound` is part of the standard library, so no extra player library is needed. On non-Windows systems, `simpleaudio` may be required to play WAVs.

If you plan to use optional STT backends:
- Google Cloud Speech-to-Text: `pip install google-cloud-speech` and set `GOOGLE_APPLICATION_CREDENTIALS` to your service account JSON.
- Vosk: `pip install vosk` and download a model (see Vosk docs). Place under `models/` and point the app accordingly if needed.

## Data files
- Audio samples are expected under `./audio/`. Example default: `.\audio\konnichiwa.wav`.
- `keywords.json` and `sequence.json` are optional helper files. If present, point to them with `--keywords-file` or `--sequence-file`.
- Large assets like models should be placed under `./models/` (ignored by Git by default).

## Troubleshooting
- Microphone not found / device errors: specify `--device <index>` or check sound settings.
- No response in hotkey mode: press SPACE (or configured key) within the arm window after "armed" log appears.
- Sounddevice installation issues: upgrade pip (`python -m pip install --upgrade pip`) and reinstall wheels. Most Windows setups work out-of-the-box.

## Development
```powershell
# Lint/format (if you add tooling later)
# ruff, black, mypy, etc. can be added as needed
```

## License
Private repository. Usage restricted to collaborators.

## Windows quick commands (PowerShell)
```powershell
# 1) 依存インストール（仮想環境は任意）
pip install sounddevice numpy pyttsx3 vosk

# 2) パッケージを見せる
$env:PYTHONPATH = "$PWD\src"

# 3-A) VAD × ホットキー × シーケンス（SPACE→次の発話終端で次のWAV）
python -m hello_demo.gui --mode end --tts wav --device 1 `
  --gate hotkey --hotkey SPACE --arm-window-ms 3000 `
  --sequence-file .\sequence.json

# 3-B) キーワード版（Vosk）
# 先に Vosk モデルのパスを設定（例）
# $env:VOSK_MODEL_PATH = "C:\vosk\vosk-model-ja-0.22"
python -m hello_demo.gui --mode keyword --stt vosk `
>>     --keywords-file .\keywords.json --device 1 `
>>     --tts voicevox `
>>     --voicevox-url http://127.0.0.1:50021 `
>>     --voicevox-speaker 3
```
