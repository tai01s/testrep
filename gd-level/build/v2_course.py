"""Test v2 gameplay, built path-first: the clicks sit on notes of the song, the path is simulated with gdphys, the
corridor and hazards are placed around that path, and every click's timing window is measured.

Parts (cut-song bars; bar c starts at c * 1.875 s):
  A  bars 0-2  ball, 1x      gatehouse: floor and ceiling ledges with iron spikes in the gaps
  B  bars 3-4  UFO, 1x       stairwell: floating masonry with spikes, eighth-note pulse, bass pickup
  C  bars 5-6  wave, 2x      ramparts: beat entry
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gdphys import Course, Player, Input, simulate, windows, ups, DT  # noqa: E402

BEAT = 60 / 128.0
E8 = BEAT / 2
BAR = 4 * BEAT
TAP = 0.05                       # how long a tap is held (s)


def T(bar, e=1):
    """Time of eighth note e (1-8) in cut bar `bar`."""
    return bar * BAR + (e - 1) * E8


class Build:
    """Gameplay objects with their role, kept so the deco pass can dress each one."""

    def __init__(self):
        self.course = Course()
        self.items = []          # dicts: kind, geometry, extra

    def solid(self, x0, y0, x1, y1, role='block'):
        self.course.solids.append((x0, y0, x1, y1))
        self.items.append(dict(kind='solid', box=(x0, y0, x1, y1), role=role))

    def spike(self, cx, base, down=False, role='spike'):
        """Standard spike (id 8) standing on `base` (or hanging from it if down). Hitbox 6x12 centred."""
        cy = base - 15 if down else base + 15
        self.course.hazards.append((cx - 3, cy - 6, cx + 3, cy + 6))
        self.items.append(dict(kind='spike', x=cx, y=cy, down=down, role=role))

    def spike_row(self, x0, x1, base, down=False):
        n = int(round((x1 - x0) / 30.0))
        for i in range(n):
            self.spike(x0 + 15 + 30 * i, base, down)

    def orb(self, x, y, kind):
        self.course.orbs.append((x, y, kind))
        self.items.append(dict(kind='orb', x=x, y=y, orb=kind))

    def portal(self, x, y, what, value, h=90.0, w=34.0):
        self.course.portals.append((x - w / 2, y - h / 2, x + w / 2, y + h / 2, what, value))
        self.items.append(dict(kind='portal', x=x, y=y, what=what, value=value))


# ---------------------------------------------------------------- part A: ball

A_FLOOR, A_CEIL = 30.0, 150.0                      # ledge top / ledge underside (inner height 120)
A_CLICKS = [T(1, 1), T(1, 3), T(1, 5), T(1, 6), T(1, 7),
            T(2, 1), T(2, 3), T(2, 4), T(2, 5), T(2, 7)]          # even count: ends on the floor
A_END = T(3, 1)


def ball_contacts(clicks, t_end, floor=A_FLOOR, ceil=A_CEIL):
    """Simulate the intended clicks in an open corridor; return surface contact spans [(surface, x0, x1)]."""
    c = Course(solids=[(-1e5, 0, 1e5, floor), (-1e5, ceil, 1e5, 240)], floor=0.0, ceil=240.0)
    r = simulate(c, Input([(t, t + TAP) for t in clicks]), Player(mode='ball', y=floor + 15), t_end=t_end)
    assert r['alive'], r['death']
    spans, cur = [], None
    for t, x, y, mode, up in r['path']:
        surf = 'floor' if abs(y - (floor + 15)) < 0.01 else ('ceil' if abs(y - (ceil - 15)) < 0.01 else None)
        if surf != (cur[0] if cur else None):
            if cur:
                spans.append(tuple(cur))
            cur = [surf, x, x] if surf else None
        elif cur:
            cur[2] = x
    if cur:
        spans.append(tuple(cur))
    return spans, r


def build_ball(b, clicks=A_CLICKS, t_end=A_END, win_ms=None, x_end=None):
    """Ledges are sized from the intended path so each click gets its target window: a ledge runs from where the
    ball lands (minus the early slack of the click that sent it there) to where it leaves (plus the late slack of
    the click that takes it off). Gaps between ledges hold spikes."""
    win_ms = win_ms or [50.0] * len(clicks)
    spans, r = ball_contacts(clicks, t_end)
    v = ups('1x') / 1000.0
    x_end = x_end or ups('1x') * t_end
    ledges = {'floor': [], 'ceil': []}
    for k, (surf, xl, xt) in enumerate(spans):
        land_click = k - 1                 # span k (k>=1) was reached by click k-1
        take_click = k if k < len(clicks) else None
        a = -300.0 if k == 0 else xl + 15 - win_ms[land_click] * v
        c = x_end if take_click is None else xt - 15 + win_ms[take_click] * v
        ledges[surf].append((a, c))
    for surf, segs in ledges.items():
        prev = -300.0
        for a, c in segs + [(x_end, x_end)]:
            if a - prev > 1:
                if surf == 'floor':
                    n = max(1, int(round((a - prev) / 30.0)))
                    w = (a - prev) / n
                    for i in range(n):
                        b.spike(prev + w * (i + 0.5), 0.0)
                else:
                    b.solid(prev, A_CEIL + 30, a, 240, role='ceiling recess')
                    n = max(1, int(round((a - prev) / 30.0)))
                    w = (a - prev) / n
                    for i in range(n):
                        b.spike(prev + w * (i + 0.5), A_CEIL + 30, down=True)
            if c > a:
                if surf == 'floor':
                    b.solid(a, 0, c, A_FLOOR, role='ledge')
                else:
                    b.solid(a, A_CEIL, c, 240, role='ceiling ledge')
            prev = max(prev, c)
    return spans, r


# ---------------------------------------------------------------- part B: UFO

B_CLICKS = [T(3, 1), T(3, 2), T(3, 3), T(3, 5), T(3, 7),          # found by search: the only 8th pattern
            T(4, 1), T(4, 3), T(4, 5), T(4, 6), T(4, 7), T(4, 8)]  # with the accents that stays in y 58..219
B_PORTAL_T = T(2, 7) + 0.30                    # after the last ball landing, before the first UFO click
C_PORTAL_T = T(4, 8) + 0.16                    # wave + 2x, before the beat entry at T(5, 1)


def extrema(path, t0, t1):
    """Local maxima / minima of y on the recorded path between t0 and t1: [(kind, t, x, y)]."""
    pts = [q for q in path if t0 <= q[0] <= t1]
    out = []
    for i in range(1, len(pts) - 1):
        a, b_, c = pts[i - 1][2], pts[i][2], pts[i + 1][2]
        if b_ > a and b_ >= c:
            out.append(('max', pts[i][0], pts[i][1], b_))
        elif b_ < a and b_ <= c:
            out.append(('min', pts[i][0], pts[i][1], b_))
    return out


def at(path, t):
    """(x, y) on the recorded path at time t (nearest sample)."""
    q = min(path, key=lambda q: abs(q[0] - t))
    return q[1], q[2]


def build_ufo(b, path, clicks, t_stop, clear, width=30.0, top=None, floor=0.0):
    """A gate under every click (the dip) and over every apex between clicks. Each gate clears the intended path
    across its whole width by `clear` units (UFO box to spike hitbox). Pillars run to the band floor/ceiling."""
    top = top if top is not None else 300.0
    gates = []
    marks = []
    for k, t in enumerate(clicks):
        x, y = at(path, t)
        marks.append(('min', t, x, y))
        t2 = clicks[k + 1] if k + 1 < len(clicks) else t_stop
        seg = [q for q in path if t < q[0] < t2]
        if seg:
            q = max(seg, key=lambda q: q[2])
            if q[2] > y + 4:
                marks.append(('max', q[0], q[1], q[2]))
    for k, (kind, t, x, y) in enumerate(marks):
        c = clear[k] if k < len(clear) else clear[-1]
        x0, x1 = x - width / 2, x + width / 2
        span = [q[2] for q in path if x0 - 15 <= q[1] <= x1 + 15]
        if kind == 'max':
            base = max(span) + 15 + c + 21
            b.solid(x0, base, x1, top + 150, role='hanging pillar')
            for i in range(int(width // 30)):
                b.spike(x0 + 15 + 30 * i, base, down=True)
        else:
            base = min(span) - 15 - c - 21
            if base > floor:
                b.solid(x0, floor - 150, x1, base, role='standing pillar')
            for i in range(int(width // 30)):
                b.spike(x0 + 15 + 30 * i, max(base, floor))
        gates.append((kind, t, x, y))
    return gates


# ---------------------------------------------------------------- part C: wave, 2x

S16 = BEAT / 4
C_N16 = 24                                     # wave runs T(5,1) .. T(6,5)


def wave_rhythm(y0, lo, hi, v=None, n=C_N16, max16=6):
    """Pick the wave's hold/release pattern on the 16th grid from T(5,1): every segment must keep the path in
    [lo, hi]; turns score by beat strength (beat 3, eighth 2, sixteenth 0.6), changing segment lengths score a
    little (variety), lone sixteenths cost a little. Returns (hold intervals, segments)."""
    import functools
    v = v or ups('2x') * S16

    def w(k):
        return 3.0 if k % 4 == 0 else (2.0 if k % 2 == 0 else 0.6)

    @functools.lru_cache(None)
    def best(k, y, up, n16, last):
        if k >= n:
            return (0.0, ())
        out = (-1e9, ())
        for L in (1, 2, 3, 4):
            e = min(n, k + L)
            y2 = y + (v if up else -v) * (e - k)
            if not (lo <= y2 <= hi):
                continue
            k16 = n16 + (1 if L % 2 else 0)
            if k16 > max16:
                continue
            sub = best(e, round(y2, 3), not up, k16, L)
            sc = sub[0] + (w(e) if e < n else 0) + (0.9 if L != last else 0) - (0.4 if L == 1 else 0)
            if sc > out[0]:
                out = (sc, ((k, e, up),) + sub[1])
        return out
    cands = [best(0, round(y0, 3), up, 0, 0) for up in (True, False)]
    sc, segs = max(cands, key=lambda c: c[0])
    assert sc > -1e8, 'no wave pattern fits'
    holds = [(T(5, 1) + a * S16, T(5, 1) + (e if e < n else n + 1) * S16) for a, e, up in segs if up]
    return holds, segs


def fly_band(y_portal, mode='wave'):
    """GD-like fly bounds for a mode portal at y_portal: 300 tall (240 for ball) centred on the portal snapped to
    the 30 grid, floor clamped to the ground."""
    hgt = 240.0 if mode in ('ball', 'spider') else 300.0
    c = round(y_portal / 30.0) * 30.0
    lo = max(0.0, c - hgt / 2)
    return lo, lo + hgt
C_END_T = T(5, 1) + C_N16 * S16 + 0.05


def build_wave(b, path, toggles, clear, band=(0.0, 300.0)):
    """A gate at every turn (every hold edge): hazards above and below the turn point, `clear` units from the wave
    box (half-size 5), each clearing the intended path across the gate's width."""
    turns = []
    for k, t in enumerate(toggles):
        x, y = at(path, t)
        c = clear[k] if k < len(clear) else clear[-1]
        span = [q[2] for q in path if x - 20 <= q[1] <= x + 20]
        hi = max(span) + 5 + c
        lo = min(span) - 5 - c
        b.solid(x - 15, hi + 21, x + 15, band[1] + 150, role='wave ceiling tooth')
        b.spike(x, hi + 21, down=True, role='wave spike')
        if lo - 21 > band[0]:
            b.solid(x - 15, band[0] - 150, x + 15, lo - 21, role='wave floor tooth')
        b.spike(x, max(lo - 21, band[0]), role='wave spike')
        turns.append((t, x, y))
    return turns


