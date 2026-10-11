"""Render GD level frames with the game's real sprites.

Sprite placement and draw order follow GDRWeb by IliasHDZ (MIT, https://github.com/iliasHDZ/GDRWeb): object
sprite table (assets/object.json), sprite quad = offset + (contentSize - cropSize)/2, object model = translate *
rotate(with warp) * scale(with flips), batches per Z layer and sprite sheet, blending sprites before normal ones,
objects sorted by Z order. Sprite sheets are RobTop's and are NOT stored in this repo: point GDRWEB_ASSETS at a
GDRWeb checkout's assets/ folder (or your own GD Resources with matching -hd sheets).

State at a time t: position-triggered colour/alpha/toggle/move triggers and spawn chains are simulated roughly
(linear easing, no pulses, no rotate/follow/keyframes). Good enough to see composition, palette and layering.
"""
import json
import math
import os
import plistlib
import re
import sys
from functools import lru_cache

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gmd import load, x_to_time_fn, KA4_SPEED, NAMES, is_trigger, SPEED_PORTAL  # noqa: E402

ASSETS = os.environ.get('GDRWEB_ASSETS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref',
                                                      'GDRWeb', 'assets'))
SHEET_FILES = {'game1': 'GJ_GameSheet-hd', 'game2': 'GJ_GameSheet02-hd', 'fire': 'FireSheet_01-hd',
               'glow': 'GJ_GameSheetGlow-hd', 'pixel': 'PixelSheet_01-hd', 'particle': 'GJ_ParticleSheet-hd'}
SHEET_ORDER = {'glow': 0, 'particle': 1, 'pixel': 2, 'game2': 3, 'fire': 4, 'text': 5, 'special': 6, 'unknown': 7,
               'game1': 8}
ZRANK = {-5: 0, -3: 1, -1: 2, 1: 3, 3: 4, 5: 5, 7: 6, 9: 7, 11: 8}   # file values B5..T4

OBJ = json.load(open(os.path.join(ASSETS, 'object.json')))


