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
        # Per-deck volume, 0.0 to 1.0
        self.volume = {"left": 1.0, "right": 1.0}
        # Per-deck, per-stem: True = include in mix (order: bass, drums, other, vocals)
        self.active_stems = {"left": [True, True, True, True], "right": [True, True, True, True]}

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
            for i, stem_data in enumerate(self.stems[side]):
                if not self.active_stems[side][i]:
                    continue
                slen = len(stem_data)
                mask = i0 < slen - 1
                idx = np.minimum(i0[mask], slen - 2)
                frac = t[mask]
                samples = stem_data[idx] * (1 - frac[:, None]) + stem_data[idx + 1] * frac[:, None]
                outdata[:n_valid][mask] += samples * self.volume[side]
            self.position[side] = pos + frames
        outdata *= 0.5
        np.clip(outdata, -1.0, 1.0, out=outdata)

    def play(self, side):
        self.playing[side] = True

    def pause(self, side):
        self.playing[side] = False

    def get_duration(self, side):
        """Return duration in samples for the given side, or 0 if no stems."""
        if not self.stems[side]:
            return 0
        return max(len(s) for s in self.stems[side])

    def get_position(self, side):
        """Return current play position in samples."""
        return self.position[side]

    def set_position(self, side, pos_samples):
        """Seek to position (in samples). Clamped to [0, duration]."""
        duration = self.get_duration(side)
        if duration <= 0:
            return
        self.position[side] = max(0.0, min(float(pos_samples), duration))

    def get_volume(self, side):
        """Return volume for side, 0.0 to 1.0."""
        return self.volume[side]

    def set_volume(self, side, value):
        """Set volume for side. Clamped to [0.0, 1.0]."""
        self.volume[side] = max(0.0, min(1.0, float(value)))

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
        self.active_stems[side] = [True, True, True, True]

    def set_stem_active(self, side, stem_index, active):
        """Enable or disable a stem in the mix (stem_index 0=bass, 1=drums, 2=other, 3=vocals)."""
        if 0 <= stem_index < 4:
            self.active_stems[side][stem_index] = bool(active)

    def toggle_stem(self, side, stem_index):
        """Toggle a stem on/off; returns new state."""
        if 0 <= stem_index < 4:
            self.active_stems[side][stem_index] = not self.active_stems[side][stem_index]
            return self.active_stems[side][stem_index]
        return False

    def close(self):
        self.stream.stop()
        self.stream.close()