def check(b, presses, t_end, start=None, label=''):
    start = start or (lambda: Player(mode='ball', y=A_FLOOR + 15))
    r = simulate(b.course, Input(presses), start(), t_end=t_end, fly_bounds=fly_band)
    print('%s intended run: %s %s' % (label, 'ALIVE' if r['alive'] else 'DIED', r['death'] or ''),
          'at t=%.3f x=%.1f y=%.1f' % (r['t'], r['x'], r['y']) if not r['alive'] else '')
    w = windows(b.course, presses, start, t_end, fly_bounds=fly_band)
    for i, e, l in w:
        print('  input %2d at %6.3fs (%s): -%3.0f / +%3.0f ms' % (i + 1, presses[i][0], bar_label(presses[i][0]), e, l))
    return r, w


def bar_label(t):
    k = t / E8
    bar = int(k // 8)
    e = k - bar * 8
    return '%d.%g' % (bar, round(e + 1, 2))


def check(b, presses, t_end, start=None, label=''):
    start = start or (lambda: Player(mode='ball', y=A_FLOOR + 15))
    r = simulate(b.course, Input(presses), start(), t_end=t_end, fly_bounds=fly_band)
    print('%s intended run: %s %s' % (label, 'ALIVE' if r['alive'] else 'DIED', r['death'] or ''),
          'at t=%.3f x=%.1f y=%.1f' % (r['t'], r['x'], r['y']) if not r['alive'] else '')
    w = windows(b.course, presses, start, t_end, fly_bounds=fly_band)
    for i, e, l in w:
        print('  input %2d at %6.3fs: -%3.0f / +%3.0f ms' % (i + 1, presses[i][0], e, l))
    return r, w


def build_all(verbose=True):
    b = Build()
    b.course.floor, b.course.ceil = 0.0, 240.0
    xb = ups('1x') * B_PORTAL_T
    build_ball(b, win_ms=[55, 55, 50, 50, 50, 50, 45, 45, 45, 45], x_end=xb + 40)
    b.portal(xb, 60.0, 'mode', 'ufo')
    presses_a = [(t, t + TAP) for t in A_CLICKS]
    presses_b = [(t, t + TAP) for t in B_CLICKS]
    xc = xb + ups('1x') * (C_PORTAL_T - B_PORTAL_T)
    probe = simulate(b.course, Input(presses_a + presses_b), Player(mode='ball', y=A_FLOOR + 15), t_end=C_PORTAL_T,
                     fly_bounds=fly_band)
    assert probe['alive'], ('probe', probe['death'], probe['t'])
    gates = build_ufo(b, probe['path'], B_CLICKS, C_PORTAL_T - 0.05, clear=[13.0])
    # wave portal: centred on the UFO's height where it meets the portal
    y_at = [q[2] for q in probe['path'] if abs(q[1] - (xc - 30)) < 6][0]
    y_p = round(y_at)
    band = fly_band(y_p)
    b.portal(xc, y_p, 'mode', 'wave')
    b.portal(xc, y_p, 'speed', '2x', h=44.0)
    t_hit = (xc - 32) / ups('1x')                       # roughly when the wave starts
    y51 = y_at - ups('2x') * (T(5, 1) - t_hit)          # descending until the beat entry
    holds, segs = wave_rhythm(y51, band[0] + 55, band[1] - 55)
    probe2 = simulate(b.course, Input(presses_a + presses_b + holds), Player(mode='ball', y=A_FLOOR + 15),
                      t_end=C_END_T, fly_bounds=fly_band)
    assert probe2['alive'], ('probe2', probe2['death'], probe2['t'], probe2['x'], probe2['y'])
    toggles = sorted([a for a, z in holds] + [z for a, z in holds if z < C_END_T - 0.06])
    turns = build_wave(b, probe2['path'], toggles, clear=[27.0], band=band)
    presses = presses_a + presses_b + holds
    return b, presses, dict(ufo_gates=gates, wave_turns=turns, y_wave_portal=y_p, band=band, x_ufo=xb, x_wave=xc,
                            wave_segments=segs)


if __name__ == '__main__':
    b, presses, info = build_all()
    print('UFO portal x=%.0f, wave portal x=%.0f y=%d band %s' % (info['x_ufo'], info['x_wave'], info['y_wave_portal'],
                                                                   info['band']))
    print('UFO gates:', [(k, round(x), round(y)) for k, t, x, y in info['ufo_gates']])
    print('wave segments (16ths from 5.1):', [(a, e, 'U' if u else 'D') for a, e, u in info['wave_segments']])
    print('wave turns:', [(round(x), round(y)) for t, x, y in info['wave_turns']])
    check(b, presses, C_END_T, label='v2')
