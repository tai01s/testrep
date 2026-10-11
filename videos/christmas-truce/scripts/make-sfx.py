"""Synthesise the sound effects the video uses (no external assets)."""
import wave
import numpy as np

SR = 44100
rng = np.random.default_rng(1914)


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
    fade = min(len(x), int(0.02 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    with wave.open(f"public/sfx/{name}.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def boom(d=2.5, f0=28, f1=60):
    tt = t(d)
    freq = f0 + f1 * np.exp(-tt * 4)
    x = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 1.4)
    x += lowpass(rng.standard_normal(len(tt)), 250) * np.exp(-tt * 2.2) * 2.5
    return x


# distant artillery barrage: a few rumbling booms
tt = t(4.0)
barrage = np.zeros_like(tt)
for start, g in [(0.0, 1), (0.7, 0.6), (1.5, 0.8), (2.6, 0.5)]:
    b = boom(1.4) * g
    n0 = int(start * SR)
    barrage[n0:n0 + len(b)] += b[: len(tt) - n0]
save("barrage", lowpass(barrage, 900), 0.8)

# single close impact (for the war resuming)
save("boom", boom(2.8, 30, 80))

# rifle cracks
tt = t(1.6)
rifles = np.zeros_like(tt)
for start, g in [(0.0, 1), (0.42, 0.5), (0.95, 0.7)]:
    n0 = int(start * SR)
    tl = tt[: len(tt) - n0]
    crack = rng.standard_normal(len(tl)) * np.exp(-tl * 70) + lowpass(rng.standard_normal(len(tl)), 500) * np.exp(-tl * 8) * 0.8
    rifles[n0:] += crack * g
save("rifles", rifles, 0.6)

# cold wind bed
tt = t(12.0)
n = rng.standard_normal(len(tt))
wind = lowpass(n, 500) - lowpass(n, 120)
wind *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt) * np.sin(2 * np.pi * 0.047 * tt + 1)
wind *= np.minimum(1, tt / 1.5) * np.minimum(1, (12 - tt) / 1.5)
save("wind", wind, 0.5)

# star-shell flare: rising hiss then pop
tt = t(2.0)
hiss = (lowpass(rng.standard_normal(len(tt)), 4000) - lowpass(rng.standard_normal(len(tt)), 900)) * np.minimum(1, tt / 0.8) * np.exp(-np.maximum(0, tt - 0.9) * 6)
hiss[int(0.9 * SR):] += (rng.standard_normal(len(tt) - int(0.9 * SR)) * np.exp(-tt[: len(tt) - int(0.9 * SR)] * 40))
save("flare", hiss, 0.5)

# soft church-bell chime
tt = t(4.0)
bell = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) * g for f, d, g in [(392, 0.9, 1), (784, 1.4, 0.5), (1046, 2.0, 0.35), (1568, 3.0, 0.2), (933, 1.2, 0.25)])
save("bell", bell * (1 - np.exp(-tt * 200)), 0.6)

# football kick
tt = t(0.35)
kick = np.sin(2 * np.pi * (90 + 160 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 18) + rng.standard_normal(len(tt)) * np.exp(-tt * 90) * 0.5
save("kick", kick, 0.8)

# page flip
tt = t(0.45)
flip = (lowpass(rng.standard_normal(len(tt)), 6000) - lowpass(rng.standard_normal(len(tt)), 1500)) * np.sin(np.pi * tt / 0.45) ** 2
save("flip", flip, 0.5)

# stamp thud
tt = t(0.6)
thud = np.sin(2 * np.pi * (55 + 120 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9) + lowpass(rng.standard_normal(len(tt)), 1200) * np.exp(-tt * 40)
save("thud", thud)

# soft whoosh for transitions
tt = t(0.9)
nn = rng.standard_normal(len(tt))
save("whoosh", (lowpass(nn, 1600) - lowpass(nn, 250)) * np.sin(np.pi * tt / 0.9) ** 3, 0.5)
