"""Player physics for Geometry Dash 2.2, from decompiled game code, for checking that gameplay is possible and for
measuring timing windows. It does not replace GD: a bot run and a playtest are still the real test.

Sources (constants copied, not guessed):
  - PlayerObject::updateJump and PlayerObject::updateTimeMod, decompiled by camila314
    (https://github.com/camila314/gdp): per-speed jump velocity (m_yStart), gravity and x speed; cube/robot/
    ball/spider gravity factors; UFO click impulse and gravity; ship acceleration rules and velocity caps; wave
    velocity = x velocity.
  - PlayerObject::ringJump, PlayerObject::propellPlayer, GJBaseGameLayer::getBumpMod and gravBumpPlayer, from the
    IDA decompilation of the native game in https://github.com/Velipetroll/gd-web-decompiled-cpp: orb multipliers
    per orb type and mode, pad impulse 16 * mod, ball/spider/swing x0.6 on pads, ball x0.7 after orbs.
  - GJBaseGameLayer::update (camila314): physics runs at 240 steps/s, each step dt = 0.25 in 60 fps frame units,
    the player is updated and then collisions are checked.

Units: positions in GD units (1 block = 30), velocities in units per 60 fps frame. The player position is its
centre.

Collision is conservative where the game's exact rules aren't known:
  - hazards are hit with the full player box (optionally grown by `margin`);
  - solids kill if the small inner box (0.3 of the size) touches them, otherwise the player lands or bumps;
  - the wave dies on any solid contact (the game lets it slide on flat ground, so this is stricter);
  - orbs activate on a fresh press while the boxes overlap; orb box `ORB_HALF` is 18 (36x36).
"""
from dataclasses import dataclass, field

STEP = 0.25                      # frame units per 240 Hz step
DT = STEP / 60.0                 # seconds per step

# speed name -> (m_playerSpeed, m_speedMultiplier, m_yStart, m_gravity)   [updateTimeMod]
SPEED = {
    '0.5x': (0.7, 5.980002, 10.620032, 0.940199),
    '1x': (0.9, 5.77000189, 11.1800318, 0.958199024),
    '2x': (1.1, 5.870002, 11.420032, 0.957199),
    '3x': (1.3, 6.000002, 11.230032, 0.961199),
    '4x': (1.6, 6.000002, 11.230032, 0.961199),
}
FLY_G = 0.9582                   # used instead of m_gravity for ball, ship, ufo, wave, spider


def xvel(speed):
    p, m, _, _ = SPEED[speed]
    return p * m                 # units per frame


def ups(speed):
    return xvel(speed) * 60.0    # units per second

# ringJump multipliers on m_yStart. Keys: orb kind -> mode -> mult (missing mode = 1.0)
ORB_MULT = {
    'yellow': {'robot': 0.9},
    'pink': {'ship': 0.37, 'ufo': 0.42, 'ball': 0.77, 'cube': 0.72, 'robot': 0.72, 'spider': 0.72},
    'red': {'cube': 1.38, 'ball': 1.34, 'spider': 1.34, 'robot': 1.28, 'ufo': 1.02, 'ship': 1.0},
    'blue': {},                  # x0.8 then gravity flip (handled below)
    'green': {'ship': 0.7},      # gravity flip first, then jump
}
PAD_MOD = {'yellow': 1.0, 'pink': {'ship': 0.35, 'ufo': 0.4, 'ball': 0.7, 'spider': 0.7}, 'red': 1.25}
PAD_MOD_DEFAULT_PINK = 0.65
ORB_IDS = {36: 'yellow', 141: 'pink', 1333: 'red', 84: 'blue', 1022: 'green', 1330: 'black'}
PAD_IDS = {35: 'yellow', 140: 'pink', 1332: 'red', 67: 'blue'}
ORB_HALF = 18.0


@dataclass
class Course:
    solids: list = field(default_factory=list)     # (x0, y0, x1, y1)
    hazards: list = field(default_factory=list)    # (x0, y0, x1, y1)
    orbs: list = field(default_factory=list)       # (x, y, kind)
    pads: list = field(default_factory=list)       # (x0, y0, x1, y1, kind)
    portals: list = field(default_factory=list)    # (x0, y0, x1, y1, what, value)  what: mode/speed/grav/size
    floor: float = 0.0                              # GD ground / fly-mode bounds, set by mode portals
    ceil: float = 1e9


