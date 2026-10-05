"""Deco building toolkit: allocates groups/channels and emits GD objects.

Geometry primitives
  rect/seg   : Colored Inner Square (211, 30x30 - confirmed by tiling in real
               levels) scaled + rotated.  Always NoTouch so it never collides.
  gtri/gpoly : Gradient trigger (2903) in vertex mode, drawing solid triangles
               between hidden corner markers.  Every shape is triangles with the
               3rd/4th corner slots sharing one group, so the result does not
               depend on which slot is BL/BR/TL/TR.  Both gradient colours use the
               same channel -> solid fill, no direction ambiguity.
  glow       : Large/Medium/Small Glow Orb (1888/1886/1887), round so rotation
               does not matter.
"""
import math
import random

from gdobj import (Obj, ROT, COLOR1, COLOR2, Z_LAYER, Z_ORDER, SCALE_X, SCALE_Y,
                   NO_TOUCH, HIDE, GROUPS, EDITOR_L1, HIGH_DETAIL, DONT_FADE,
                   DONT_ENTER, GRAD_LAYER, GRAD_BL, GRAD_BR, GRAD_TL, GRAD_TR,
                   GRAD_VERTEX, GRAD_PREVIEW_OPACITY, GRAD_BLEND, GRAD_ID, TARGET,
                   SECOND_TARGET, DURATION, EASING, EASE_RATE, MOVE_X, MOVE_Y,
                   LOCK_CAM_X, LOCK_CAM_Y, MOD_X, MOD_Y, RED, GREEN, BLUE,
                   OPACITY, BLENDING, TARGET_COLOR, FADE_IN, HOLD, FADE_OUT,
                   PULSE_TARGET_TYPE, SPAWN_TRIG, MULTI_TRIG, SPAWN_DELAY,
                   FOLLOW_XMOD, FOLLOW_YMOD, PARTICLE_DATA, QUICK_START, GL,
                   NO_GLOW, EXCLUSIVE)

# Glow orb diameters at scale 1 (in level units). Listed in the in-game
# checklist; everything scales from these.
GLOW_DIAM = {"L": 120.0, "M": 80.0, "S": 40.0}
GLOW_ID = {"L": 1888, "M": 1886, "S": 1887}

# editor layers (key 20) so the deco is easy to edit by hand afterwards
EL = {"far": 20, "mid": 21, "rock": 22, "rim": 23, "glow": 24, "thread": 25,
      "lava": 26, "particle": 27, "fg": 28, "trigger": 29, "corner": 30, "plat": 31}


