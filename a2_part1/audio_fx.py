from __future__ import annotations
import numpy as np
import pygame


def synth_tone(frequency=440.0, duration=0.12, volume=0.4, wave="sine"):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    if wave == "square":
        samples = np.sign(np.sin(2 * np.pi * frequency * t))
    else:
        samples = np.sin(2 * np.pi * frequency * t)
    envelope = np.linspace(1.0, 0.0, n_samples) ** 2  # quick decay, no click/pop at cutoff
    samples = (samples * envelope * volume * 32767).astype(np.int16)
    stereo = np.column_stack([samples, samples])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def load_or_synth(path, fallback_frequency, fallback_duration=0.12, fallback_wave="sine"):
    try:
        if path.exists():
            return pygame.mixer.Sound(str(path))
    except Exception:
        pass
    return synth_tone(fallback_frequency, fallback_duration, wave=fallback_wave)


SFX_SPEC = {
    "wall_pop":     dict(fallback_frequency=180.0, fallback_duration=0.08, fallback_wave="square"),
    "waypoint_pop": dict(fallback_frequency=520.0, fallback_duration=0.06, fallback_wave="sine"),
    "path_found":   dict(fallback_frequency=660.0, fallback_duration=0.18, fallback_wave="sine"),
    "goal_fanfare": dict(fallback_frequency=880.0, fallback_duration=0.30, fallback_wave="sine"),
    "invalid":      dict(fallback_frequency=110.0, fallback_duration=0.15, fallback_wave="square"),
}
