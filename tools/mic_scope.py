# tools/mic_scope.py
import argparse, numpy as np, sounddevice as sd
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt, matplotlib.animation as animation

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--device', type=int, default=None)
    ap.add_argument('--rate', type=int, default=16000)
    ap.add_argument('--block-ms', type=int, default=20)
    ap.add_argument('--duration', type=float, default=2.0)  # 表示窓(秒)
    args = ap.parse_args()

    block = int(args.rate * (args.block_ms/1000.0))
    ring_len = int(args.rate * args.duration)
    ring = np.zeros(ring_len, dtype=np.float32)
    w = 0

    fig, ax = plt.subplots(figsize=(8,3))
    t = np.linspace(-args.duration, 0, ring_len)
    (line,) = ax.plot(t, ring)
    ax.set_ylim(-1, 1); ax.set_xlim(t[0], t[-1]); ax.set_xlabel('time (s)')

    def cb(indata, frames, time_info, status):
        nonlocal w, ring
        if status: print(status)
        x = indata[:,0] if indata.ndim==2 else indata
        n = len(x)
        end = w+n
        if end <= ring_len:
            ring[w:end] = x
        else:
            k = ring_len - w
            ring[w:] = x[:k]; ring[:n-k] = x[k:]
        w = (w + n) % ring_len

    stream = sd.InputStream(samplerate=args.rate, channels=1, dtype='float32',
                            blocksize=block, device=args.device, callback=cb)
    stream.start()

    def update(_):
        y = np.concatenate([ring[w:], ring[:w]])
        line.set_ydata(y)
        return (line,)

    ani = animation.FuncAnimation(fig, update, interval=args.block_ms, blit=True)
    plt.show()
    stream.stop(); stream.close()

if __name__ == '__main__':
    main()
