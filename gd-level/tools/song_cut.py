"""Cut 'Castle Of Shadows' (instrumental) on its exact 128 BPM grid. Bar n (1-based) starts at T0 + (n-1)*1.875 s."""
import numpy as np, soundfile as sf, json
x, sr = sf.read('full.wav')
g = json.load(open('grid128.json')); P = g['P']; T0 = g['t0']; B = 4 * P
def bar(n): return T0 + (n - 1) * B
segs = [(bar(0), bar(29)), (bar(69), bar(93)), (bar(125), 241.5)]
XF = 0.030
out = None; starts = []
for a, b in segs:
    ia, ib = int(round(a * sr)), int(round(b * sr))
    if out is None:
        out = x[ia:ib].copy(); starts.append(0.0); continue
    n = int(XF * sr); w = np.linspace(0, np.pi / 2, n)[:, None]
    out[-n:] = out[-n:] * np.cos(w) + x[ia - n:ia] * np.sin(w)
    starts.append(len(out) / sr)
    out = np.vstack([out, x[ia:ib]])
nf = int(1.5 * sr); out[-nf:] *= (np.linspace(1, 0, nf) ** 2)[:, None]
sf.write('cut.wav', out, sr)
info = dict(bpm=128.0, beat=P, bar=B, first_note_T=B, cut_segments=[dict(cut_T=s, orig_from=a, orig_to=b) for s, (a, b) in zip(starts, segs)],
            duration=len(out) / sr,
            sections_cut_bar={'lead-in': 0, 'intro': 1, 'A (beat in)': 5, 'B': 13, "A'": 21, 'break': 29, 'pre-drop fill': 36, 'C (drop)': 37, 'D': 45, 'outro hit': 53})
json.dump(info, open('cutmap.json', 'w'), indent=1)
print('duration %.3f s; segment starts %s (expected %.3f, %.3f)' % (len(out) / sr, ['%.3f' % s for s in starts], 29 * B, 53 * B))
