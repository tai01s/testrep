import random, math, sys
from gen import *
from phys import SPEED
from PIL import Image, ImageDraw

def jitter_fn(kind, seed, W):
    rnd = random.Random(seed)
    cache = {}
    def f(i, p):
        d = 2 * FRAME * p.vx() if i < 1000 else 1 * FRAME * p.vx()
        if i >= 1000 and kind[0] == 'r': return 0.0
        if kind == 'none': return 0.0
        if kind == 'early': return -d
        if kind == 'late': return d
        if i not in cache: cache[i] = rnd.choice((-d, 0, d))
        return cache[i]
    return f

def verify(L, end_x, verbose=True):
    W, C = L.W, L.C
    W.index()
    fails = []
    results = []
    for vi in range(6):
        for jk in ('none', 'early', 'late', 'r1', 'r2'):
            p, tr, touched, mc = simulate(W, C, vi, jitter_fn(jk, hash(jk) & 0xffff, W), until=end_x, record=(jk == 'none'))
            ok = p.dead is None
            results.append((vi, jk, ok, round(p.x), p.dead, mc))
            if not ok: fails.append((vi, jk, p.dead))
            if verbose and not ok: print('FAIL', vi, jk, p.dead, 'mode', p.mode)
    return fails, results

def render(L, x0, x1, out, sc=0.5, trajs=()):
    W = L.W
    H = int(330 * sc); Wd = int((x1 - x0) * sc)
    im = Image.new('RGB', (Wd, H), (20, 18, 30)); d = ImageDraw.Draw(im)
    def Y(y): return H - (y + 15) * sc
    for (c, r) in W.cells:
        X = c * 30
        if x0 - 30 <= X <= x1:
            d.rectangle([(X - x0) * sc, Y(r * 30 + 30), (X + 30 - x0) * sc, Y(r * 30)], fill=(70, 70, 90), outline=(150, 120, 255))
    for (x, y, rot) in W.spikes:
        if x0 <= x <= x1:
            X = (x - x0) * sc
            if rot == 0: d.polygon([(X - 15 * sc, Y(y - 15)), (X + 15 * sc, Y(y - 15)), (X, Y(y + 15))], fill=(255, 60, 80))
            else: d.polygon([(X - 15 * sc, Y(y + 15)), (X + 15 * sc, Y(y + 15)), (X, Y(y - 15))], fill=(255, 60, 80))
    for pd in W.portals:
        if x0 <= pd['x'] <= x1:
            X = (pd['x'] - x0) * sc
            col = {'cube': (0, 255, 0), 'ship': (255, 0, 255), 'ball': (255, 140, 0), 'ufo': (255, 255, 0), 'wave': (0, 255, 255), 'speed': (255, 255, 255), 'grav': (0, 120, 255), 'mini': (255, 120, 200)}[pd['kind']]
            d.rectangle([X - 5 * sc, Y(pd['y'] + 45), X + 5 * sc, Y(pd['y'] - 45)], outline=col, width=2)
    cols = [(0, 255, 120), (255, 255, 0), (0, 200, 255), (255, 120, 0), (200, 200, 200), (255, 0, 255)]
    for i, tr in enumerate(trajs):
        pts = [((x - x0) * sc, Y(y)) for (x, y, *_ ) in tr if x0 <= x <= x1]
        if len(pts) > 1: d.line(pts, fill=cols[i % len(cols)], width=1)
    for gx in range(int(x0 // 300) * 300, int(x1) + 1, 300):
        d.text(((gx - x0) * sc + 2, 2), str(gx), fill=(255, 255, 0))
    im.save(out)
