"""Synthesise the few sound effects the video uses (no external assets)."""
import wave
import numpy as np

SR = 44100
rng = np.random.default_rng(1453)


def t(d):
    return np.arange(int(SR * d)) / SR


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def save(name, x, peak=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    fade = min(len(x), int(0.01 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(f"public/sfx/{name}.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# deep cinematic impact
tt = t(2.2)
freq = 32 + 70 * np.exp(-tt * 5)
boom = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 1.8)
boom += lowpass(rng.standard_normal(len(tt)), 400) * np.exp(-tt * 9) * 1.5
save("boom", boom)

# chain rattle: a few metallic hits with inharmonic partials
tt = t(1.0)
clank = np.zeros_like(tt)
for start, gain in [(0.0, 1), (0.09, 0.7), (0.21, 0.85), (0.34, 0.5), (0.5, 0.35)]:
    n0 = int(start * SR)
    tl = tt[: len(tt) - n0]
    hit = sum(np.sin(2 * np.pi * f * tl + rng.uniform(0, 6)) * np.exp(-tl * d)
              for f, d in [(523, 14), (1371, 22), (2207, 30), (3413, 40), (4810, 55)])
    hit += rng.standard_normal(len(tl)) * np.exp(-tl * 120) * 0.8
    clank[n0:] += hit * gain
save("clank", clank, 0.8)

# whoosh
tt = t(0.9)
env = np.sin(np.pi * tt / 0.9) ** 3
noise = rng.standard_normal(len(tt))
whoosh = lowpass(noise, 1800) - lowpass(noise, 300)
save("whoosh", whoosh * env, 0.7)

# splash
tt = t(1.1)
splash = lowpass(rng.standard_normal(len(tt)), 2500) * np.exp(-tt * 4.5) * (1 - np.exp(-tt * 60))
splash += lowpass(rng.standard_normal(len(tt)), 600) * np.exp(-tt * 2.5) * 0.6
save("splash", splash, 0.75)

# wooden hull grinding over greased rollers
tt = t(5.0)
wob = 120 + 25 * np.sin(2 * np.pi * 0.7 * tt) + 10 * np.sin(2 * np.pi * 3.1 * tt)
saw = 2 * ((np.cumsum(wob) / SR) % 1) - 1
creak = lowpass(saw, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 1.3 * tt) ** 8)
creak += lowpass(rng.standard_normal(len(tt)), 160) * 2.5
creak *= np.minimum(1, tt / 0.5) * np.minimum(1, (5.0 - tt) / 0.8)
save("drag", creak, 0.6)

# stamp thud
tt = t(0.6)
thud = np.sin(2 * np.pi * (55 + 120 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
thud += lowpass(rng.standard_normal(len(tt)), 1200) * np.exp(-tt * 40)
save("thud", thud)
