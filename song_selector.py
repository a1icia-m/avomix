import sounddevice as sd
import soundfile as sf
import numpy as np

STEMS = ["bass", "drums", "other", "vocals"]

class SongSelector:
    def __init__(self, sr=44100):
        self.sr = sr
        self.stems = {"left": [], "right": []}
        self.playing = {"left": False, "right": False}
        self.position = {"left": 0.0, "right": 0.0}

        self.stream = sd.OutputStream(
            samplerate=sr,
            channels=2,
            dtype="float32",
            callback=self._callback,
        )
        self.stream.start()

    def _callback(self, outdata, frames, time, status):
        outdata[:] = 0
        for side in ["left", "right"]:
            if not self.playing[side] or not self.stems[side]:
                continue
            pos = self.position[side]
            max_len = max(len(s) for s in self.stems[side])
            if pos >= max_len:
                self.playing[side] = False
                continue
            read_positions = pos + np.arange(frames, dtype=np.float64)
            valid = read_positions < max_len
            if not np.any(valid):
                self.playing[side] = False
                continue
            rp = read_positions[valid]
            i0 = np.floor(rp).astype(np.int64)
            t = (rp - i0).astype(np.float32)
            n_valid = len(rp)
            for stem_data in self.stems[side]:
                slen = len(stem_data)
                mask = i0 < slen - 1
                idx = np.minimum(i0[mask], slen - 2)
                frac = t[mask]
                samples = stem_data[idx] * (1 - frac[:, None]) + stem_data[idx + 1] * frac[:, None]
                outdata[:n_valid][mask] += samples
            self.position[side] = pos + frames
        outdata *= 0.5
        np.clip(outdata, -1.0, 1.0, out=outdata)

    def play(self, side):
        self.playing[side] = True

    def pause(self, side):
        self.playing[side] = False

    def select(self, side, song):
        self.playing[side] = False
        loaded = []
        for stem in STEMS:
            data, _ = sf.read(f"songs/{song}/{stem}.mp3", dtype="float32")
            if data.ndim == 1:
                data = np.column_stack([data, data])
            loaded.append(data)
        self.stems[side] = loaded
        self.position[side] = 0.0

    def close(self):
        self.stream.stop()
        self.stream.close()
