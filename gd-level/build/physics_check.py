"""Sanity check for cube sections. NOT a replacement for GD: GD's own physics decide; the bot + playtest are the
real test. Uses GD's published cube constants (jump 11.180032 u/frame, gravity 0.958199 u/frame^2 at 60 fps
frame units; jump height ~2.13 blocks matches the wiki) and steps at 240 Hz like 2.2.

Collision is deliberately conservative: the full 30x30 cube box kills on any side/ceiling contact, and spikes use
a hitbox larger than GD's. If a pattern survives this, it should survive in GD; margins are reported per click.
"""
from gdlevel import SPEED_UPS

VJ, G = 11.180032, 0.958199
STEP = 0.25  # frames (60 fps units) per 240 Hz step
SPIKE_HB = {'conservative': (7.5, 3.0, 24.0), 'nominal': (3.0, 9.0, 21.0)}  # half-width, y-lo, y-hi above base


def simulate(clicks, solids, spikes, portals, start_speed, t_end, model='conservative', start_x=0.0):
    """clicks: sorted times (s). solids: (x0,y0,x1,y1). spikes: (cx, base_y). portals: (x, speed).
    Returns (alive, t_death_or_end, x, path)."""
    hw, ylo, yhi = SPIKE_HB[model]
    x, yb, vy = start_x, 0.0, 0.0
    sp = start_speed
    on_ground = True
    t = 0.0
    dt = STEP / 60.0
    ci = 0
    portals = sorted(portals)
    pi = 0
    path = []
    while t < t_end:
        while pi < len(portals) and x >= portals[pi][0]:
            sp = portals[pi][1]
            pi += 1
        if ci < len(clicks) and t >= clicks[ci]:
            if on_ground:
                vy = VJ
            ci += 1
        vy -= G * STEP
        nx = x + SPEED_UPS[sp] * dt
        ny = yb + vy * STEP
        land = None
        if vy <= 0:
            for top in [0.0] + [y1 for (x0, y0, x1, y1) in solids if nx + 15 > x0 and nx - 15 < x1]:
                if yb >= top - 0.01 and ny <= top and (land is None or top > land):
                    land = top
        if land is not None:
            ny, vy, on_ground = land, 0.0, True
        else:
            on_ground = False
        x, yb = nx, ny
        # deaths: solid side/ceiling overlap
        for (x0, y0, x1, y1) in solids:
            if x + 15 > x0 + 0.01 and x - 15 < x1 - 0.01 and yb < y1 - 0.5 and yb + 30 > y0 + 0.01:
                return False, t, x, path
        for (cx, base) in spikes:
            if abs(x - cx) < 15 + hw and yb < base + yhi and yb + 30 > base + ylo:
                return False, t, x, path
        path.append((t, x, yb))
        t += dt
    return True, t, x, path


def click_windows(clicks, solids, spikes, portals, start_speed, t_end, model='conservative'):
    """For each click: earliest/latest offset (ms) keeping the run alive with all other clicks nominal."""
    out = []
    for i in range(len(clicks)):
        ok = []
        for off in range(-150, 151, 5):
            c = list(clicks)
            c[i] = clicks[i] + off / 1000.0
            if i > 0 and c[i] <= c[i - 1] or i + 1 < len(c) and c[i] >= c[i + 1]:
                continue
            if simulate(sorted(c), solids, spikes, portals, start_speed, t_end, model)[0]:
                ok.append(off)
        out.append((min(ok), max(ok)) if ok else None)
    return out