class Scene:
    def __init__(self, group_start=200, channel_start=100, seed=7):
        self.objs = []
        self.channels = {}          # name -> dict(id, rgb, opacity, blending, copy)
        self._next_group = group_start
        self._next_channel = channel_start
        self.rng = random.Random(seed)
        self.corner_cache = {}
        self.grad_count = 0
        self.trig_y = {}            # trigger column stacking per x

    # ---------------------------------------------------------------- ids
    def group(self):
        g = self._next_group
        self._next_group += 1
        if g > 9999:
            raise ValueError("ran out of group ids")
        return g

    def chan(self, name, rgb, opacity=1.0, blending=False):
        if name in self.channels:
            return self.channels[name]["id"]
        cid = self._next_channel
        self._next_channel += 1
        self.channels[name] = dict(id=cid, rgb=tuple(int(c) for c in rgb),
                                   opacity=float(opacity), blending=bool(blending))
        return cid

    def ch(self, name):
        return self.channels[name]["id"]

    def add(self, o):
        self.objs.append(o)
        return o

    # ----------------------------------------------------------- objects
    def _deco(self, o, z, zo, groups, layer, high_detail):
        o.set(Z_LAYER, z)
        o.set(Z_ORDER, zo)
        o.set(EDITOR_L1, EL[layer])
        o.set(NO_GLOW, 1)
        o.set(DONT_FADE, 1)
        o.set(DONT_ENTER, 1)
        if high_detail:
            o.set(HIGH_DETAIL, 1)
        if groups:
            o.add_groups(*groups)
        return self.add(o)

    def rect(self, cx, cy, w, h, ch, z, zo=0, rot=0.0, groups=(), layer="rock",
             high_detail=False):
        if w <= 0 or h <= 0:
            return None
        o = Obj(211, cx, cy)
        o.set(COLOR1, ch)
        o.set(SCALE_X, round(w / 30.0, 4))
        o.set(SCALE_Y, round(h / 30.0, 4))
        if abs(rot) > 1e-6:
            o.set(ROT, round(rot, 3))
        o.set(NO_TOUCH, 1)
        return self._deco(o, z, zo, groups, layer, high_detail)

    MAX_SEG = 90.0   # long scaled objects get culled when their centre leaves the screen

    def seg(self, a, b, thick, ch, z, zo=0, groups=(), layer="rim", extend=0.0,
            high_detail=False):
        (ax, ay), (bx, by) = a, b
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        if L < 0.5:
            return None
        ang = math.degrees(math.atan2(dy, dx))
        n = max(1, int(math.ceil(L / self.MAX_SEG)))
        out = None
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            px, py = ax + dx * t0, ay + dy * t0
            qx, qy = ax + dx * t1, ay + dy * t1
            # GD rotation is clockwise-positive; pieces overlap slightly
            out = self.rect((px + qx) / 2, (py + qy) / 2, L / n + extend + (1.0 if n > 1 else 0.0),
                            thick, ch, z, zo, rot=-ang, groups=groups, layer=layer,
                            high_detail=high_detail)
        return out

    def polyline(self, pts, thick, ch, z, zo=0, groups=(), layer="rim", closed=False,
                 high_detail=False):
        n = len(pts)
        rng = range(n if closed else n - 1)
        out = []
        for i in rng:
            out.append(self.seg(pts[i], pts[(i + 1) % n], thick, ch, z, zo, groups,
                                layer, extend=thick * 0.9, high_detail=high_detail))
        return out

    def glow(self, cx, cy, diam, ch, z, zo=0, groups=(), layer="glow", kind="L",
             high_detail=False):
        o = Obj(GLOW_ID[kind], cx, cy)
        o.set(COLOR1, ch)
        s = round(diam / GLOW_DIAM[kind], 4)
        o.set(SCALE_X, s)
        o.set(SCALE_Y, s)
        return self._deco(o, z, zo, groups, layer, high_detail)

    def particles(self, x, y, pstring, z, zo=0, groups=(), quick=True,
                  high_detail=True):
        o = Obj(2065, x, y)
        o.set(PARTICLE_DATA, pstring)
        if quick:
            o.set(QUICK_START, 1)
        return self._deco(o, z, zo, groups, "particle", high_detail)

    # ------------------------------------------------- gradient triangles
    def _corner(self, p, groups):
        key = (round(p[0], 2), round(p[1], 2), tuple(sorted(groups)))
        if key in self.corner_cache:
            return self.corner_cache[key]
        g = self.group()
        o = Obj(3802, p[0], p[1])
        o.set(HIDE, 1)
        o.set(EDITOR_L1, EL["corner"])
        o.add_groups(g, *groups)
        self.add(o)
        self.corner_cache[key] = g
        return g

    def _trigger_xy(self, x):
        y = self.trig_y.get(x, 1500.0)
        self.trig_y[x] = y + 10.0
        return x, y

    def gtri(self, a, b, c, ch, layer, groups=(), x_trig=4.0, blend=0):
        # skip degenerate triangles
        area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if abs(area) < 1.0:
            return None
        ga = self._corner(a, groups)
        gb = self._corner(b, groups)
        gc = self._corner(c, groups)
        tx, ty = self._trigger_xy(x_trig)
        o = Obj(2903, tx, ty)
        o.set(COLOR1, ch)
        o.set(COLOR2, ch)
        o.set(GRAD_LAYER, GL[layer])
        o.set(GRAD_VERTEX, 1)
        o.set(GRAD_BL, ga)
        o.set(GRAD_BR, gb)
        o.set(GRAD_TL, gc)
        o.set(GRAD_TR, gc)
        if blend:
            o.set(GRAD_BLEND, blend)
        o.set(GRAD_PREVIEW_OPACITY, 1)
        # every gradient needs its own ID: triggers sharing an ID edit the same
        # gradient effect (GD Creator School, gradient trigger guide)
        self.grad_count += 1
        o.set(GRAD_ID, self.grad_count)
        o.set(EDITOR_L1, EL["trigger"])
        return self.add(o)

    def gpoly(self, pts, ch, layer, groups=(), x_trig=4.0):
        tris = triangulate(pts)
        for a, b, c in tris:
            self.gtri(a, b, c, ch, layer, groups, x_trig)
        return tris

    # ------------------------------------------------------------ triggers
    def _trig(self, oid, x, y=None):
        if y is None:
            x, y = self._trigger_xy(x)
        o = Obj(oid, x, y)
        o.set(EDITOR_L1, EL["trigger"])
        return self.add(o)

    def color_trigger(self, x, ch, rgb, dur=0.0, opacity=1.0, blending=False, y=None):
        o = self._trig(899, x, y)
        o.set(TARGET_COLOR, ch)
        o.set(RED, int(rgb[0])); o.set(GREEN, int(rgb[1])); o.set(BLUE, int(rgb[2]))
        o.set(DURATION, dur)
        o.set(OPACITY, opacity)
        if blending:
            o.set(BLENDING, 1)
        return o

    def pulse(self, x, target, rgb, fade_in, hold, fade_out, group=False, y=None,
              spawn=False, exclusive=False):
        o = self._trig(1006, x, y)
        o.set(TARGET, target)
        if group:
            o.set(PULSE_TARGET_TYPE, 1)
        o.set(RED, int(rgb[0])); o.set(GREEN, int(rgb[1])); o.set(BLUE, int(rgb[2]))
        o.set(FADE_IN, fade_in); o.set(HOLD, hold); o.set(FADE_OUT, fade_out)
        if exclusive:
            o.set(EXCLUSIVE, 1)
        if spawn:
            o.set(SPAWN_TRIG, 1); o.set(MULTI_TRIG, 1)
        return o

    def spawn(self, x, target, delay=0.0, y=None, spawn=False):
        o = self._trig(1268, x, y)
        o.set(TARGET, target)
        if delay:
            o.set(SPAWN_DELAY, round(delay, 4))
        if spawn:
            o.set(SPAWN_TRIG, 1); o.set(MULTI_TRIG, 1)
        return o

    def lock_camera(self, x, target, mod_x, mod_y):
        o = self._trig(901, x)
        o.set(TARGET, target)
        o.set(MOVE_X, 0); o.set(MOVE_Y, 0)
        o.set(DURATION, -1)
        o.set(LOCK_CAM_X, 1); o.set(LOCK_CAM_Y, 1)
        o.set(MOD_X, mod_x); o.set(MOD_Y, mod_y)
        return o

    def follow(self, x, target, follow_group, dur):
        o = self._trig(1347, x)
        o.set(TARGET, target)
        o.set(SECOND_TARGET, follow_group)
        o.set(DURATION, dur)
        o.set(FOLLOW_XMOD, 1); o.set(FOLLOW_YMOD, 1)
        return o

    def options(self, x, flags):
        o = self._trig(2899, x)
        for k, v in flags.items():
            o.set(int(k), v)
        return o