def _vec(s):
    return [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', s)]


class Sheets:
    def __init__(self):
        self.frames, self.images = {}, {}
        for key, base in SHEET_FILES.items():
            pl = os.path.join(ASSETS, base + '.plist')
            if not os.path.exists(pl):
                continue
            p = plistlib.load(open(pl, 'rb'))
            for name, fr in p['frames'].items():
                x, y, w, h = _vec(fr['textureRect'])
                self.frames.setdefault(name, (key, x, y, w, h, bool(fr.get('textureRotated'))))

    def image(self, key):
        if key not in self.images:
            self.images[key] = np.asarray(Image.open(os.path.join(ASSETS, SHEET_FILES[key] + '.png')).convert('RGBA'),
                                          dtype=np.float32) / 255.0
        return self.images[key]

    @lru_cache(maxsize=4096)
    def sprite(self, name, fx, fy):
        if name not in self.frames:
            return None
        key, x, y, w, h, rot = self.frames[name]
        img = self.image(key)
        if rot:
            a = img[int(y):int(y + w), int(x):int(x + h)]
            a = np.rot90(a, 1)                     # restore: sprite-up was image-right
        else:
            a = img[int(y):int(y + h), int(x):int(x + w)]
        if fx:
            a = a[:, ::-1]
        if fy:
            a = a[::-1, :]
        return np.ascontiguousarray(a)


SHEETS = None


def rgb_to_hsv(c):
    import colorsys
    return colorsys.rgb_to_hsv(*c)


def apply_hsv(rgb, hsv):
    import colorsys
    try:
        p = hsv.split('a')
        h, s, v, sa, va = float(p[0]), float(p[1]), float(p[2]), p[3] == '1', p[4] == '1'
    except Exception:
        return rgb
    hh, ss, vv = colorsys.rgb_to_hsv(*rgb)
    hh = (hh + h / 360.0) % 1.0
    ss = min(1, max(0, ss + s if sa else ss * s))
    vv = min(1, max(0, vv + v if va else vv * v))
    return colorsys.hsv_to_rgb(hh, ss, vv)


class State:
    """Colour channels, group opacity/visibility/offset at song time t."""

    def __init__(self, L, t, tfx):
        self.L = L
        self.col = {}
        for ch, d in L['colors'].items():
            self.col[ch] = dict(rgb=(float(d.get('1', 255)) / 255, float(d.get('2', 255)) / 255, float(d.get('3', 255)) / 255),
                                op=float(d.get('7', 1) or 1), bl=d.get('5') == '1', copy=int(d.get('9', 0) or 0),
                                hsv=d.get('10'))
        self.alpha, self.hidden, self.off = {}, set(), {}
        events = []                                   # (start_time, trigger)
        trig = [o for o in L['objs'] if o['_id'] in (899, 1007, 1049, 901, 1268)]
        by_group = {}
        for o in trig:
            for g in (o.get('57') or '').split('.'):
                if g:
                    by_group.setdefault(int(g), []).append(o)
        for o in trig:
            if o.get('62') == '1' or o.get('11') == '1':
                continue
            st = tfx(o['_x'])
            if st <= t:
                events.append((st, o))
        # expand spawn chains (bounded)
        pending = [e for e in events if e[1]['_id'] == 1268]
        seen = 0
        while pending and seen < 4000:
            st, sp = pending.pop()
            seen += 1
            t2 = st + float(sp.get('63', 0) or 0)
            if t2 > t:
                continue
            for o in by_group.get(int(sp.get('51', 0) or 0), []):
                if o.get('62') == '1':
                    events.append((t2, o))
                    if o['_id'] == 1268:
                        pending.append((t2, o))
        events.sort(key=lambda e: e[0])
        self.cam_locks = []
        for st, o in events:
            oid = o['_id']
            dur = float(o.get('10', 0) or 0)
            k = 1.0 if dur <= 0 else max(0.0, min(1.0, (t - st) / dur))
            if oid == 899:
                ch = int(o.get('23', 1) or 1)
                prev = self.col.get(ch, dict(rgb=(1, 1, 1), op=1, bl=False, copy=0, hsv=None))
                tgt = (float(o.get('7', 255)) / 255, float(o.get('8', 255)) / 255, float(o.get('9', 255)) / 255)
                cp = int(o.get('50', 0) or 0)
                if cp:
                    self.col[ch] = dict(prev, copy=cp, hsv=o.get('49'), op=float(o.get('35', 1) or 1),
                                        bl=o.get('17') == '1')
                else:
                    rgb = tuple(a + (b - a) * k for a, b in zip(prev['rgb'], tgt))
                    op = prev['op'] + (float(o.get('35', 1) or 1) - prev['op']) * k
                    self.col[ch] = dict(rgb=rgb, op=op, bl=o.get('17') == '1', copy=0, hsv=None)
            elif oid == 1007:
                g = int(o.get('51', 0) or 0)
                a0 = self.alpha.get(g, 1.0)
                self.alpha[g] = a0 + (float(o.get('35', 1) or 0) - a0) * k
            elif oid == 1049:
                g = int(o.get('51', 0) or 0)
                (self.hidden.discard if o.get('56') == '1' else self.hidden.add)(g)
            elif oid == 901:
                g = int(o.get('51', 0) or 0)
                if o.get('141') == '1' or o.get('58') == '1':
                    self.cam_locks.append((g, st, dur, float(o.get('143', 1) or 1) if o.get('141') == '1' else 1.0))
                    continue
                if o.get('100') == '1':
                    continue
                dx, dy = float(o.get('28', 0) or 0) * k, float(o.get('29', 0) or 0) * k
                ox, oy = self.off.get(g, (0.0, 0.0))
                self.off[g] = (ox + dx, oy + dy)

    def color(self, ch, depth=0):
        if ch == 1010:
            return (0, 0, 0), 1.0, False
        if ch in (1011, 1012):
            return (1, 1, 1), 1.0, False
        if ch == 1005:
            return (0.49, 1, 0), 1.0, True
        if ch == 1006:
            return (0, 1, 1), 1.0, True
        c = self.col.get(ch)
        if c is None:
            return (1, 1, 1), 1.0, False
        rgb = c['rgb']
        if c['copy'] and depth < 8:
            base, _, _ = self.color(c['copy'], depth + 1)
            rgb = apply_hsv(base, c['hsv']) if c['hsv'] else base
        return rgb, c['op'], c['bl']


def render(L, t, tfx, xfn, cam_x=None, cam_y=None, W=570, H=320, S=2, player=None, show_triggers=False, filt=None):
    global SHEETS
    if SHEETS is None:
        SHEETS = Sheets()
    st = State(L, t, tfx)
    c = xfn(t) if cam_x is None else cam_x
    xl = c - 160
    yb = cam_y if cam_y is not None else -60
    # camera-locked groups (parallax): offset grows with camera movement since the trigger
    cam_off = {}
    for g, t0, dur, mod in st.cam_locks:
        t1 = min(t, t0 + dur) if dur > 0 else t
        cam_off[g] = cam_off.get(g, 0.0) + mod * (xfn(t1) - xfn(t0))
    bg, _, _ = st.color(1000)
    canvas = np.zeros((H * S, W * S, 3), np.float32) + np.array(bg, np.float32)
    items = []
    for idx, o in enumerate(L['objs']):
        oid = o['_id']
        if is_trigger(oid) or oid in (31, 3642) or o.get('135') == '1':
            continue
        info = OBJ.get(str(oid))
        if not info:
            continue
        if filt is not None and not filt(o):
            continue
        gs = [int(g) for g in (o.get('57') or '').split('.') if g]
        if any(g in st.hidden for g in gs):
            continue
        dx = dy = 0.0
        alpha = 1.0
        for g in gs:
            ox, oy = st.off.get(g, (0, 0))
            dx += ox + cam_off.get(g, 0.0)
            dy += oy
            alpha *= st.alpha.get(g, 1.0)
        x, y = o['_x'] + dx, o['_y'] + dy
        if x < xl - 400 or x > xl + W + 400 or y < yb - 400 or y > yb + H + 400:
            continue
        if alpha <= 0.01:
            continue
        zl = int(o.get('24', 0) or 0)
        zlayer = zl if zl in ZRANK else info.get('defaultZLayer', 3)
        zorder = int(float(o.get('25', 0) or 0)) if '25' in o else int(info.get('defaultZOrder', 0) or 0)
        s = float(o.get('32', 1) or 1)
        sx = s * float(o.get('128', 1) or 1) * (-1 if o.get('4') == '1' else 1)
        sy = s * float(o.get('129', 1) or 1) * (-1 if o.get('5') == '1' else 1)
        rot = float(o.get('6', 0) or 0)
        ax = -math.radians(rot + float(o.get('131', 0) or 0))
        ay = -math.radians(rot + float(o.get('132', 0) or 0))
        # model matrix columns: x axis rotated by ax, y axis rotated by ay (GDRWeb swaps warp angles)
        M = np.array([[math.cos(ax) * sx, -math.sin(ay) * sy, x], [math.sin(ax) * sx, math.cos(ay) * sy, y]])
        base_ch = int(o.get('21', 0) or 0) or info.get('defaultBaseColorChannel', 1011) or 1011
        det_ch = int(o.get('22', 0) or 0) or info.get('defaultDetailColorChannel', 0) or 1011
        for sp in info['sprites']:
            ct = sp['colorType']
            if ct == 'glow':
                continue
            ch = det_ch if ct == 'detail' else base_ch
            rgb, op, bl = st.color(ch)
            if ct == 'black':
                rgb = (0, 0, 0)
            hsv = o.get('43') if ct == 'base' and o.get('41') == '1' else (o.get('44') if ct == 'detail' and o.get('42') == '1' else None)
            if hsv:
                rgb = apply_hsv(rgb, hsv)
            a = op * alpha
            if a <= 0.01:
                continue
            sheet = info.get('spriteSheet', 'game1')
            items.append(((ZRANK.get(zlayer, 4), SHEET_ORDER.get(sheet, 8), 0 if bl else 1, zorder, idx),
                          M, sp, rgb, a, bl))
    items.sort(key=lambda it: it[0])
    for _, M, sp, rgb, a, bl in items:
        _draw_sprite(canvas, M, sp, rgb, a, bl, xl, yb, H, S)
    img = Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8))
    if player is not None:
        from PIL import ImageDraw
        px, py = player
        d = ImageDraw.Draw(img)
        d.rectangle(((px - 15 - xl) * S, (H - (py + 30 - yb)) * S, (px + 15 - xl) * S, (H - (py - yb)) * S),
                    outline=(125, 255, 0), width=3)
    return img


