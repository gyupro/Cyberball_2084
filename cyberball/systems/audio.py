"""Audio system — generates simple tones via pygame.sndarray."""
import math
import pygame


def _make_tone(frequency, duration_ms, volume=0.3, sample_rate=22050):
    """Build a Sound from an array of sine samples. Returns None on failure."""
    try:
        import array
        n_samples = int(sample_rate * duration_ms / 1000)
        amplitude = int(32767 * volume)
        buf = array.array('h')
        for i in range(n_samples):
            # Short fade in/out to avoid clicks
            fade = min(1.0, i / 100, (n_samples - i) / 100)
            s = int(amplitude * fade * math.sin(2 * math.pi * frequency * i / sample_rate))
            buf.append(s)
            buf.append(s)  # stereo
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


class AudioSystem:
    def __init__(self):
        self.enabled = True
        self.volume = 0.4
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except pygame.error:
            self.enabled = False
            return
        self._init_sounds()

    def _init_sounds(self):
        specs = {
            'paddle_hit': (440, 80),
            'wall_hit':   (220, 60),
            'powerup':    (880, 200),
            'score':      (660, 300),
        }
        for name, (freq, dur) in specs.items():
            snd = _make_tone(freq, dur, self.volume)
            if snd:
                self.sounds[name] = snd

    def play(self, name):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd is not None:
            try:
                snd.play()
            except pygame.error:
                pass

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))
        for s in self.sounds.values():
            try:
                s.set_volume(self.volume)
            except pygame.error:
                pass

    def toggle_mute(self):
        self.enabled = not self.enabled