# ------------------------------------------------------------------ geometry
def _area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2


def _in_tri(p, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def triangulate(pts):
    """Ear clipping for a simple polygon (any winding). Returns triangles."""
    pts = [tuple(p) for p in pts]
    # drop consecutive duplicates
    clean = []
    for p in pts:
        if not clean or (abs(p[0] - clean[-1][0]) > 1e-6 or abs(p[1] - clean[-1][1]) > 1e-6):
            clean.append(p)
    if len(clean) > 1 and clean[0] == clean[-1]:
        clean.pop()
    pts = clean
    if _area(pts) < 0:
        pts = pts[::-1]
    idx = list(range(len(pts)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        ear_found = False
        for i in range(n):
            ia, ib, ic = idx[(i - 1) % n], idx[i], idx[(i + 1) % n]
            a, b, c = pts[ia], pts[ib], pts[ic]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-9:
                continue
            if any(_in_tri(pts[j], a, b, c) for j in idx if j not in (ia, ib, ic)):
                continue
            tris.append((a, b, c))
            idx.pop(i)
            ear_found = True
            break
        if not ear_found:
            # numerical trouble: drop a collinear/reflex vertex
            idx.pop(0)
    if len(idx) == 3:
        tris.append(tuple(pts[i] for i in idx))
    return tris


def jitter_line(a, b, step, amp, rng, keep_ends=True):
    """Points from a to b with perpendicular jitter (for jagged rock edges)."""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay)
    n = max(1, int(L // step))
    nx, ny = -(by - ay) / L, (bx - ax) / L
    out = []
    for i in range(n + 1):
        t = i / n
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        if not (keep_ends and (i == 0 or i == n)):
            d = rng.uniform(-amp, amp)
            x, y = x + nx * d, y + ny * d
        out.append((x, y))
    return out