def _draw_sprite(canvas, M, sp, rgb, a, bl, xl, yb, H, S):
    arr = SHEETS.sprite(sp['texture'], bool(sp.get('flipX')), bool(sp.get('flipY')))
    if arr is None:
        return
    hp, wp = arr.shape[:2]
    cw, ch = wp / 2.0, hp / 2.0                                  # -hd sheets: 2 px per point
    offx, offy = sp['spriteOffset']
    if sp.get('flipX'):
        offx = -offx
    if sp.get('flipY'):
        offy = -offy
    cs = sp['contentSize']
    ox, oy = offx + (cs[0] - cw) / 2, offy + (cs[1] - ch) / 2
    # sprite transform: translate(position) * rotate(rotation) * scale(scale)
    pr = math.radians(sp.get('rotation', 0) or 0)
    ssx, ssy = sp['scale']
    px, py = sp['position']
    Ts = np.array([[math.cos(pr) * ssx, -math.sin(pr) * ssy, px], [math.sin(pr) * ssx, math.cos(pr) * ssy, py]])
    # local point from texture pixel (u right, v down): (ox + u/2, oy + ch - v/2)
    L0 = np.array([[0.5, 0, ox], [0, -0.5, oy + ch]])
    def comp(A, B):
        return np.array([[A[0, 0] * B[0, 0] + A[0, 1] * B[1, 0], A[0, 0] * B[0, 1] + A[0, 1] * B[1, 1], A[0, 0] * B[0, 2] + A[0, 1] * B[1, 2] + A[0, 2]],
                         [A[1, 0] * B[0, 0] + A[1, 1] * B[1, 0], A[1, 0] * B[0, 1] + A[1, 1] * B[1, 1], A[1, 0] * B[0, 2] + A[1, 1] * B[1, 2] + A[1, 2]]])
    Wm = comp(M, comp(Ts, L0))                                  # texture px -> world
    Sm = np.array([[S, 0, -xl * S], [0, -S, (H + yb) * S]])      # world -> screen px
    F = comp(Sm, Wm)                                             # texture px -> screen px
    corners = [F @ np.array([u, v, 1.0]) for u, v in ((0, 0), (wp, 0), (wp, hp), (0, hp))]
    xs, ys = [p[0] for p in corners], [p[1] for p in corners]
    X0, X1 = int(math.floor(max(0, min(xs)))), int(math.ceil(min(canvas.shape[1], max(xs))))
    Y0, Y1 = int(math.floor(max(0, min(ys)))), int(math.ceil(min(canvas.shape[0], max(ys))))
    if X1 <= X0 or Y1 <= Y0 or (X1 - X0) * (Y1 - Y0) > 6e6:
        return
    A = F[:, :2]
    det = A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0]
    if abs(det) < 1e-9:
        return
    Ai = np.array([[A[1, 1], -A[0, 1]], [-A[1, 0], A[0, 0]]]) / det
    bi = -Ai @ F[:, 2]
    # PIL AFFINE maps output (x,y) [relative to X0,Y0] -> input (u,v)
    data = (Ai[0, 0], Ai[0, 1], Ai[0, 0] * X0 + Ai[0, 1] * Y0 + bi[0],
            Ai[1, 0], Ai[1, 1], Ai[1, 0] * X0 + Ai[1, 1] * Y0 + bi[1])
    tint = arr.copy()
    tint[..., :3] *= np.array(rgb, np.float32)
    tint[..., 3] *= a
    pre = tint.copy()
    pre[..., :3] *= pre[..., 3:4]                              # premultiply before resampling
    im = Image.fromarray((pre * 255).astype(np.uint8), 'RGBA')
    out = np.asarray(im.transform((X1 - X0, Y1 - Y0), Image.AFFINE, data, resample=Image.BILINEAR),
                     dtype=np.float32) / 255.0
    region = canvas[Y0:Y1, X0:X1]
    if bl:
        region += out[..., :3]
    else:
        region *= (1 - out[..., 3:4])
        region += out[..., :3]


