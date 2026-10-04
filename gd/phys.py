"""GD 2.1/2.2 player physics model (60 fps 'frame' constants converted to units/second),
used only to *verify* the generated level. Every uncertain constant is given as a set of
variants; a level part only counts as playable if it survives every variant."""
import math, itertools

SPEED = {0.5: 251.16, 1: 311.58, 2: 387.42, 3: 468.0, 4: 576.0}
F = 60.0
G0 = 0.958199 * F * F          # cube gravity, units/s^2
J0 = 11.180032 * F             # cube jump velocity
DT = 1.0 / 240.0               # GD 2.2 physics tick

# k = 1.0 -> velocities applied 1:1 ; k = 0.9 -> GD's 0.9 velocity multiplier.  We don't trust
# either 100%, so every check runs with both, plus extra slack on ship/ufo/ball.
def variants(mode):
    out = []
    for k in (0.9, 1.0):
        if mode == 'cube':
            out.append(dict(k=k, V=J0 * k, G=G0 * k, fall=15 * F * k))
        elif mode == 'ship':
            for a in (0.85, 1.0, 1.15):
                out.append(dict(k=k, a=a))
        elif mode == 'ball':
            for g, v0 in ((0.85, 0.0), (1.0, 0.25), (1.15, 0.35)):
                out.append(dict(k=k, G=0.6 * G0 * k * g, v0=J0 * k * v0, fall=15 * F * k))
        elif mode == 'ufo':
            for v, g in ((0.95, 0.9), (1.0, 1.0), (1.05, 1.15)):
                out.append(dict(k=k, V=7.0 * F * k * v, G=0.5 * G0 * k * g, fall=6.4 * F * k * 1.2))
        elif mode == 'wave':
            out.append(dict(k=k))
    return out


class Player:
    def __init__(self, x, y, mode, speed, mini=False, gdir=1, vy=0.0):
        self.x, self.y, self.vy = x, y, vy
        self.mode, self.speed, self.mini, self.gdir = mode, speed, mini, gdir
        self.ground = False
        self.dead = None
        self.prev_hold = False

    @property
    def half(self):
        if self.mode == 'wave':
            return 5.0 if self.mini else 7.0
        return 9.0 if self.mini else 15.0

    def vx(self):
        return SPEED[self.speed]


def step(p, hold, prm, world):
    """Advance one tick. world provides solids(x0,x1) -> list of (x0,y0,x1,y1) boxes,
    hazards(x0,x1) -> boxes, floor_y, ceil_y (hard bounds, None if absent)."""
    dt = DT
    vx = p.vx()
    press = hold and not p.prev_hold
    m, gd = p.mode, p.gdir
    if m == 'cube':
        if p.ground and hold:
            p.vy = prm['V'] * gd * (0.81 if p.mini else 1.0)  # mini: ~9.4/11.18 jump
            p.ground = False
        else:
            p.vy -= prm['G'] * gd * dt
            p.vy = max(-prm['fall'], min(prm['fall'], p.vy))
    elif m == 'ship':
        k, a = prm['k'], prm['a']
        rising = p.vy * gd > 0
        if hold:
            acc = (0.4 if rising else 0.5) * 1.0
        else:
            acc = -(0.4 * 1.2 if rising else 0.4 * 0.8)
        p.vy += G0 * k * a * acc * gd * dt
        up, dn = 8.0 * F * k, 6.4 * F * k
        if gd > 0:
            p.vy = max(-dn, min(up, p.vy))
        else:
            p.vy = max(-up, min(dn, p.vy))
    elif m == 'ball':
        if press and p.ground:
            p.gdir = gd = -gd
            p.vy = -prm['v0'] * gd  # small push away from the surface it leaves
            p.ground = False
        p.vy -= prm['G'] * gd * dt
        p.vy = max(-prm['fall'], min(prm['fall'], p.vy))
    elif m == 'ufo':
        if press:
            p.vy = prm['V'] * gd
        else:
            p.vy -= prm['G'] * gd * dt
            if gd > 0:
                p.vy = max(-prm['fall'], p.vy)
            else:
                p.vy = min(prm['fall'], p.vy)
    elif m == 'wave':
        s = 2.0 if p.mini else 1.0
        p.vy = (vx * s if hold else -vx * s) * gd
    p.prev_hold = hold

    px, py = p.x, p.y
    p.x += vx * dt
    p.y += p.vy * dt
    h = p.half
    p.ground = False
    # hard bounds (GD ground / mode ceiling)
    if world.floor_y is not None and p.y - h < world.floor_y:
        if p.mode == 'wave':
            p.y = world.floor_y + h
        else:
            p.y = world.floor_y + h;
            if p.vy < 0: p.vy = 0
            if gd > 0: p.ground = True
            elif p.mode == 'cube':
                pass
    if world.ceil_y is not None and p.y + h > world.ceil_y:
        p.y = world.ceil_y - h
        if p.vy > 0: p.vy = 0
        if gd < 0: p.ground = True
    # solids
    for (x0, y0, x1, y1) in world.solids(p.x - h, p.x + h):
        if p.x + h <= x0 or p.x - h >= x1 or p.y + h <= y0 or p.y - h >= y1:
            continue
        if p.mode == 'wave':
            p.dead = ('wave-solid', p.x, p.y); return
        tol = 2.0
        if py - h >= y1 - tol and (gd > 0 or p.mode in ('ship', 'ufo', 'ball')) and p.vy <= 0:
            p.y = y1 + h; p.vy = 0
            if gd > 0: p.ground = True
            continue
        if py + h <= y0 + tol and (gd < 0 or p.mode in ('ship', 'ufo', 'ball')) and p.vy >= 0:
            p.y = y0 - h; p.vy = 0
            if gd < 0: p.ground = True
            continue
        p.dead = ('solid', p.x, p.y, (x0, y0, x1, y1)); return
    # landed-on check for cube resting exactly on a surface (ground flag kept)
    if not p.ground and abs(p.vy) < 1e-9:
        for (x0, y0, x1, y1) in world.solids(p.x - h, p.x + h):
            if p.x + h > x0 and p.x - h < x1:
                if gd > 0 and abs((p.y - h) - y1) < 0.01: p.ground = True
                if gd < 0 and abs((p.y + h) - y0) < 0.01: p.ground = True
        if world.floor_y is not None and gd > 0 and abs(p.y - h - world.floor_y) < 0.01: p.ground = True
        if world.ceil_y is not None and gd < 0 and abs(p.y + h - world.ceil_y) < 0.01: p.ground = True
    for (x0, y0, x1, y1) in world.hazards(p.x - h, p.x + h):
        if p.x + h > x0 and p.x - h < x1 and p.y + h > y0 and p.y - h < y1:
            p.dead = ('hazard', round(p.x, 1), round(p.y, 1), (x0, y0, x1, y1)); return


def clearance(p, world):
    """distance from player box to nearest hazard / (non-supporting) solid, for margin stats"""
    h = p.half; best = 1e9
    for (x0, y0, x1, y1) in world.hazards(p.x - h - 60, p.x + h + 60):
        dx = max(x0 - (p.x + h), (p.x - h) - x1, 0)
        dy = max(y0 - (p.y + h), (p.y - h) - y1, 0)
        best = min(best, math.hypot(dx, dy))
    return best
