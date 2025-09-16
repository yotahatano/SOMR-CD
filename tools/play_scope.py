# tools/play_scope.py
import argparse, wave, threading, time, numpy as np
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# 単純なWAV再生（Windowsならwinsound、他はsimpleaudio）
def play_wav(path):
    import platform
    if platform.system() == 'Windows':
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME)
    else:
        import simpleaudio as sa
        sa.WaveObject.from_wave_file(path).play().wait_done()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wav-file', required=True)
    args = ap.parse_args()

    with wave.open(args.wav_file, 'rb') as wf:
        n, rate, ch, sw = wf.getnframes(), wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
        y = np.frombuffer(wf.readframes(n), dtype={1:np.int8,2:np.int16,4:np.int32}[sw])
        if ch>1: y = y.reshape(-1,ch)[:,0]
        y = y.astype(np.float32) / np.iinfo({1:np.int8,2:np.int16,4:np.int32}[sw]).max
    t = np.arange(len(y)) / rate

    fig, ax = plt.subplots(figsize=(8,3))
    ax.plot(t, y); ax.set_xlim(0, t[-1]); ax.set_ylim(-1, 1)
    head = ax.axvline(0, color='r'); ax.set_title(args.wav_file)

    start = None
    th = threading.Thread(target=play_wav, args=(args.wav_file,), daemon=True)
    start = time.time(); th.start()

    def update(_):
        x = time.time() - start
        head.set_xdata([min(x, t[-1])])
        return (head,)

    import matplotlib.animation as animation
    ani = animation.FuncAnimation(fig, update, interval=30, blit=True)
    plt.show()

if __name__ == '__main__':
    main()