def cam_y_for(L, x, default=-60, H=320):
    """Pick a camera bottom so the gameplay near x is framed (median of gameplay objects)."""
    ys = [o['_y'] for o in L['objs'] if abs(o['_x'] - x - 120) < 260 and (o['_id'] in (1, 8, 39, 103, 392, 216, 217, 218, 1715, 1716, 1717, 1718, 1719, 1720, 1721, 1722)
          or o['_id'] in (35, 36, 67, 84, 140, 141, 1022, 1330, 1332, 1333) or o['_id'] in SPEED_PORTAL)]
    if not ys:
        return default
    ys.sort()
    mid = ys[len(ys) // 2]
    return mid - H * 0.45


def sheet(path, times, out, cols=2, S=1, label=True):
    L = load(path)
    tfn, _ = x_to_time_fn(L['objs'], KA4_SPEED.get(int(L['header'].get('kA4', 0) or 0), '1x'))
    xs = list(range(-300, int(max(o['_x'] for o in L['objs'])) + 60, 5))
    def xfn(t):
        lo, hi = -300.0, float(xs[-1])
        for _ in range(40):
            m = (lo + hi) / 2
            if tfn(m) < t:
                lo = m
            else:
                hi = m
        return lo
    frames = []
    for t in times:
        c = xfn(t)
        img = render(L, t, tfn, xfn, cam_y=cam_y_for(L, c), S=S)
        if label:
            from PIL import ImageDraw
            ImageDraw.Draw(img).text((6, 4), '%s  t=%.1fs' % (L['name'], t), fill=(255, 255, 0))
        frames.append(img)
    w, h = frames[0].size
    rows = (len(frames) + cols - 1) // cols
    sh = Image.new('RGB', (w * cols, h * rows), (25, 25, 25))
    for i, f in enumerate(frames):
        sh.paste(f, ((i % cols) * w, (i // cols) * h))
    sh.save(out)
    return out


if __name__ == '__main__':
    path, out = sys.argv[1], sys.argv[2]
    times = [float(v) for v in sys.argv[3].split(',')]
    print(sheet(path, times, out, S=int(sys.argv[4]) if len(sys.argv) > 4 else 1))
