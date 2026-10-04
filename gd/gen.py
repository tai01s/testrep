import math, random, collections, sys
from phys import Player, step, variants, SPEED, DT, clearance

B = 30.0
SPIKE_W, SPIKE_LO, SPIKE_HI = 4.5, 7.0, 21.0   # conservative spike hitbox (bigger than GD's)
PORTAL_ID = {'cube': 12, 'ship': 13, 'ball': 47, 'ufo': 111, 'wave': 660}
SPEED_ID = {0.5: 200, 1: 201, 2: 202, 3: 203, 4: 1334}
FRAME = 1 / 60.0


class World:
    def __init__(self):
        self.cells = {}            # (col,row) -> True  solid block
        self.haz = collections.defaultdict(list)   # col -> boxes
        self.spikes = []           # (x,y,rot,channel)
        self.portals = []          # dict(x,y,kind,val)
        self.deco = []             # raw extra objects (dicts)
        self.floor_y = 0.0
        self.ceil_y = None

    # ---- geometry
    def block(self, c, r):
        self.cells[(c, r)] = True

    def fill_col(self, c, r0, r1):
        for r in range(r0, r1):
            self.block(c, r)

    def solids(self, x0, x1):
        out = []
        for c in range(int(math.floor(x0 / B)), int(math.floor(x1 / B)) + 1):
            for r in self.colrows(c):
                out.append((c * B, r * B, c * B + B, r * B + B))
        return out

    def colrows(self, c):
        return self._colidx.get(c, ()) if hasattr(self, '_colidx') else [r for (cc, r) in self.cells if cc == c]

    def index(self):
        d = collections.defaultdict(list)
        for (c, r) in self.cells:
            d[c].append(r)
        self._colidx = d

    def clear_cols(self, c0, c1):
        for k in [k for k in self.cells if c0 <= k[0] <= c1]:
            del self.cells[k]
        for c in range(c0, c1 + 1):
            self.haz.pop(c, None)
        self.spikes = [s for s in self.spikes if not (c0 <= int(s[0] // B) <= c1)]

    def spike(self, c, r, down=False):
        x = c * B + 15; y = r * B + 15
        if down:
            box = (x - SPIKE_W, y + 15 - SPIKE_HI, x + SPIKE_W, y + 15 - SPIKE_LO)
        else:
            box = (x - SPIKE_W, y - 15 + SPIKE_LO, x + SPIKE_W, y - 15 + SPIKE_HI)
        self.spikes.append((x, y, 180 if down else 0))
        self.haz[c].append(box)

    def hazards(self, x0, x1):
        out = []
        for c in range(int(math.floor(x0 / B)) - 1, int(math.floor(x1 / B)) + 2):
            out.extend(self.haz.get(c, ()))
        return out

    def portal(self, x, y, kind, val=None):
        self.portals.append(dict(x=x, y=y, kind=kind, val=val))


class Run:
    """one simulated attempt through (part of) the level"""
    def __init__(self, W, ctrl, vi, jit, x0=None, state=None):
        self.W, self.ctrl, self.vi, self.jit = W, ctrl, vi, jit

    pass


def prm_for(mode, vi):
    v = variants(mode)
    if mode in ('cube', 'wave'):
        return v[min(vi // 3, len(v) - 1)]
    return v[vi % len(v)]


class Controller:
    """the 'bot': open-loop presses for cube/ball, toggles for wave, closed loop for ship/ufo"""
    def __init__(self):
        self.presses = []     # (x, hold_len_units)
        self.waveholds = []   # (x_on, x_off)
        self.tracks = []      # (x0, x1, fn yc(x), kind)

    def hold(self, p, jit, t_since_press):
        x = p.x
        for i, (xp, hl) in enumerate(self.presses):
            s = jit(i, p) if jit else 0.0
            if xp + s <= x < xp + s + hl:
                return True
        for i, (a, b) in enumerate(self.waveholds):
            s = jit(1000 + i, p) if jit else 0.0
            if a + s <= x < b + s:
                return True
        for (a, b, fn, kind) in self.tracks:
            if a <= x < b:
                vx = p.vx()
                if kind == 'ship':
                    d = 6.0
                    ff = (fn(x + 0.12 * vx + d) - fn(x + 0.12 * vx - d)) / (2 * d) * vx
                    vd = ff + 7.0 * (fn(x + 0.04 * vx) - p.y)
                    return p.gdir * (vd - p.vy) > 0
                if kind == 'ufo':
                    err = fn(x + 0.10 * vx) - p.y
                    return p.gdir * p.vy < 0 and p.gdir * err > 22 and t_since_press > 0.07
        return False


def simulate(W, C, vi, jit=None, start=None, until=1e18, record=False, modes_at_start=None):
    if start is None:
        p = Player(0.0, 15.0, 'cube', 2)
    else:
        p = Player(**start)
    prm = prm_for(p.mode, vi)
    portals = sorted(W.portals, key=lambda d: d['x'])
    used = set()
    traj = []
    t_since = 9.0
    touched = []
    minclr = 1e9
    while p.x < until:
        # portals
        h = p.half
        for i, d in enumerate(portals):
            if i in used: continue
            if d['x'] > p.x + 80: break
            if abs(d['x'] - p.x) < 17 + h and abs(d['y'] - p.y) < 43 + h:
                used.add(i); touched.append(i)
                k = d['kind']
                if k in PORTAL_ID:
                    old = p.mode
                    p.mode = k; prm = prm_for(k, vi)
                    if k in ('ship', 'ufo', 'ball'):
                        p.vy *= 0.5
                    if k == 'cube' and old != 'cube':
                        p.vy *= 0.5
                elif k == 'speed':
                    p.speed = d['val']
                elif k == 'grav':
                    if p.gdir != d['val']:
                        p.gdir = d['val']; p.vy *= 0.5
                elif k == 'mini':
                    p.mini = d['val']
        hold = C.hold(p, jit, t_since)
        if hold and not p.prev_hold:
            t_since = 0.0
        t_since += DT
        W.ceil_y = 300.0 if p.mode in ('ship', 'ufo', 'wave') else None
        step(p, hold, prm, W)
        if record:
            traj.append((p.x, p.y, p.mode, p.ground, p.gdir))
        if p.dead:
            break
        c = clearance(p, W) if record else 1e9
        if c < minclr: minclr = c
    return p, traj, touched, minclr


# ---------------------------------------------------------------- builders

class Level:
    def __init__(self):
        self.W = World()
        self.C = Controller()
        self.sections = []   # (x0,x1,name,mode,speed)
        self.colors = []     # (x, palette)
        self.notes = []

    def warn(self, s):
        self.notes.append(s)
        print('WARN', s)


def jit_states(speed):
    d = 2 * FRAME * SPEED[speed]
    return [0.0, -d, d]


def cube_jump_trajs(W, x_press, y0, speed, gd=1, mini=False, extra_until=420):
    """trajectories for a press at x_press from ground state at y0 (all variants x jitter)"""
    trajs = []
    for vi in (0, 3):
        for s in jit_states(speed):
            C = Controller(); C.presses = [(x_press + s, 3 * FRAME * SPEED[speed])]
            st = dict(x=x_press - 45, y=y0, mode='cube', speed=speed, mini=mini, gdir=gd)
            p = Player(**st); p.ground = True
            prm = prm_for('cube', vi)
            tr = []
            jumped = False
            while p.x < x_press + extra_until:
                hold = C.hold(p, None, 9)
                step(p, hold, prm, W)
                tr.append((p.x, p.y, p.ground))
                if p.dead: tr.append(('dead', p.dead)); break
                if p.y > y0 + 1: jumped = True
                if jumped and p.ground and p.x > x_press + s + 60:
                    break
            trajs.append(tr)
    return trajs


def build_cube(L, x0, x1, speed, f_row, script, ceiling_row=None):
    W, C = L.W, L.C
    f = f_row          # floor row count (floor surface at f*30)
    xc = x0
    col = lambda x: int(math.floor(x / B))
    floor_until = col(x0)
    W.clear_cols(col(x0) + 1, col(x0) + 400)
    def lay_floor(to_x):
        nonlocal floor_until
        while floor_until <= col(to_x):
            if f > 0:
                W.fill_col(floor_until, 0, f)
            floor_until += 1
    for ev in script:
        kind = ev[0]
        if kind == 'W':
            xc += ev[1] * B
            continue
        if kind == 'D':        # floor drops by ev[1] rows at the next column boundary
            xd = (col(xc) + ev[2]) * B
            lay_floor(xd - 1)
            f = max(0, f - ev[1])
            xc = xd
            # simulate the fall to find landing
            W.index()
            land = 0
            for vi in (0, 3):
                p = Player(x=xc - 40, y=(f + ev[1]) * B + 15, mode='cube', speed=speed)
                p.ground = True
                lay_floor(xc + 400); W.index()
                while p.x < xc + 400:
                    step(p, False, prm_for('cube', vi), W)
                    if p.dead: L.warn(f'drop death {p.dead}'); break
                    if p.ground and p.y < (f + ev[1]) * B: land = max(land, p.x); break
            xc = land + 2 * FRAME * SPEED[speed]
            continue
        lead = ev[2] if len(ev) > 2 else 1.0
        xp = xc + lead * B
        lay_floor(xp + 450); W.index()
        y0 = f * B + 15
        trajs = cube_jump_trajs(W, xp, y0, speed)
        for tr in trajs:
            if tr and tr[-1][0] == 'dead':
                L.warn(f'cube pre-death at {xp}: {tr[-1][1]}')
        good = [tr for tr in trajs if tr and tr[-1][0] != 'dead']
        m = 3.0
        if kind == 'J':
            k = ev[1]
            safe = []
            lmin = min(tr[-1][0] for tr in good) if good else xp
            for c in range(col(xp), col(xp) + 12):
                xs = c * B + 15
                ok = xs + 15 + SPIKE_W + m < lmin
                for tr in good:
                    for (x, y, g) in tr:
                        if abs(x - xs) < 15 + SPIKE_W + m and (y - 15) < f * B + SPIKE_HI + m:
                            ok = False; break
                    if not ok: break
                safe.append(ok)
            runs = []; i = 0
            while i < len(safe):
                if safe[i]:
                    j = i
                    while j < len(safe) and safe[j]: j += 1
                    runs.append((i, j)); i = j
                else: i += 1
            if not runs:
                L.warn(f'no spike spot for jump at {xp}')
            else:
                a, b = max(runs, key=lambda r: r[1] - r[0])
                n = min(k, b - a)
                if n < k: L.warn(f'jump at {xp:.0f}: wanted {k} spikes, fit {n}')
                st = a + (b - a - n) // 2
                for c in range(col(xp) + st, col(xp) + st + n):
                    W.spike(c, f)
            land = max(tr[-1][0] for tr in good)
            xc = land
            C.presses.append((xp, 3 * FRAME * SPEED[speed]))
        elif kind == 'U':
            up = ev[1]
            # find valid platform edges
            valid = []
            for c in range(col(xp) + 1, col(xp) + 12):
                xb = c * B
                ok = True
                for tr in good:
                    hit = None
                    for (x, y, g) in tr:
                        if x + 15 >= xb - m:
                            hit = (x, y); break
                    if hit is None or hit[1] - 15 < (f + up) * B + m:
                        ok = False; break
                    # must still be above (not yet landed) i.e. y descending later below new top
                valid.append((c, ok))
            cs = [c for c, ok in valid if ok]
            if not cs:
                L.warn(f'no step-up spot at {xp}'); continue
            cb = cs[len(cs) // 2] if len(cs) < 3 else cs[1]
            lay_floor(cb * B - 1)
            f += up
            floor_until = cb
            lay_floor(xp + 450); W.index()
            # landing after step
            trajs = cube_jump_trajs(W, xp, y0, speed)
            land = 0
            for tr in trajs:
                if tr and tr[-1][0] == 'dead': L.warn(f'step-up death at {xp}: {tr[-1][1]}'); continue
                land = max(land, tr[-1][0])
            # spikes on the lower floor in front of the step where safe
            if len(ev) > 3 and ev[3]:
                for c in range(cb - ev[3], cb):
                    xs = c * B + 15
                    if all(not (abs(x - xs) < 15 + SPIKE_W + m and (y - 15) < (f - up) * B + SPIKE_HI + m) for tr in trajs if tr[-1][0] != 'dead' for (x, y, g) in tr):
                        if not W.cells.get((c, f - up)):
                            W.spike(c, f - up)
            xc = land
            C.presses.append((xp, 3 * FRAME * SPEED[speed]))
    x1 = max(x1 or 0, xc + 4 * B)
    lay_floor(x1); W.index()
    L.sections.append((x0, x1, 'cube', speed))
    return f, x1


def path_corridor(L, x0, x1, yc, half, clr, mode, spikes=True, top=300.0, bottom=0.0, minopen=0):
    W = L.W
    c0 = int(math.floor(x0 / B)); c1 = int(math.floor(x1 / B))
    pad = half + clr
    W.clear_cols(c0, c1)
    prof = []
    for c in range(c0, c1 + 1):
        xs = [c * B - pad + i * (B + 2 * pad) / 12 for i in range(13)]
        ys = [yc(min(max(x, x0), x1)) for x in xs]
        lo, hi = min(ys) - half - clr, max(ys) + half + clr
        fr = max(0, int(math.floor((lo - bottom) / B)))
        cr = min(int(round((top - bottom) / B)), int(math.ceil((hi - bottom) / B)))
        prof.append((c, fr, cr, min(ys), max(ys)))
    for (c, fr, cr, ymin, ymax) in prof:
        rb = int(round(bottom / B))
        W.fill_col(c, rb, rb + fr)
        W.fill_col(c, rb + cr, int(round(top / B)))
    if spikes:
        for i, (c, fr, cr, ymin, ymax) in enumerate(prof):
            # widen check by neighbours (horizontal clearance of a spike box)
            nb = prof[max(0, i - 1):i + 2]
            lo = min(p[3] for p in nb) - half
            hi = max(p[4] for p in nb) + half
            rb = int(round(bottom / B))
            if fr > 0 or bottom > 0:
                if (rb + fr) * B + SPIKE_HI + clr < lo and fr < cr - 1:
                    W.spike(c, rb + fr)
            if (rb + cr) * B - SPIKE_HI - clr > hi and cr - 1 > fr and cr * B + bottom < top:
                W.spike(c, rb + cr - 1, down=True)
    W.index()
    return prof


def smooth(points):
    """points: [(x,y)] -> cosine interpolated function"""
    pts = sorted(points)
    def f(x):
        if x <= pts[0][0]: return pts[0][1]
        if x >= pts[-1][0]: return pts[-1][1]
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            if xa <= x <= xb:
                t = (x - xa) / (xb - xa)
                t = (1 - math.cos(math.pi * t)) / 2
                return ya + (yb - ya) * t
    return f


def build_track(L, x0, x1, speed, pts_rel, kind, tol, clr=4.0, gravs=()):
    """ship / ufo: pts_rel [(blocks from x0, y)]"""
    pts = [(x0 + b * B, y) for b, y in pts_rel]
    yc = smooth(pts)
    half = 15 + tol
    path_corridor(L, x0, x1, yc, half, clr, kind)
    L.C.tracks.append((x0 - 60, x1, yc, kind))
    for (b, g) in gravs:
        x = x0 + b * B
        L.W.portal(x, yc(x), 'grav', g)
    L.sections.append((x0, x1, kind, speed))
    return yc


def build_wave(L, x0, speed, y0, segs, mini=False, clr=14.0, ylo=60.0, yhi=240.0, yend=None):
    """segs: list of (blocks, dir) dir=+1 up/-1 down/0 not allowed. returns x_end,y_end"""
    s = 2.0 if mini else 1.0
    pts = [(x0 - 60, y0), (x0, y0)]
    x, y = x0, y0
    holds = []
    # pre-segment: player arrives in wave mode moving down (not holding) -> start with flat? we
    # start with first seg immediately at x0
    for blocks, d in segs:
        dx = blocks * B
        if y + d * s * dx > yhi or y + d * s * dx < ylo:
            d = -d
        if y + d * s * dx > yhi or y + d * s * dx < ylo:
            L.warn(f'wave seg out of range at {x}')
        nx, ny = x + dx, y + d * s * dx
        if d > 0: holds.append((x, nx))
        pts.append((nx, ny)); x, y = nx, ny
    if yend is not None and abs(y - yend) > 1:
        d = 1 if yend > y else -1
        dx = abs(yend - y) / s
        nx, ny = x + dx, yend
        if d > 0: holds.append((x, nx))
        pts.append((nx, ny)); x, y = nx, ny
    pts.append((x + 45, y + (s * 45 if (yend is not None and False) else -s * 45)))
    def yc(q):
        if q <= x0: return y0
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            if xa <= q <= xb:
                return ya + (yb - ya) * (q - xa) / (xb - xa) if xb > xa else yb
        return pts[-1][1]
    for (a, b) in holds:
        L.C.waveholds.append((a, b))
    half = 5.0 if mini else 7.0
    path_corridor(L, x0, x, yc, half, clr, 'wave')
    L.sections.append((x0, x, 'wave', speed))
    return x, y, yc


def build_ball(L, x0, speed, gaps, f_row=1, c_row=7):
    """gaps: list of blocks between presses (first measured from x0)."""
    W, C = L.W, L.C
    hl = 3 * FRAME * SPEED[speed]
    xs = []
    x = x0
    for g in gaps:
        x += g * B
        xs.append(x)
    xend = x + 6 * B
    W.clear_cols(int(x0 // B), int(xend // B) + 30)
    for c in range(int(x0 // B) - 1, int(xend // B) + 1):
        W.fill_col(c, 0, f_row); W.fill_col(c, c_row, 10)
    W.index()
    yF, yC = f_row * B, c_row * B
    # make sure every press happens grounded in every variant/jitter; push presses later if not
    for i in range(len(xs)):
        for attempt in range(40):
            okall = True
            for vi in range(6):
                C2 = Controller(); C2.presses = [(q, hl) for q in xs[:i]]
                p = Player(x=x0 - 60, y=yF + 15, mode='ball', speed=speed); p.ground = True
                prm = prm_for('ball', vi)
                tgt = xs[i] - 2 * FRAME * SPEED[speed]
                for jit in (0, 1, 2):
                    jj = jit_states(speed)[jit]
                    C2.presses = [(q + jj, hl) for q in xs[:i]]
                    p = Player(x=x0 - 60, y=yF + 15, mode='ball', speed=speed); p.ground = True
                    while p.x < tgt:
                        step(p, C2.hold(p, None, 9), prm, W)
                        if p.dead: break
                    if not p.ground or p.dead:
                        okall = False; break
                if not okall: break
            if okall: break
            for j in range(i, len(xs)): xs[j] += 15
        else:
            L.warn(f'ball press {i} never grounded')
    for q in xs:
        C.presses.append((q, hl))
    xend = xs[-1] + 6 * B
    for c in range(int(x0 // B) - 1, int(xend // B) + 1):
        W.fill_col(c, 0, f_row); W.fill_col(c, c_row, 10)
    W.index()
    # trajectories
    trajs = []
    for vi in range(6):
        for jj in jit_states(speed):
            C2 = Controller(); C2.presses = [(q + jj, hl) for q in xs]
            p = Player(x=x0 - 60, y=yF + 15, mode='ball', speed=speed); p.ground = True
            prm = prm_for('ball', vi); tr = []
            while p.x < xend:
                step(p, C2.hold(p, None, 9), prm, W); tr.append((p.x, p.y))
                if p.dead: L.warn(f'ball dead {p.dead}'); break
            trajs.append(tr)
    m = 4.0
    for c in range(int(x0 // B) + 2, int(xend // B) - 1):
        xs_ = c * B + 15
        near = [(x, y) for tr in trajs for (x, y) in tr if abs(x - xs_) < 15 + SPIKE_W + m]
        if near and all(y - 15 > yF + SPIKE_HI + m for x, y in near):
            W.spike(c, f_row)
        if near and all(y + 15 < yC - SPIKE_HI - m for x, y in near):
            W.spike(c, c_row - 1, down=True)
    W.index()
    L.sections.append((x0, xend, 'ball', speed))
    if len(xs) % 2:
        L.warn('ball ends on ceiling')
    return xend