@dataclass
class Player:
    x: float = 0.0
    y: float = 15.0
    vy: float = 0.0
    mode: str = 'cube'
    speed: str = '1x'
    mini: bool = False
    upside: bool = False
    on_ground: bool = True
    accel: bool = False          # m_isAccelerating (after orbs/pads), lifts the fly velocity caps

    @property
    def size(self):
        if self.mode == 'wave':
            return 10.0 if not self.mini else 6.0
        return 30.0 * (0.6 if self.mini else 1.0)

    @property
    def flip(self):
        return -1 if self.upside else 1


class Input:
    """presses: list of (t_press, t_release). Ball/UFO/orbs use the press edge; cube/ship/wave use holding."""

    def __init__(self, presses):
        self.p = sorted(presses)

    def holding(self, t):
        return any(a <= t < b for a, b in self.p)

    def press_index(self, t):
        """Index of the press being held at t, or None."""
        for i, (a, b) in enumerate(self.p):
            if a <= t < b:
                return i
        return None


def _overlap(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0


def simulate(course, inp, p=None, t_end=10.0, t0=0.0, margin=0.0, entry_vy_mult=1.0, record=True,
             fly_bounds=None):
    """Run from t0 to t_end. Returns dict(alive, t, death, path=[(t, x, y, mode, upside)], events=[...]).
    fly_bounds(portal_y, mode) -> (floor, ceil) for mode portals; default GD-like: 300 tall (240 for ball),
    centred on the portal and clamped to the ground."""
    p = p or Player()
    used_presses = set()           # presses consumed by an orb / ball / ufo
    used_objs = set()              # orbs/pads/portals already activated
    floor, ceil = course.floor, course.ceil
    path, events = [], []
    t = t0
    n = 0
    while t < t_end:
        hold = inp.holding(t)
        pi = inp.press_index(t)
        fresh = pi is not None and pi not in used_presses
        # m_isAccelerating clears once the fly velocity is back inside the caps
        if p.mode in ('ship', 'ufo'):
            v16 = 1.0 if not p.mini else 0.85
            up_cap, dn_cap = 8.0 / v16, -6.4 / v16
            if dn_cap < p.vy * p.flip < up_cap:
                p.accel = False
        _update_jump(p, hold, fresh, lambda: used_presses.add(pi), events, t)
        vx = xvel(p.speed)
        px, py = p.x, p.y
        p.x += vx * STEP
        p.y += p.vy * STEP
        dead = _collide(course, p, py, floor, ceil, margin)
        if dead:
            return dict(alive=False, t=t, death=dead, x=p.x, y=p.y, path=path, events=events, player=p)
        # orbs (fresh press, overlap)
        h = p.size / 2
        for i, (ox, oy, kind) in enumerate(course.orbs):
            if ('o', i) in used_objs:
                continue
            if _overlap(p.x - h, p.y - h, p.x + h, p.y + h, ox - ORB_HALF, oy - ORB_HALF, ox + ORB_HALF, oy + ORB_HALF):
                if fresh and pi not in used_presses:
                    _ring_jump(p, kind)
                    used_presses.add(pi)
                    used_objs.add(('o', i))
                    events.append((t, 'orb', kind, i))
        for i, (x0, y0, x1, y1, kind) in enumerate(course.pads):
            if ('p', i) in used_objs:
                continue
            if _overlap(p.x - h, p.y - h, p.x + h, p.y + h, x0, y0, x1, y1):
                _bump(p, kind)
                used_objs.add(('p', i))
                events.append((t, 'pad', kind, i))
        for i, (x0, y0, x1, y1, what, val) in enumerate(course.portals):
            if ('q', i) in used_objs:
                continue
            if _overlap(p.x - h, p.y - h, p.x + h, p.y + h, x0, y0, x1, y1):
                used_objs.add(('q', i))
                events.append((t, what, val, i))
                if what == 'speed':
                    p.speed = val
                elif what == 'grav':
                    want = val == 'up'
                    if p.upside != want:
                        p.upside = want
                        p.vy *= 0.5
                elif what == 'size':
                    p.mini = val == 'mini'
                elif what == 'mode':
                    if p.mode != val:
                        p.mode = val
                        p.vy *= entry_vy_mult
                        p.on_ground = False
                        p.accel = False
                        if fly_bounds:
                            floor, ceil = fly_bounds((y0 + y1) / 2, val)
                        elif val in ('ship', 'ufo', 'wave', 'ball', 'spider', 'swing'):
                            hgt = 240.0 if val in ('ball', 'spider') else 300.0
                            c = round(((y0 + y1) / 2) / 30.0) * 30.0
                            floor = max(0.0, c - hgt / 2)
                            ceil = floor + hgt
                        else:
                            floor, ceil = 0.0, 1e9
        if record and n % 2 == 0:
            path.append((t, p.x, p.y, p.mode, p.upside))
        t += DT
        n += 1
    return dict(alive=True, t=t, death=None, x=p.x, y=p.y, path=path, events=events, player=p)


def _update_jump(p, hold, fresh, consume, events, t):
    _, _, y_start, g_speed = SPEED[p.speed]
    flip = p.flip
    if p.mode in ('cube', 'robot', 'ball', 'spider'):
        v16 = 0.8 if p.mini else 1.0
        float_b = 0.6 if p.mode in ('ball', 'spider') else (0.9 if p.mode == 'robot' else 1.0)
        g = FLY_G if p.mode in ('ball', 'spider') else g_speed
        if p.mode == 'ball':
            if p.on_ground and fresh:
                p.vy = flip * y_start * v16
                p.upside = not p.upside
                p.vy *= 0.6
                p.on_ground = False
                consume()
                events.append((t, 'flip', p.upside))
                return
        elif p.mode == 'cube' and p.on_ground and hold:
            p.vy = flip * y_start * v16
            p.on_ground = False
            events.append((t, 'jump', None))
            return
        p.vy -= flip * g * STEP * float_b
        if p.upside:
            p.vy = min(p.vy, 15.0)
        else:
            p.vy = max(p.vy, -15.0)
        return
    if p.mode == 'ufo':
        v16 = 1.0 if not p.mini else 0.85
        if fresh:
            imp = flip * (7.0 if not p.mini else 8.0) * v16
            if (imp < p.vy) if p.upside else (imp > p.vy):
                p.vy = imp
            consume()
            events.append((t, 'ufo', None))
        falling = p.vy * flip < 0
        v41 = 0.8 if falling else 1.2
        p.vy -= FLY_G * STEP * flip * v41 * 0.5 / v16
        if not p.accel:
            p.vy = _clamp_fly(p, v16, 0.8)
        return
    if p.mode == 'ship':
        v16 = 1.0 if not p.mini else 0.85
        falling = p.vy * flip < 0
        float_c = FLY_G
        if hold:
            v51 = 0.8 if (p.accel and p.vy * flip >= 0) else -1.0
        elif not p.accel:
            v51 = 0.8 if falling else 1.2
        else:
            v51 = 0.8 if falling else 1.2
        v52 = 0.5 if falling else 0.4
        if not p.accel and not hold:
            v52 = 0.4
        p.vy += -v51 * float_c * STEP * flip * v52 / v16
        if not p.accel:
            p.vy = _clamp_fly(p, v16, 0.8)
        return
    if p.mode == 'wave':
        k = 2.0 if p.mini else 1.0
        p.vy = flip * xvel(p.speed) * k * (1.0 if hold else -1.0)
        return
    raise ValueError(p.mode)


def _clamp_fly(p, v16, v42):
    lo, hi = (v42 * -8.0) / v16, 8.0 / v16
    if p.upside:
        lo, hi = -8.0 / v16, (v42 * 8.0) / v16
    return min(max(p.vy, lo), hi)


def _ring_jump(p, kind):
    _, _, y_start, _ = SPEED[p.speed]
    v22 = 0.8 if p.mini else 1.0
    if kind == 'black':
        v = (-14.0 if p.mode in ('ship', 'ufo', 'wave') else -15.0) * p.flip
        if p.mode == 'ufo':
            v *= 0.8
        p.vy = v
        p.on_ground = False
        return
    if p.mode == 'wave':
        if kind in ('blue', 'green'):
            p.upside = not p.upside
        return
    v23 = y_start
    if kind == 'blue':
        v23 *= 0.8
    else:
        m = ORB_MULT.get(kind, {})
        if kind == 'red' and p.mode == 'ship' and p.mini:
            v23 *= 1.4
        elif kind == 'red' and p.mode == 'ufo' and p.mini:
            v23 *= 1.36
        else:
            v23 *= m.get(p.mode, 1.0)
    if kind == 'green':
        p.upside = not p.upside
    p.vy = v23 * p.flip * v22
    if p.mode == 'ball':
        p.vy *= 0.7
    elif p.mode == 'spider':
        p.vy *= 0.7
    if kind == 'blue':
        p.upside = not p.upside
    p.on_ground = False
    p.accel = True


def _bump(p, kind):
    v16 = 0.8 if p.mini else 1.0
    if kind == 'blue':
        p.vy = 0.8 * 16.0 * p.flip * v16
        if p.mode in ('ball', 'spider', 'swing'):
            p.vy *= 0.6
        p.upside = not p.upside
    else:
        mod = PAD_MOD[kind]
        if kind == 'pink':
            mod = mod.get(p.mode, PAD_MOD_DEFAULT_PINK)
        elif kind == 'red':
            if p.mode == 'ship':
                mod = 0.95 if p.mini else 0.63
            elif p.mode == 'ufo':
                mod = 0.98 if p.mini else 0.6
        p.vy = mod * 16.0 * p.flip * v16
        if p.mode in ('ball', 'spider', 'swing'):
            p.vy *= 0.6
    p.on_ground = False
    p.accel = True


def _collide(course, p, prev_y, floor, ceil, margin):
    h = p.size / 2
    x0, x1 = p.x - h, p.x + h
    flying = p.mode in ('ship', 'ufo', 'wave', 'swing')
    surfaces = [(-1e12, floor - 1e6, 1e12, floor)]
    if ceil < 1e8:
        surfaces.append((-1e12, ceil, 1e12, ceil + 1e6))
    landed = False
    for sx0, sy0, sx1, sy1 in surfaces + course.solids:
        if not (x0 < sx1 and x1 > sx0):
            continue
        if not (p.y - h < sy1 and p.y + h > sy0):
            continue
        if p.mode == 'wave':
            return 'solid (wave)'
        if prev_y - h >= sy1 - 1e-6:                  # came from above: stand on it
            p.y = sy1 + h
            if p.vy < 0:
                p.vy = 0.0
            if not p.upside:
                landed = True
            continue
        if prev_y + h <= sy0 + 1e-6:                  # came from below: hit its underside
            p.y = sy0 - h
            if p.vy > 0:
                p.vy = 0.0
            if p.upside:
                landed = True
            elif p.mode in ('cube', 'robot'):
                return 'head bonk'                    # stricter than GD; the design must not rely on it
            continue
        return 'solid side'                           # stricter than GD (inner box rule); never by design
    p.on_ground = landed and not flying
    hm = h + margin
    for hx0, hy0, hx1, hy1 in course.hazards:
        if _overlap(p.x - hm, p.y - hm, p.x + hm, p.y + hm, hx0, hy0, hx1, hy1):
            return 'hazard'
    return None


def windows(course, presses, p0_factory, t_end, res_ms=2.0, limit_ms=150.0, **kw):
    """Per-press timing window: how far one press (both edges) can move earlier / later with the run still alive,
    found by bisection (assumes one contiguous window). Returns [(index, early_ms, late_ms)]; limit_ms means
    'not constrained within the limit'."""
    def ok(i, d):
        pr = list(presses)
        a, b = pr[i]
        pr[i] = (a + d / 1000.0, b + d / 1000.0)
        pr.sort()
        return simulate(course, Input(pr), p0_factory(), t_end=t_end, record=False, **kw)['alive']
    out = []
    for i in range(len(presses)):
        res = []
        for sign in (-1, 1):
            if ok(i, sign * limit_ms):
                res.append(limit_ms)
                continue
            lo, hi = 0.0, limit_ms
            while hi - lo > res_ms:
                m = (lo + hi) / 2
                if ok(i, sign * m):
                    lo = m
                else:
                    hi = m
            res.append(lo)
        out.append((i, res[0], res[1]))
    return out
